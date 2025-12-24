
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from ..common.executor import Executor

@dataclass
class PCIeDevice:
    """Represents a single PCIe device"""
    bus_id: str
    vendor_id: str
    device_id: str
    class_id: str
    revision_id: str
    subsystem_vendor: Optional[str] = None
    subsystem_device: Optional[str] = None
    config_space: Optional[bytes] = None
    link_speed: Optional[str] = None
    link_width: Optional[str] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class LspciCheckResult:
    """Results from lspci diagnostic checks"""
    timestamp: datetime
    lspci_available: bool
    tree_view: Optional[str] = None
    devices_list: Optional[str] = None
    verbose_dump: Optional[str] = None
    devices: List[PCIeDevice] = field(default_factory=list)
    nvidia_devices: List[PCIeDevice] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class LspciDiagnostics:
    """
    Runs comprehensive PCIe diagnostics matching nvidia-bug-report.sh checks.
    
    Executes:
    - lspci -nntv: Tree view with vendor:device IDs
    - lspci -nn: Device list with class and vendor IDs  
    - lspci -nnDvvvxxxx: Full verbose dump with config space
    - Fallback to sysfs if lspci unavailable
    - Special focus on NVIDIA devices (vendor 0x10de)
    """
    
    NVIDIA_VENDOR_ID = "10de"
    SYSFS_PCI_PATH = Path("/sys/bus/pci/devices")
    
    def __init__(self):
        self.executor = Executor()
        self.lspci_path =  self.executor.find_binary("lspci")
        self.hexdump_path = self.executor.find_binary("hexdump")





    
    async def _run_command(self, cmd: Union[List[str], str], timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Run command and return (success, stdout, stderr)
        """
        try:
            cmd_string = " ".join(cmd) if isinstance(cmd, list) else cmd
            result = await self.executor.execute(cmd_string, timeout)
            return (result is not None, result, None)
        except subprocess.TimeoutExpired:
            return (False, "", f"Command timed out after {timeout}s")
        except Exception as e:
            return (False, "", str(e))
    
    async def run_lspci_tree_view(self) -> Optional[str]:
        """
        Run: lspci -nntv
        Shows all devices in tree format with vendor:device IDs
        """
        if not self.lspci_path:
            return None
            
        success, stdout, stderr = await self._run_command([self.lspci_path, "-nntv"])
        if success:
            return stdout
        return None
    
    async def run_lspci_basic(self) -> Optional[str]:
        """
        Run: lspci -nn
        Lists all devices with class names and vendor:device IDs
        """
        if not self.lspci_path:
            return None
            
        success, stdout, stderr = await self._run_command([self.lspci_path, "-nn"])
        if success:
            return stdout
        return None
    
    async def run_lspci_verbose(self) -> Optional[str]:
        """
        Run: lspci -nnDvvvxxxx
        Most comprehensive - verbose info with full config space hex dump
        This is the CRITICAL check that reveals:
        - PCIe link speed/width capabilities and current values
        - Correctable/uncorrectable error registers
        - AER capability data
        - Device control/status registers
        - BAR addresses
        """
        if not self.lspci_path:
            return None
            
        success, stdout, stderr = await self._run_command(
            [self.lspci_path, "-nnDvvvxxxx"],
            timeout=60  # Can be slow on systems with many devices
        )
        if success:
            return stdout
        return None
    
    async def _read_sysfs_device_info(self, device_path: Path) -> Optional[PCIeDevice]:
        """Read PCIe device info from sysfs"""
        try:
            bus_id = device_path.name
            
            # Read vendor, device, class, revision
            vendor_id = (device_path / "vendor").read_text().strip().replace("0x", "")
            device_id = (device_path / "device").read_text().strip().replace("0x", "")
            class_id = (device_path / "class").read_text().strip().replace("0x", "")
            revision_id = (device_path / "revision").read_text().strip().replace("0x", "")
            
            # Read config space
            config_path = device_path / "config"
            config_space = None
            if config_path.exists():
                try:
                    config_space = config_path.read_bytes()
                except Exception:
                    pass
            
            # Try to read subsystem IDs if available
            subsystem_vendor = None
            subsystem_device = None
            try:
                if (device_path / "subsystem_vendor").exists():
                    subsystem_vendor = (device_path / "subsystem_vendor").read_text().strip().replace("0x", "")
                if (device_path / "subsystem_device").exists():
                    subsystem_device = (device_path / "subsystem_device").read_text().strip().replace("0x", "")
            except Exception:
                pass
            
            return PCIeDevice(
                bus_id=bus_id,
                vendor_id=vendor_id,
                device_id=device_id,
                class_id=class_id,
                revision_id=revision_id,
                subsystem_vendor=subsystem_vendor,
                subsystem_device=subsystem_device,
                config_space=config_space
            )
            
        except Exception as e:
            return None
    
    def _format_config_space_hex(self, config_space: bytes) -> str:
        """Format config space bytes as hex dump matching lspci format"""
        lines = []
        for i in range(0, len(config_space), 16):
            chunk = config_space[i:i+16]
            hex_bytes = " ".join(f"{b:02x}" for b in chunk)
            lines.append(f"{i:02x}: {hex_bytes}")
        return "\n".join(lines)
    
    async def read_sysfs_fallback(self) -> str:
        """
        Fallback: Read config space from sysfs (lines 1202-1237 in script)
        Used when lspci is not available
        """
        output_lines = ["PCI devices configuration space dump using sysfs", ""]
        
        if not self.SYSFS_PCI_PATH.exists():
            return "Error: /sys/bus/pci/devices not found"
        
        for device_path in sorted(self.SYSFS_PCI_PATH.iterdir()):
            if not device_path.is_dir():
                continue
                
            device = await self._read_sysfs_device_info(device_path)
            if not device:
                continue
            
            # Print device header
            output_lines.append("")
            output_lines.append(
                f"{device.bus_id} {device.class_id}: "
                f"Vendor {device.vendor_id} Device {device.device_id} "
                f"(rev {device.revision_id})"
            )
            
            # Print config space hex dump
            if device.config_space:
                output_lines.append(self._format_config_space_hex(device.config_space))
        
        return "\n".join(output_lines)
    
    def parse_lspci_verbose_for_errors(self, verbose_output: str) -> List[str]:
        """
        Parse lspci verbose output for PCIe errors
        Looks for:
        - Correctable/Uncorrectable error status
        - Link degradation
        - AER errors
        """
        errors = []
        
        if not verbose_output:
            return errors
        
        lines = verbose_output.split("\n")
        current_device = None
        
        for line in lines:
            # Track current device
            if line and not line.startswith("\t"):
                current_device = line.split()[0] if line.split() else None
            
            line_lower = line.lower()
            
            # Check for error indicators
            if "correctable" in line_lower and "error" in line_lower:
                if "+" in line or "status" in line_lower:
                    errors.append(f"{current_device}: Correctable error detected - {line.strip()}")
            
            if "uncorrectable" in line_lower and "error" in line_lower:
                if "+" in line or "status" in line_lower:
                    errors.append(f"{current_device}: Uncorrectable error detected - {line.strip()}")
            
            if "lnksta:" in line_lower:
                # Parse link status for degradation
                if "speed" in line_lower and "width" in line_lower:
                    errors.append(f"{current_device}: Link status - {line.strip()}")
            
            if "aer" in line_lower and ("error" in line_lower or "fatal" in line_lower):
                errors.append(f"{current_device}: AER event - {line.strip()}")
        
        return errors
    
    async def get_nvidia_devices_from_sysfs(self) -> List[PCIeDevice]:
        """Get all NVIDIA devices from sysfs"""
        nvidia_devices = []
        
        if not self.SYSFS_PCI_PATH.exists():
            return nvidia_devices
        
        for device_path in self.SYSFS_PCI_PATH.iterdir():
            if not device_path.is_dir():
                continue
            
            try:
                vendor_file = device_path / "vendor"
                if vendor_file.exists():
                    vendor_id = vendor_file.read_text().strip().replace("0x", "")
                    if vendor_id.lower() == self.NVIDIA_VENDOR_ID:
                        device = await self._read_sysfs_device_info(device_path)
                        if device:
                            nvidia_devices.append(device)
            except Exception:
                continue
        
        return nvidia_devices
    
    def check_pcie_link_status(self, device: PCIeDevice) -> Dict[str, str]:
        """
        Check PCIe link status from sysfs for a device
        Returns current and max link speed/width
        """
        status = {}
        device_path = self.SYSFS_PCI_PATH / device.bus_id
        
        try:
            # Current link speed and width
            current_speed_path = device_path / "current_link_speed"
            current_width_path = device_path / "current_link_width"
            
            if current_speed_path.exists():
                status["current_speed"] = current_speed_path.read_text().strip()
            
            if current_width_path.exists():
                status["current_width"] = current_width_path.read_text().strip()
            
            # Max link speed and width
            max_speed_path = device_path / "max_link_speed"
            max_width_path = device_path / "max_link_width"
            
            if max_speed_path.exists():
                status["max_speed"] = max_speed_path.read_text().strip()
            
            if max_width_path.exists():
                status["max_width"] = max_width_path.read_text().strip()
                
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    async def run_all_checks(self) -> LspciCheckResult:
        """
        Run all lspci checks matching nvidia-bug-report.sh
        Returns comprehensive result object
        """
        result = LspciCheckResult(
            timestamp=datetime.now(),
            lspci_available=self.lspci_path is not None
        )
        
        if self.lspci_path:
            # Run all lspci variants
            result.tree_view = await self.run_lspci_tree_view()
            result.devices_list = await self.run_lspci_basic()
            result.verbose_dump = await self.run_lspci_verbose()
            
            if not result.tree_view:
                result.warnings.append("lspci -nntv failed or returned no output")
            if not result.devices_list:
                result.warnings.append("lspci -nn failed or returned no output")
            if not result.verbose_dump:
                result.warnings.append("lspci -nnDvvvxxxx failed or returned no output")
            
            # Parse for errors
            if result.verbose_dump:
                pcie_errors = self.parse_lspci_verbose_for_errors(result.verbose_dump)
                result.errors.extend(pcie_errors)
        else:
            # Fallback to sysfs
            result.warnings.append("lspci not available, using sysfs fallback")
            result.verbose_dump = await self.read_sysfs_fallback()
        
        # Get NVIDIA devices specifically
        result.nvidia_devices = await self.get_nvidia_devices_from_sysfs()
        
        if not result.nvidia_devices:
            result.warnings.append("No NVIDIA devices found")
        
        # Check link status for each NVIDIA device
        for device in result.nvidia_devices:
            link_status = self.check_pcie_link_status(device)
            device.link_speed = link_status.get("current_speed")
            device.link_width = link_status.get("current_width")
            
            # Check for link degradation
            if "current_speed" in link_status and "max_speed" in link_status:
                if link_status["current_speed"] != link_status["max_speed"]:
                    result.warnings.append(
                        f"{device.bus_id}: PCIe link speed degraded - "
                        f"Running at {link_status['current_speed']}, "
                        f"capable of {link_status['max_speed']}"
                    )
            
            if "current_width" in link_status and "max_width" in link_status:
                if link_status["current_width"] != link_status["max_width"]:
                    result.warnings.append(
                        f"{device.bus_id}: PCIe link width degraded - "
                        f"Running at x{link_status['current_width']}, "
                        f"capable of x{link_status['max_width']}"
                    )
        
        return result
    
    def format_report(self, result: LspciCheckResult) -> str:
        """
        Format results as a human-readable report matching nvidia-bug-report.sh style
        """
        lines = ["=" * 80]
        lines.append("PCIe Diagnostics Report")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append(f"lspci available: {result.lspci_available}")
        lines.append("=" * 80)
        lines.append("")
        
        # Warnings
        if result.warnings:
            lines.append("WARNINGS:")
            for warning in result.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        # Errors
        if result.errors:
            lines.append("ERRORS DETECTED:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        # NVIDIA devices summary
        if result.nvidia_devices:
            lines.append(f"NVIDIA Devices Found: {len(result.nvidia_devices)}")
            lines.append("-" * 80)
            for device in result.nvidia_devices:
                lines.append(f"  Bus ID: {device.bus_id}")
                lines.append(f"  Vendor: 0x{device.vendor_id}")
                lines.append(f"  Device: 0x{device.device_id}")
                lines.append(f"  Class: 0x{device.class_id}")
                if device.link_speed:
                    lines.append(f"  Link Speed: {device.link_speed}")
                if device.link_width:
                    lines.append(f"  Link Width: x{device.link_width}")
                if device.errors:
                    lines.append(f"  Errors: {', '.join(device.errors)}")
                lines.append("")
        
        # Tree view
        if result.tree_view:
            lines.append("=" * 80)
            lines.append("lspci -nntv (Tree View)")
            lines.append("=" * 80)
            lines.append(result.tree_view)
            lines.append("")
        
        # Devices list
        if result.devices_list:
            lines.append("=" * 80)
            lines.append("lspci -nn (Devices List)")
            lines.append("=" * 80)
            lines.append(result.devices_list)
            lines.append("")
        
        # Note about verbose dump (too long to include in summary)
        if result.verbose_dump:
            lines.append("=" * 80)
            lines.append("Verbose dump available (lspci -nnDvvvxxxx or sysfs)")
            lines.append(f"Length: {len(result.verbose_dump)} characters")
            lines.append("=" * 80)
        
        return "\n".join(lines)


async def run_lspci_diagnostics():
    """Example usage"""
    from termcolor import cprint
    diagnostics = LspciDiagnostics()
    result = await diagnostics.run_all_checks()
    report = diagnostics.format_report(result)
    print(report)
    if len(result.errors) > 0:
        cprint(f"\nERROR: {len(result.errors)} error(s) detected in PCIe diagnostics", "red", attrs=["bold"])
     

    
  


if __name__ == "__main__":
    asyncio.run(run_lspci_diagnostics())