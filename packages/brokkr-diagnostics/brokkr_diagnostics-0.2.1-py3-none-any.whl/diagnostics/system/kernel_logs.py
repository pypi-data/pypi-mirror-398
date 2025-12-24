"""
Kernel Messages & Error Detection diagnostics.
Replicates kernel log checks from nvidia-bug-report.sh lines 1364-1433.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import re
import asyncio
from ..common.executor import Executor


@dataclass
class KernelError:
    """Represents a kernel error message"""
    timestamp: Optional[str]
    message: str
    source: str  # Which log file/source
    severity: str  # 'critical', 'error', 'warning', 'info'
    error_type: Optional[str] = None  # 'xid', 'fallen_off_bus', 'irq', 'dma', etc.


@dataclass
class KernelLogsResult:
    """Results from kernel log diagnostics"""
    timestamp: datetime
    dmesg_output: Optional[str] = None
    nvidia_messages: List[str] = field(default_factory=list)
    errors: List[KernelError] = field(default_factory=list)
    xid_errors: List[KernelError] = field(default_factory=list)
    critical_errors: List[KernelError] = field(default_factory=list)
    sources_checked: List[str] = field(default_factory=list)
    sources_found: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class KernelLogsDiagnostics:
    """
    Kernel Messages & Error Detection diagnostics.
    
    Scans:
    - /var/log/messages, /var/log/kern.log, /var/log/kernel.log, /var/log/dmesg
    - journalctl (current and 2 previous boots)
    - Full dmesg output
    
    Searches for NVIDIA patterns:
    - NVRM, nvidia-, nvrm-nvlog, nvidia-powerd
    
    Detects critical issues:
    - XID errors (GPU hardware errors)
    - "GPU has fallen off the bus"
    - IRQ assignment failures
    - DMA mapping errors
    - Driver initialization failures
    - Timeout errors
    """
    
    # Log files to check
    LOG_FILES = [
        Path("/var/log/messages"),
        Path("/var/log/kern.log"),
        Path("/var/log/kernel.log"),
        Path("/var/log/dmesg"),
    ]
    
    # NVIDIA-related grep patterns
    NVIDIA_PATTERNS = ["NVRM", "nvidia-", "nvrm-nvlog", "nvidia-powerd"]
    
    # Critical error patterns
    CRITICAL_PATTERNS = {
        'xid': re.compile(r'NVRM:.*Xid.*:\s*(\d+)', re.IGNORECASE),
        'fallen_off_bus': re.compile(r'fallen off.*bus', re.IGNORECASE),
        'gpu_lost': re.compile(r'GPU.*has been lost', re.IGNORECASE),
        'irq': re.compile(r'(IRQ|interrupt).*fail', re.IGNORECASE),
        'dma': re.compile(r'DMA.*error|mapping.*fail', re.IGNORECASE),
        'timeout': re.compile(r'timeout|timed out', re.IGNORECASE),
        'hung': re.compile(r'hung|hang', re.IGNORECASE),
        'failed': re.compile(r'failed to (initialize|allocate|map)', re.IGNORECASE),
    }
    
    def __init__(self):
        self.executor = Executor()
        self.journalctl_path = self.executor.find_binary("journalctl")
        self.dmesg_path = self.executor.find_binary("dmesg")
    
    async def read_log_file(self, log_path: Path) -> Optional[str]:
        """Read a log file if it exists and is readable"""
        if not log_path.exists():
            return None
        
        try:
            return log_path.read_text()
        except Exception:
            return None
    
    async def search_log_file(self, log_path: Path, patterns: List[str]) -> List[str]:
        """Search log file for NVIDIA-related patterns"""
        content = await self.read_log_file(log_path)
        if not content:
            return []
        
        matches = []
        for line in content.split("\n"):
            for pattern in patterns:
                if pattern.lower() in line.lower():
                    matches.append(line)
                    break
        
        return matches
    
    async def get_dmesg_output(self) -> Optional[str]:
        """Get full dmesg output (line 1425-1433)"""
        if not self.dmesg_path:
            return None
        
        result = await self.executor.execute(f"sudo {self.dmesg_path}")
        return result if result else None
    
    async def get_journalctl_nvidia_messages(self, boot_offset: int = 0) -> Optional[str]:
        """
        Get NVIDIA messages from journalctl for specific boot
        boot_offset: 0 = current, -1 = previous, -2 = 2 boots ago
        """
        if not self.journalctl_path:
            return None
        
        boot_arg = f"-{abs(boot_offset)}" if boot_offset != 0 else "-0"
        
        # Build grep pattern with | for alternation
        grep_pattern = "|".join(self.NVIDIA_PATTERNS)
        
        cmd = f"sudo {self.journalctl_path} -b {boot_arg} | grep -E '{grep_pattern}'"
        result = await self.executor.execute(cmd)
        
        return result if result else None
    
    def classify_error(self, message: str) -> tuple[str, Optional[str]]:
        """
        Classify error severity and type
        Returns: (severity, error_type)
        """
        message_lower = message.lower()
        
        # Check for critical patterns
        if 'fallen off' in message_lower or 'gpu.*lost' in message_lower:
            return ('critical', 'fallen_off_bus')
        
        # Check for XID errors
        xid_match = self.CRITICAL_PATTERNS['xid'].search(message)
        if xid_match:
            xid_code = xid_match.group(1)
            return ('critical', f'xid_{xid_code}')
        
        # Check other critical patterns
        for error_type, pattern in self.CRITICAL_PATTERNS.items():
            if error_type in ['xid', 'fallen_off_bus']:
                continue
            if pattern.search(message):
                return ('error', error_type)
        
        # Check severity keywords
        if 'error' in message_lower or 'fail' in message_lower:
            return ('error', None)
        elif 'warning' in message_lower or 'warn' in message_lower:
            return ('warning', None)
        else:
            return ('info', None)
    
    def parse_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line if present"""
        # Common formats:
        # [12345.678901] kernel message
        # Dec 16 19:30:00 hostname message
        # 2025-12-16T19:30:00.123456+00:00 message
        
        # Kernel timestamp [xxxxx.xxxxxx]
        kernel_ts = re.match(r'^\[(\s*\d+\.\d+)\]', line)
        if kernel_ts:
            return kernel_ts.group(1).strip()
        
        # Syslog timestamp
        syslog_ts = re.match(r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})', line)
        if syslog_ts:
            return syslog_ts.group(1)
        
        # ISO timestamp
        iso_ts = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
        if iso_ts:
            return iso_ts.group(1)
        
        return None
    
    async def analyze_messages(self, messages: List[str], source: str) -> List[KernelError]:
        """Analyze messages and create KernelError objects"""
        errors = []
        
        for message in messages:
            timestamp = self.parse_timestamp(message)
            severity, error_type = self.classify_error(message)
            
            error = KernelError(
                timestamp=timestamp,
                message=message.strip(),
                source=source,
                severity=severity,
                error_type=error_type
            )
            
            errors.append(error)
        
        return errors
    
    async def run_all_checks(self) -> KernelLogsResult:
        """Run all kernel log checks"""
        result = KernelLogsResult(timestamp=datetime.now())
        
        # Get dmesg output
        result.dmesg_output = await self.get_dmesg_output()
        if not result.dmesg_output:
            result.warnings.append("Could not retrieve dmesg output")
        
        # Check log files
        for log_file in self.LOG_FILES:
            result.sources_checked.append(str(log_file))
            
            matches = await self.search_log_file(log_file, self.NVIDIA_PATTERNS)
            if matches:
                result.sources_found.append(str(log_file))
                result.nvidia_messages.extend(matches)
                
                # Analyze errors from this source
                file_errors = await self.analyze_messages(matches, str(log_file))
                result.errors.extend(file_errors)
        
        # Check journalctl for current and previous boots
        if self.journalctl_path:
            for boot_offset in [0, -1, -2]:
                boot_label = f"journalctl boot {boot_offset}"
                result.sources_checked.append(boot_label)
                
                journal_messages = await self.get_journalctl_nvidia_messages(boot_offset)
                if journal_messages:
                    result.sources_found.append(boot_label)
                    messages = journal_messages.split("\n")
                    result.nvidia_messages.extend(messages)
                    
                    # Analyze errors from journalctl
                    journal_errors = await self.analyze_messages(messages, boot_label)
                    result.errors.extend(journal_errors)
        else:
            result.warnings.append("journalctl not available")
        
        # Separate out critical errors and XID errors
        for error in result.errors:
            if error.severity == 'critical':
                result.critical_errors.append(error)
            
            if error.error_type and error.error_type.startswith('xid_'):
                result.xid_errors.append(error)
        
        # Summary warnings
        if not result.sources_found:
            result.warnings.append("No NVIDIA messages found in any log source")
        
        if result.xid_errors:
            result.warnings.append(f"Found {len(result.xid_errors)} XID errors (GPU hardware errors)")
        
        if result.critical_errors:
            result.warnings.append(f"Found {len(result.critical_errors)} critical errors")
        
        return result
    
    def format_report(self, result: KernelLogsResult) -> str:
        """Format results as human-readable report"""
        lines = ["=" * 80]
        lines.append("Kernel Messages & Error Detection")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append("Summary:")
        lines.append("-" * 80)
        lines.append(f"  Sources checked: {len(result.sources_checked)}")
        lines.append(f"  Sources with NVIDIA messages: {len(result.sources_found)}")
        lines.append(f"  Total NVIDIA messages: {len(result.nvidia_messages)}")
        lines.append(f"  Total errors: {len(result.errors)}")
        lines.append(f"  Critical errors: {len(result.critical_errors)}")
        lines.append(f"  XID errors: {len(result.xid_errors)}")
        lines.append("")
        
        # Warnings
        if result.warnings:
            lines.append("WARNINGS:")
            for warning in result.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        # Critical errors
        if result.critical_errors:
            lines.append("CRITICAL ERRORS:")
            lines.append("-" * 80)
            for error in result.critical_errors[:10]:  # Show first 10
                lines.append(f"  [{error.timestamp or 'no timestamp'}] {error.source}")
                lines.append(f"    Type: {error.error_type or 'unknown'}")
                lines.append(f"    {error.message[:200]}")  # Truncate long messages
                lines.append("")
            if len(result.critical_errors) > 10:
                lines.append(f"  ... and {len(result.critical_errors) - 10} more")
            lines.append("")
        
        # XID errors
        if result.xid_errors:
            lines.append("XID ERRORS (GPU Hardware Errors):")
            lines.append("-" * 80)
            for error in result.xid_errors[:10]:
                lines.append(f"  [{error.timestamp or 'no timestamp'}] {error.source}")
                lines.append(f"    {error.message[:200]}")
                lines.append("")
            if len(result.xid_errors) > 10:
                lines.append(f"  ... and {len(result.xid_errors) - 10} more")
            lines.append("")
        
        # Sources found
        lines.append("Log Sources Found:")
        lines.append("-" * 80)
        if result.sources_found:
            for source in result.sources_found:
                lines.append(f"  - {source}")
        else:
            lines.append("  None")
        lines.append("")
        
        # dmesg summary
        if result.dmesg_output:
            lines.append("dmesg Output:")
            lines.append("-" * 80)
            lines.append(f"  Length: {len(result.dmesg_output)} characters")
            lines.append(f"  Lines: {result.dmesg_output.count(chr(10))}")
            lines.append("")
        
        return "\n".join(lines)


async def run_kernel_logs_diagnostics():
    """Example usage"""
    diagnostics = KernelLogsDiagnostics()
    from termcolor import cprint
    result = await diagnostics.run_all_checks()
    
    cprint(diagnostics.format_report(result), "white")
    
    # Show sample of recent NVIDIA messages
    if result.nvidia_messages:
        cprint("\nRecent NVIDIA Messages (last 10):", "cyan")
        cprint("-" * 80, "cyan")
        for msg in result.nvidia_messages[-10:]:
            cprint(f"  {msg[:150]}", "white")


if __name__ == "__main__":
    asyncio.run(run_kernel_logs_diagnostics())

