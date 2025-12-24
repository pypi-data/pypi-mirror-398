"""
System Information & Configuration diagnostics.
Replicates /proc file checks and NUMA configuration from nvidia-bug-report.sh lines 1544-1556, 1245-1289.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from ..common.executor import Executor


@dataclass
class ProcFileData:
    """Data from a single /proc file"""
    path: str
    exists: bool
    readable: bool
    content: Optional[str] = None
    error: Optional[str] = None


@dataclass
class NUMAInfo:
    """NUMA configuration information"""
    numactl_hardware: Optional[str] = None
    numa_balancing: Optional[str] = None
    has_cpu: Optional[str] = None
    has_memory: Optional[str] = None
    has_normal_memory: Optional[str] = None
    online: Optional[str] = None
    possible: Optional[str] = None
    gpu_numa_mappings: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class SystemInfoResult:
    """Results from system information diagnostics"""
    timestamp: datetime
    proc_files: Dict[str, ProcFileData] = field(default_factory=dict)
    numa_info: Optional[NUMAInfo] = None
    thp_enabled: Optional[str] = None
    compaction_proactiveness: Optional[str] = None
    nvidia_driver_version: Optional[str] = None
    kernel_version: Optional[str] = None
    cpu_count: Optional[int] = None
    total_memory: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ProcDiagnostics:
    """
    System Information & Configuration diagnostics.
    
    Collects:
    - /proc files (cmdline, cpuinfo, meminfo, interrupts, modules, version, etc.)
    - NVIDIA driver parameters and registry settings
    - NUMA configuration
    - Transparent Huge Pages settings
    - GPU NUMA node mappings
    """
    
    # Core /proc files to collect
    PROC_FILES = [
        Path("/proc/cmdline"),
        Path("/proc/cpuinfo"),
        Path("/proc/meminfo"),
        Path("/proc/interrupts"),
        Path("/proc/modules"),
        Path("/proc/version"),
        Path("/proc/iomem"),
        Path("/proc/mtrr"),
        Path("/proc/driver/nvidia/version"),
        Path("/proc/driver/nvidia/params"),
        Path("/proc/driver/nvidia/registry"),
    ]
    
    # NUMA-related files
    NUMA_FILES = [
        Path("/sys/devices/system/node/has_cpu"),
        Path("/sys/devices/system/node/has_memory"),
        Path("/sys/devices/system/node/has_normal_memory"),
        Path("/sys/devices/system/node/online"),
        Path("/sys/devices/system/node/possible"),
    ]
    
    def __init__(self):
        self.executor = Executor()
        self.numactl_path = self.executor.find_binary("numactl")
        self.lspci_path = self.executor.find_binary("lspci")
    
    async def read_proc_file(self, file_path: Path) -> ProcFileData:
        """Read a /proc file and return its data"""
        data = ProcFileData(
            path=str(file_path),
            exists=file_path.exists(),
            readable=False
        )
        
        if not data.exists:
            data.error = "File does not exist"
            return data
        
        try:
            data.content = file_path.read_text()
            data.readable = True
        except PermissionError:
            data.content = await self.executor.execute(f"sudo cat {file_path}")
            data.readable = True

        except Exception as e:
            data.error = str(e)
        
        return data
    
    async def get_numa_hardware_info(self) -> Optional[str]:
        """Get NUMA hardware configuration using numactl -H"""
        if not self.numactl_path:
            return None
        
        result = await self.executor.execute(f"{self.numactl_path} -H")
        return result
    
    async def get_gpu_numa_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Get NUMA node and CPU list mappings for each GPU
        Lines 1275-1284 of nvidia-bug-report.sh
        """
        if not self.lspci_path:
            return {}
        
        # Get all NVIDIA GPU PCI addresses (vendor ID 10de, function .0)
        gpu_list_cmd = f"{self.lspci_path} -d '10de:*' -s '.0' | awk '{{print $1}}'"
        gpu_result = await self.executor.execute(gpu_list_cmd)
        
        if not gpu_result:
            return {}
        
        mappings = {}
        gpus = gpu_result.strip().split("\n")
        
        for gpu_addr in gpus:
            if not gpu_addr.strip():
                continue
            
            gpu_info = {}
            
            # Read local_cpulist
            cpulist_path = Path(f"/sys/bus/pci/devices/0000:{gpu_addr}/local_cpulist")
            if cpulist_path.exists():
                try:
                    gpu_info['local_cpulist'] = cpulist_path.read_text().strip()
                except Exception:
                    pass
            
            # Read numa_node
            numa_node_path = Path(f"/sys/bus/pci/devices/0000:{gpu_addr}/numa_node")
            if numa_node_path.exists():
                try:
                    gpu_info['numa_node'] = numa_node_path.read_text().strip()
                except Exception:
                    pass
            
            if gpu_info:
                mappings[gpu_addr] = gpu_info
        
        return mappings
    
    async def collect_numa_info(self) -> NUMAInfo:
        """Collect all NUMA-related information"""
        numa_info = NUMAInfo()
        
        # Get numactl hardware info
        numa_info.numactl_hardware = await self.get_numa_hardware_info()
        
        # Read NUMA balancing setting
        balancing_path = Path("/proc/sys/kernel/numa_balancing")
        if balancing_path.exists():
            try:
                numa_info.numa_balancing = balancing_path.read_text().strip()
            except Exception:
                pass
        
        # Read NUMA node information
        for numa_file in self.NUMA_FILES:
            if numa_file.exists():
                try:
                    content = numa_file.read_text().strip()
                    field_name = numa_file.name
                    setattr(numa_info, field_name, content)
                except Exception:
                    pass
        
        # Get GPU NUMA mappings
        numa_info.gpu_numa_mappings = await self.get_gpu_numa_mappings()
        
        return numa_info
    
    def extract_nvidia_driver_version(self, content: Optional[str]) -> Optional[str]:
        """Extract NVIDIA driver version from /proc/driver/nvidia/version"""
        if not content:
            return None
        
        # Look for pattern like "NVRM version: NVIDIA UNIX x86_64 Kernel Module  535.104.05"
        for line in content.split("\n"):
            if "NVRM version:" in line or "Kernel Module" in line:
                parts = line.split()
                if len(parts) > 0:
                    # Get the last token which is usually the version
                    return parts[-1]
        
        return None
    
    def extract_kernel_version(self, content: Optional[str]) -> Optional[str]:
        """Extract kernel version from /proc/version"""
        if not content:
            return None
        
        # Format: "Linux version 5.15.0-58-generic ..."
        parts = content.split()
        if len(parts) >= 3:
            return parts[2]
        
        return None
    
    def extract_cpu_count(self, content: Optional[str]) -> Optional[int]:
        """Count processors from /proc/cpuinfo"""
        if not content:
            return None
        
        count = 0
        for line in content.split("\n"):
            if line.startswith("processor"):
                count += 1
        
        return count if count > 0 else None
    
    def extract_total_memory(self, content: Optional[str]) -> Optional[str]:
        """Extract total memory from /proc/meminfo"""
        if not content:
            return None
        
        for line in content.split("\n"):
            if line.startswith("MemTotal:"):
                return line.split(":", 1)[1].strip()
        
        return None
    
    async def run_all_checks(self) -> SystemInfoResult:
        """Run all system information checks"""
        result = SystemInfoResult(timestamp=datetime.now())
        
        # Read all /proc files
        for proc_file in self.PROC_FILES:
            file_data = await self.read_proc_file(proc_file)
            result.proc_files[str(proc_file)] = file_data
            
            if not file_data.readable:
                result.warnings.append(f"Could not read {proc_file}: {file_data.error}")
        
        # Read THP (Transparent Huge Pages) settings
        thp_path = Path("/sys/kernel/mm/transparent_hugepage/enabled")
        if thp_path.exists():
            try:
                result.thp_enabled = thp_path.read_text().strip()
            except Exception as e:
                result.warnings.append(f"Could not read THP settings: {e}")
        
        # Read compaction proactiveness
        compaction_path = Path("/proc/sys/vm/compaction_proactiveness")
        if compaction_path.exists():
            try:
                result.compaction_proactiveness = compaction_path.read_text().strip()
            except Exception as e:
                result.warnings.append(f"Could not read compaction proactiveness: {e}")
        
        # Collect NUMA information
        result.numa_info = await self.collect_numa_info()
        
        # Extract key information
        nvidia_version_file = result.proc_files.get("/proc/driver/nvidia/version")
        if nvidia_version_file and nvidia_version_file.content:
            result.nvidia_driver_version = self.extract_nvidia_driver_version(
                nvidia_version_file.content
            )
        
        kernel_version_file = result.proc_files.get("/proc/version")
        if kernel_version_file and kernel_version_file.content:
            result.kernel_version = self.extract_kernel_version(
                kernel_version_file.content
            )
        
        cpuinfo_file = result.proc_files.get("/proc/cpuinfo")
        if cpuinfo_file and cpuinfo_file.content:
            result.cpu_count = self.extract_cpu_count(cpuinfo_file.content)
        
        meminfo_file = result.proc_files.get("/proc/meminfo")
        if meminfo_file and meminfo_file.content:
            result.total_memory = self.extract_total_memory(meminfo_file.content)
        
        # Check for critical missing files
        if not result.nvidia_driver_version:
            result.warnings.append("Could not determine NVIDIA driver version")
        
        return result
    
    def format_report(self, result: SystemInfoResult) -> str:
        """Format results as human-readable report"""
        lines = ["=" * 80]
        lines.append("System Information & Configuration")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append("Summary:")
        lines.append("-" * 80)
        if result.kernel_version:
            lines.append(f"  Kernel Version:        {result.kernel_version}")
        if result.nvidia_driver_version:
            lines.append(f"  NVIDIA Driver:         {result.nvidia_driver_version}")
        if result.cpu_count:
            lines.append(f"  CPU Count:             {result.cpu_count}")
        if result.total_memory:
            lines.append(f"  Total Memory:          {result.total_memory}")
        if result.thp_enabled:
            lines.append(f"  THP Enabled:           {result.thp_enabled}")
        if result.compaction_proactiveness:
            lines.append(f"  Compaction Proactive:  {result.compaction_proactiveness}")
        lines.append("")
        
        # Warnings
        if result.warnings:
            lines.append("WARNINGS:")
            for warning in result.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        # Errors
        if result.errors:
            lines.append("ERRORS:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        # /proc files status
        lines.append("/proc Files:")
        lines.append("-" * 80)
        readable_count = sum(1 for f in result.proc_files.values() if f.readable)
        lines.append(f"  Total files: {len(result.proc_files)}")
        lines.append(f"  Readable: {readable_count}")
        lines.append("")
        
        for path, file_data in sorted(result.proc_files.items()):
            status = "OK" if file_data.readable else f"FAIL ({file_data.error})"
            lines.append(f"  [{status:20s}] {path}")
        lines.append("")
        
        # NUMA Information
        if result.numa_info:
            lines.append("NUMA Configuration:")
            lines.append("-" * 80)
            
            if result.numa_info.numa_balancing:
                lines.append(f"  NUMA Balancing: {result.numa_info.numa_balancing}")
            
            if result.numa_info.online:
                lines.append(f"  Online Nodes:   {result.numa_info.online}")
            
            if result.numa_info.has_cpu:
                lines.append(f"  Nodes with CPU: {result.numa_info.has_cpu}")
            
            if result.numa_info.has_memory:
                lines.append(f"  Nodes with Mem: {result.numa_info.has_memory}")
            
            if result.numa_info.numactl_hardware:
                lines.append("")
                lines.append("  Hardware Configuration:")
                for line in result.numa_info.numactl_hardware.split("\n")[:10]:
                    lines.append(f"    {line}")
                if result.numa_info.numactl_hardware.count("\n") > 10:
                    lines.append("    ...")
            
            if result.numa_info.gpu_numa_mappings:
                lines.append("")
                lines.append("  GPU NUMA Mappings:")
                for gpu_addr, info in sorted(result.numa_info.gpu_numa_mappings.items()):
                    lines.append(f"    GPU {gpu_addr}:")
                    if 'numa_node' in info:
                        lines.append(f"      NUMA Node:    {info['numa_node']}")
                    if 'local_cpulist' in info:
                        lines.append(f"      Local CPUs:   {info['local_cpulist']}")
            
            lines.append("")
        
        # Key file contents (truncated)
        lines.append("Key File Contents:")
        lines.append("-" * 80)
        
        # Boot command line
        cmdline = result.proc_files.get("/proc/cmdline")
        if cmdline and cmdline.content:
            lines.append("  Boot Command Line:")
            lines.append(f"    {cmdline.content[:200]}")
            if len(cmdline.content) > 200:
                lines.append("    ...")
            lines.append("")
        
        # NVIDIA driver parameters
        params = result.proc_files.get("/proc/driver/nvidia/params")
        if params and params.content:
            lines.append("  NVIDIA Driver Parameters:")
            param_lines = params.content.split("\n")[:15]
            for line in param_lines:
                if line.strip():
                    lines.append(f"    {line}")
            if len(params.content.split("\n")) > 15:
                lines.append("    ...")
            lines.append("")
        
        # Interrupts (NVIDIA related only)
        interrupts = result.proc_files.get("/proc/interrupts")
        if interrupts and interrupts.content:
            lines.append("  NVIDIA Interrupts:")
            for line in interrupts.content.split("\n"):
                if "nvidia" in line.lower() or "NVIDIA" in line:
                    lines.append(f"    {line[:120]}")
            lines.append("")
        
        return "\n".join(lines)


async def run_proc_diagnostics():
    """Example usage"""
    diagnostics = ProcDiagnostics()
    from termcolor import cprint
    result = await diagnostics.run_all_checks()
    
    cprint(diagnostics.format_report(result), "white")


if __name__ == "__main__":
    asyncio.run(run_proc_diagnostics())