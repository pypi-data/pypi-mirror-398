"""
NVIDIA SystemD Services Diagnostics.
Replicates systemd service checks from nvidia-bug-report.sh lines 995-1009.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from ..common.executor import Executor


@dataclass
class ServiceStatus:
    """Status of a single systemd service"""
    name: str
    exists: bool
    active: bool
    status: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class NvidiaServicesResult:
    """Results from NVIDIA service diagnostics"""
    timestamp: datetime
    services: Dict[str, ServiceStatus] = field(default_factory=dict)
    systemctl_available: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class NvidiaServicesDiagnostics:
    
    NVIDIA_SERVICES = [
        "nvidia-suspend.service",
        "nvidia-hibernate.service",
        "nvidia-resume.service",
        "nvidia-powerd.service",
        "nvidia-persistenced.service",
        "nvidia-fabricmanager.service",
    ]
    
    def __init__(self):
        self.executor = Executor()
        self.systemctl_path = self.executor.find_binary("systemctl")
    
    async def get_service_status(self, service_name: str) -> ServiceStatus:
        """
        Get status of a single systemd service
        
        Returns parsed service status including whether it's active, failed, or not found
        """
        service = ServiceStatus(
            name=service_name,
            exists=False,
            active=False
        )
        
        if not self.systemctl_path:
            service.error_message = "systemctl not available"
            return service
        
        # Run systemctl status
        cmd = f"sudo {self.systemctl_path} status {service_name}"
        output = await self.executor.execute(cmd, timeout=10)
        
        if output:
            service.full_output = output
            service.exists = True
            
            # Parse status from output
            for line in output.split("\n"):
                line_lower = line.lower()
                
                # Look for Active: line
                if "active:" in line_lower:
                    if "active (running)" in line_lower:
                        service.status = "active"
                        service.active = True
                    elif "active (exited)" in line_lower:
                        service.status = "active (exited)"
                        service.active = True
                    elif "inactive" in line_lower:
                        service.status = "inactive"
                    elif "failed" in line_lower:
                        service.status = "failed"
                        service.error_message = "Service failed"
                    elif "activating" in line_lower:
                        service.status = "activating"
                    break
        else:
            # Service not found or command failed
            service.exists = False
            service.status = "not-found"
            service.error_message = "Service not found or not loaded"
        
        return service
    
    async def run_all_checks(self) -> NvidiaServicesResult:
        """Check all NVIDIA services"""
        result = NvidiaServicesResult(timestamp=datetime.now())
        
        if not self.systemctl_path:
            result.systemctl_available = False
            result.errors.append("systemctl not available - cannot check services")
            return result
        
        # Check each service
        for service_name in self.NVIDIA_SERVICES:
            service_status = await self.get_service_status(service_name)
            result.services[service_name] = service_status
            
            # Add warnings for problematic services
            if service_status.status == "failed":
                result.warnings.append(f"{service_name} is in failed state")
            elif not service_status.exists and service_name in [
                "nvidia-persistenced.service",
                "nvidia-fabricmanager.service"
            ]:
                # These services are optional but good to note
                result.warnings.append(f"{service_name} is not installed (may be optional)")
        
        return result
    
    def format_report(self, result: NvidiaServicesResult) -> str:
        """Format results as human-readable report"""
        lines = ["=" * 80]
        lines.append("NVIDIA SystemD Services Status")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append("=" * 80)
        lines.append("")
        
        if not result.systemctl_available:
            lines.append("ERROR: systemctl not available")
            lines.append("")
            return "\n".join(lines)
        
        # Summary
        total = len(result.services)
        active = sum(1 for s in result.services.values() if s.active)
        inactive = sum(1 for s in result.services.values() if s.status == "inactive")
        failed = sum(1 for s in result.services.values() if s.status == "failed")
        not_found = sum(1 for s in result.services.values() if not s.exists)
        
        lines.append("Summary:")
        lines.append("-" * 80)
        lines.append(f"  Total Services:   {total}")
        lines.append(f"  Active:           {active}")
        lines.append(f"  Inactive:         {inactive}")
        lines.append(f"  Failed:           {failed}")
        lines.append(f"  Not Found:        {not_found}")
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
        
        # Service details
        lines.append("Service Details:")
        lines.append("-" * 80)
        
        for service_name, service in result.services.items():
            status_indicator = "OK" if service.active else ("FAIL" if service.status == "failed" else "SKIP")
            lines.append(f"  [{status_indicator:4s}] {service_name}")
            lines.append(f"          Status: {service.status or 'unknown'}")
            
            if service.error_message:
                lines.append(f"          Error:  {service.error_message}")
            
            # Show first few lines of output for failed services
            if service.status == "failed" and service.full_output:
                lines.append("          Output:")
                output_lines = service.full_output.split("\n")[:5]
                for out_line in output_lines:
                    if out_line.strip():
                        lines.append(f"            {out_line[:100]}")
            
            lines.append("")
        
        return "\n".join(lines)


async def run_nvidia_services_diagnostics():
    """Example usage"""
    diagnostics = NvidiaServicesDiagnostics()
    from termcolor import cprint
    result = await diagnostics.run_all_checks()
    
    cprint(diagnostics.format_report(result), "white")


if __name__ == "__main__":
    asyncio.run(run_nvidia_services_diagnostics())
