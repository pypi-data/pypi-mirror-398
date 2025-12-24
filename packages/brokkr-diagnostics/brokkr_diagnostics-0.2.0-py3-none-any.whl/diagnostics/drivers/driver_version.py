"""
NVIDIA Driver version and installation diagnostic module.
Replicates driver checks from nvidia-bug-report.sh lines 427-446, 985-993, 1329-1360.
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from ..common.executor import Executor
from .models import ModuleInfo, DriverInstallation, DriverVersionResult

class DriverVersionDiagnostics:
    """
    NVIDIA Driver version and installation diagnostics.
    
    Checks:
    - nvidia-smi version
    - Driver version from /proc and nvidia-smi
    - Module version magic (vermagic) for ABI compatibility
    - Installation/uninstallation logs
    - DKMS compilation logs
    - Loaded modules status
    - Module parameters
    """
    
    # NVIDIA kernel modules to check
    NVIDIA_MODULES = [
        "nvidia",
        "nvidia_drm", 
        "nvidia_modeset",
        "nvidia_uvm",
        "nvidia_peermem"
    ]
    
    PROC_DRIVER_PATH = Path("/proc/driver/nvidia")
    DKMS_PATH = Path("/var/lib/dkms/nvidia")
    
    def __init__(self):
        self.executor = Executor()
        self.nvidia_smi_path = self.executor.find_binary("nvidia-smi")
        self.modinfo_path = self.executor.find_binary("modinfo")
    
    async def get_nvidia_smi_version(self) -> Optional[str]:
        """
        Get nvidia-smi version (lines 429 in script)
        """
        if not self.nvidia_smi_path:
            return None
        
        result = await self.executor.execute(f"{self.nvidia_smi_path} --version")
        return result if result else None

    def vbios_version_match(self,vbios_versions: List[str]) -> bool:
        return len(set(vbios_versions)) == 1
    
    async def get_driver_and_vbios_versions(self) -> tuple[Optional[str], List[str]]:
        """
        Get driver version and VBIOS versions from nvidia-smi (lines 438-439)
        """
        if not self.nvidia_smi_path:
            return None, []
        
        cmd = (
            f"{self.nvidia_smi_path} --query-gpu=driver_version,vbios_version "
            f"--format=csv,noheader"
        )
        result = await self.executor.execute(cmd)
        
        if not result:
            return None, []
        
        driver_version = None
        vbios_versions = []
        
        for line in result.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                if not driver_version:
                    driver_version = parts[0]
                vbios_versions.append(parts[1])
        
        return driver_version, vbios_versions
    
    async def read_proc_driver_version(self) -> Optional[str]:
        """
        Read driver version from /proc/driver/nvidia/version (line 1554)
        """
        version_file = self.PROC_DRIVER_PATH / "version"
        if not version_file.exists():
            return None
        
        try:
            return version_file.read_text().strip()
        except Exception:
            return None
    
    async def read_proc_driver_params(self) -> Dict[str, str]:
        """
        Read driver parameters from /proc/driver/nvidia/params (line 1555)
        """
        params_file = self.PROC_DRIVER_PATH / "params"
        params = {}
        
        if not params_file.exists():
            return params
        
        try:
            content = params_file.read_text()
            for line in content.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    params[key.strip()] = value.strip()
        except Exception:
            pass
        
        return params

    
    async def read_proc_driver_registry(self) -> Optional[str]:
        """
        Read driver registry from /proc/driver/nvidia/registry (line 1556)
        """
        registry_file = self.PROC_DRIVER_PATH / "registry"
        if not registry_file.exists():
            return None
        
        try:
            return registry_file.read_text().strip()
        except Exception:
            return None
    
    async def get_module_info(self, module_name: str) -> ModuleInfo:
        """
        Get module information including vermagic (lines 1329-1348)
        """
        info = ModuleInfo(name=module_name)
        
        if not self.modinfo_path:
            return info
        
        # Get modinfo output
        result = await self.executor.execute(f"{self.modinfo_path} {module_name}")
        
        if result:
            for line in result.split("\n"):
                line = line.strip()
                if line.startswith("vermagic:"):
                    info.vermagic = line.split(":", 1)[1].strip()
                elif line.startswith("version:"):
                    info.version = line.split(":", 1)[1].strip()
                elif line.startswith("filename:"):
                    info.filename = line.split(":", 1)[1].strip()
        
        return info
    
    async def check_module_loaded(self, module_name: str) -> bool:
        """
        Check if module is loaded via /proc/modules (line 1548)
        """
        modules_file = Path("/proc/modules")
        if not modules_file.exists():
            return False
        
        try:
            content = modules_file.read_text()
            return any(line.startswith(module_name + " ") for line in content.split("\n"))
        except Exception:
            return False
    
    async def get_module_parameters(self, module_name: str) -> Dict[str, str]:
        """
        Get module parameters from /sys/module/*/parameters/ (lines 1350-1360)
        """
        params = {}
        params_path = Path(f"/sys/module/{module_name}/parameters")
        
        if not params_path.exists():
            return params
        
        try:
            for param_file in params_path.iterdir():
                if param_file.is_file():
                    try:
                        value = param_file.read_text().strip()
                        params[param_file.name] = value
                    except Exception:
                        params[param_file.name] = "<unreadable>"
        except Exception:
            pass
        
        return params
    
    async def read_installation_logs(self) -> DriverInstallation:
        """
        Read installation and uninstallation logs (lines 985-993)
        """
        installation = DriverInstallation()
        
        # nvidia-installer.log
        installer_log = Path("/var/log/nvidia-installer.log")
        if installer_log.exists():
            try:
                installation.installer_log = installer_log.read_text()
            except Exception as e:
                installation.errors.append(f"Could not read installer log: {e}")
        
        # nvidia-uninstall.log
        uninstall_log = Path("/var/log/nvidia-uninstall.log")
        if uninstall_log.exists():
            try:
                installation.uninstaller_log = uninstall_log.read_text()
            except Exception as e:
                installation.errors.append(f"Could not read uninstall log: {e}")
        
        # DKMS make.log files
        if self.DKMS_PATH.exists():
            try:
                for make_log in self.DKMS_PATH.rglob("make.log"):
                    try:
                        content = make_log.read_text()
                        installation.dkms_logs[str(make_log)] = content
                    except Exception as e:
                        installation.errors.append(f"Could not read DKMS log {make_log}: {e}")
            except Exception as e:
                installation.errors.append(f"Could not scan DKMS directory: {e}")
        
        return installation
    
    async def run_all_checks(self) -> DriverVersionResult:
        """
        Run all driver version and installation checks
        """
        result = DriverVersionResult(timestamp=datetime.now())
        
        # Get nvidia-smi version
        result.nvidia_smi_version = await self.get_nvidia_smi_version()
        if not result.nvidia_smi_version and self.nvidia_smi_path:
            result.warnings.append("nvidia-smi found but version check failed")
        elif not self.nvidia_smi_path:
            result.warnings.append("nvidia-smi not found")
        
        # Get driver and VBIOS versions
        driver_ver, vbios_vers = await self.get_driver_and_vbios_versions()
        result.driver_version = driver_ver
        result.vbios_versions = vbios_vers
        
        if not result.driver_version:
            result.errors.append("Could not determine driver version from nvidia-smi")
        
        # Get /proc driver info
        result.proc_driver_version = await self.read_proc_driver_version()
        result.proc_params = await self.read_proc_driver_params()
        result.proc_registry = await self.read_proc_driver_registry()
        
        if not result.proc_driver_version:
            result.errors.append("/proc/driver/nvidia/version not readable - driver may not be loaded")
        
        # Check each NVIDIA module
        for module_name in self.NVIDIA_MODULES:
            module_info = await self.get_module_info(module_name)
            module_info.loaded = await self.check_module_loaded(module_name)
            
            if module_info.loaded:
                module_info.parameters = await self.get_module_parameters(module_name)
            
            result.modules[module_name] = module_info
            
            # Warnings for important modules
            if module_name == "nvidia" and not module_info.loaded:
                result.errors.append("Main nvidia module is not loaded")
            elif not module_info.loaded:
                result.warnings.append(f"Module {module_name} is not loaded")
            
            if module_info.loaded and not module_info.vermagic:
                result.warnings.append(f"Could not get vermagic for loaded module {module_name}")
        
        # Read installation logs
        result.installation = await self.read_installation_logs()
        
        # Check version consistency
        if result.driver_version and result.proc_driver_version:
            if result.driver_version not in result.proc_driver_version:
                result.warnings.append(
                    f"Version mismatch: nvidia-smi reports {result.driver_version}, "
                    f"but /proc reports {result.proc_driver_version}"
                )
        
        return result
    
    def format_report(self, result: DriverVersionResult) -> str:
        """
        Format results as human-readable report
        """
        lines = ["=" * 80]
        lines.append("NVIDIA Driver Version & Installation Diagnostics")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append("=" * 80)
        lines.append("")
        
        # Errors
        if result.errors:
            lines.append("ERRORS:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        # Warnings
        if result.warnings:
            lines.append("WARNINGS:")
            for warning in result.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        # Driver versions
        lines.append("Driver Versions:")
        lines.append("-" * 80)
        if result.nvidia_smi_version:
            lines.append(f"  nvidia-smi: {result.nvidia_smi_version.split()[0] if result.nvidia_smi_version else 'N/A'}")
        if result.driver_version:
            lines.append(f"  Driver:     {result.driver_version}")
        if result.vbios_versions:
            lines.append(f"  VBIOS:      {', '.join(result.vbios_versions)}")
        if self.vbios_version_match(result.vbios_versions):
            lines.append(f"  VBIOS versions match")
        else:
            lines.append(f"  VBIOS versions do not match")
            
        lines.append("")
        
        # /proc driver info
        if result.proc_driver_version:
            lines.append("/proc/driver/nvidia/version:")
            lines.append("-" * 80)
            for line in result.proc_driver_version.split("\n")[:5]:
                lines.append(f"  {line}")
            lines.append("")
        
        # Module status
        lines.append("Kernel Modules:")
        lines.append("-" * 80)
        for module_name, module_info in result.modules.items():
            status = "✓ Loaded" if module_info.loaded else "✗ Not Loaded"
            lines.append(f"  {module_name}: {status}")
            if module_info.vermagic:
                lines.append(f"    vermagic: {module_info.vermagic}")
            if module_info.version:
                lines.append(f"    version:  {module_info.version}")
            if module_info.parameters:
                lines.append(f"    parameters: {len(module_info.parameters)} set")
        lines.append("")
        
        # Installation logs summary
        if result.installation:
            lines.append("Installation Logs:")
            lines.append("-" * 80)
            if result.installation.installer_log:
                log_lines = result.installation.installer_log.count("\n")
                lines.append(f"  ✓ nvidia-installer.log: {log_lines} lines")
            else:
                lines.append(f"  ✗ nvidia-installer.log: Not found")
            
            if result.installation.uninstaller_log:
                log_lines = result.installation.uninstaller_log.count("\n")
                lines.append(f"  ✓ nvidia-uninstall.log: {log_lines} lines")
            
            if result.installation.dkms_logs:
                lines.append(f"  ✓ DKMS logs: {len(result.installation.dkms_logs)} found")
            
            if result.installation.errors:
                lines.append("  Errors reading logs:")
                for error in result.installation.errors:
                    lines.append(f"    - {error}")
            lines.append("")
        
        return "\n".join(lines)


async def run_driver_diagnostics():
    """Example usage"""
    diagnostics = DriverVersionDiagnostics()
    result = await diagnostics.run_all_checks()
   
    print(diagnostics.format_report(result))
    if len(result.errors) > 0:
        print(f"Errors: {result.errors}")
        return False
    if len(result.installation.errors) > 0:
        print(f"Installation errors: {result.installation.errors}")
        return False
    return True
    


if __name__ == "__main__":
    asyncio.run(run_driver_diagnostics())