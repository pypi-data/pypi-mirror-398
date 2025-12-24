"""
GPU Hardware State & Identification diagnostics.
Replicates GPU hardware checks from nvidia-bug-report.sh lines 438-441, 957-959, 1559-1562.
"""
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from ..common.executor import Executor
from .models import GPUDevice, GPUHardwareResult





class GPUHardwareDiagnostics:
    """
    GPU Hardware State & Identification diagnostics.
    
    Collects:
    - GPU enumeration via nvidia-smi
    - Detailed GPU properties (name, VBIOS, memory, serial, UUID)
    - Per-GPU information from /proc/driver/nvidia/gpus/<BUS_ID>/information
    - Per-GPU power state from /proc/driver/nvidia/gpus/<BUS_ID>/power
    """
    
    PROC_DRIVER_GPUS_PATH = Path("/proc/driver/nvidia/gpus")
    
    def __init__(self):
        self.executor = Executor()
        self.nvidia_smi_path = self.executor.find_binary("nvidia-smi")


    def normalize_pci_bus_id(self, pci_bus_id: str) -> str:
        """
        Normalize PCI bus ID
        """
        if pci_bus_id.count(":") >= 2:
            domain, rest = pci_bus_id.split(":", 1)
            return f"{domain[-4:]}:{rest}".lower()
        return pci_bus_id.lower()
    
    async def enumerate_gpus_basic(self) -> List[GPUDevice]:
        """
        Enumerate GPUs with basic info and error stats from nvidia-smi (lines 438-441)
        Query: name, driver_version, memory, vbios, bus_id, serial, uuid, errors, throttling, pcie
        """
        if not self.nvidia_smi_path:
            return []
        
        cmd = (
            f"{self.nvidia_smi_path} "
            f"--query-gpu=index,name,driver_version,memory.total,vbios_version,pci.bus_id,serial,uuid,"
            f"ecc.errors.corrected.volatile.total,ecc.errors.corrected.aggregate.total,"
            f"ecc.errors.uncorrected.volatile.total,ecc.errors.uncorrected.aggregate.total,"
            f"retired_pages.single_bit_ecc.count,retired_pages.double_bit.count,retired_pages.pending,"
            f"temperature.gpu,clocks_throttle_reasons.active,clocks_throttle_reasons.hw_slowdown,"
            f"pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max "
            f"--format=csv,noheader"
        )
        result = await self.executor.execute(cmd)
        if not result:
            return []
        
        gpus = []
        for line in result.strip().split("\n"):
            if not line.strip():
                continue
            
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 8:
                try:
                    gpu = GPUDevice(
                        index=int(parts[0]),
                        name=parts[1],
                        driver_version=parts[2] if parts[2] else None,
                        memory_total=parts[3] if parts[3] else None,
                        vbios_version=parts[4] if parts[4] else None,
                        pci_bus_id=parts[5] if parts[5] else None,
                        serial=parts[6] if parts[6] else None,
                        uuid=parts[7] if len(parts) > 7 and parts[7] else None,
                        # ECC Errors
                        ecc_errors_corrected_volatile=parts[8] if len(parts) > 8 else None,
                        ecc_errors_corrected_aggregate=parts[9] if len(parts) > 9 else None,
                        ecc_errors_uncorrected_volatile=parts[10] if len(parts) > 10 else None,
                        ecc_errors_uncorrected_aggregate=parts[11] if len(parts) > 11 else None,
                        # Retired Pages
                        retired_pages_single_bit_ecc=parts[12] if len(parts) > 12 else None,
                        retired_pages_double_bit=parts[13] if len(parts) > 13 else None,
                        retired_pages_pending=parts[14] if len(parts) > 14 else None,
                        # Temperature and Throttling
                        temperature_gpu=parts[15] if len(parts) > 15 else None,
                        clocks_throttle_reasons_active=parts[16] if len(parts) > 16 else None,
                        clocks_throttle_reasons_hw_slowdown=parts[17] if len(parts) > 17 else None,
                        # PCIe Link Status
                        pcie_link_gen_current=parts[18] if len(parts) > 18 else None,
                        pcie_link_gen_max=parts[19] if len(parts) > 19 else None,
                        pcie_link_width_current=parts[20] if len(parts) > 20 else None,
                        pcie_link_width_max=parts[21] if len(parts) > 21 else None,
                    )
                    gpus.append(gpu)
                except (ValueError, IndexError) as e:
                    # Skip malformed lines
                    continue
        
        return gpus
    
    async def get_gpu_proc_information(self, pci_bus_id: str) -> Optional[str]:
        """
        Read /proc/driver/nvidia/gpus/<BUS_ID>/information (lines 1559-1562)
        
        This contains:
        - GPU model and ID
        - IRQ assignments
        - Firmware version
        - Video BIOS information
        - Bus type and location
        """
        if not pci_bus_id:
            return None
        
   
        normalized_bus_id = self.normalize_pci_bus_id(pci_bus_id)
        info_file = self.PROC_DRIVER_GPUS_PATH / normalized_bus_id / "information"
        
        if not info_file.exists():
            return None
        
        try:
            return info_file.read_text().strip()
        except Exception as e:
            return f"Error reading: {e}"
    
    async def get_gpu_power_state(self, pci_bus_id: str) -> Optional[str]:
        """
        Read /proc/driver/nvidia/gpus/<BUS_ID>/power (lines 957-959)
        
        Shows GPU power management state
        """
        if not pci_bus_id:
            return None
        
        normalized_bus_id = self.normalize_pci_bus_id(pci_bus_id)
        power_file = self.PROC_DRIVER_GPUS_PATH / normalized_bus_id / "power"
        
        if not power_file.exists():
            return None
        
        try:
            return power_file.read_text().strip()
        except Exception as e:
            return f"Error reading: {e}"
    
    async def get_sysfs_power_info(self, pci_bus_id: str) -> Dict[str, Optional[str]]:
        """
        Read sysfs power management settings for GPU (lines 932-938)
        
        Returns:
        - power/control: runtime PM control mode (auto/on)
        - power/runtime_status: current runtime PM state (active/suspended/etc)
        - power/runtime_usage: usage counter
        """
        if not pci_bus_id:
            return {}
        
        normalized_bus_id = self.normalize_pci_bus_id(pci_bus_id)
        device_path = Path(f"/sys/bus/pci/devices/{normalized_bus_id}")
        
        power_info = {}
        
        for attr in ['control', 'runtime_status', 'runtime_usage']:
            attr_path = device_path / 'power' / attr
            try:
                if attr_path.exists():
                    power_info[attr] = attr_path.read_text().strip()
                else:
                    power_info[attr] = None
            except Exception:
                power_info[attr] = None
        
        return power_info
    
    async def get_parent_power_resources(self, pci_bus_id: str) -> Optional[str]:
        """
        Get parent PCIe port power resources D3hot info (lines 939-953)
        
        Only checks for VGA/3D controllers (class 0x030000 or 0x030200)
        This determines if the parent port can control GPU power.
        """
        if not pci_bus_id:
            return None
        
        normalized_bus_id = self.normalize_pci_bus_id(pci_bus_id)
        device_path = Path(f"/sys/bus/pci/devices/{normalized_bus_id}")
        
        if not device_path.exists():
            return None
        
        # Check PCI class - only relevant for VGA/3D controllers
        class_file = device_path / 'class'
        if not class_file.exists():
            return None
        
        try:
            pci_class = class_file.read_text().strip()
            # 0x030000 = VGA controller, 0x030200 = 3D controller
            if pci_class not in ['0x030000', '0x030200']:
                return None
        except Exception:
            return None
        
        # Get parent port's power_resources_D3hot
        try:
            # Resolve symlink to actual device path
            real_path = device_path.resolve()
            # Parent port is one level up
            parent_d3hot = real_path.parent / 'firmware_node' / 'power_resources_D3hot'
            
            if parent_d3hot.exists():
                # List contents of the directory
                contents = list(parent_d3hot.iterdir())
                if contents:
                    return f"Found {len(contents)} power resources"
                else:
                    return "Directory exists but empty"
            else:
                return None
        except Exception as e:
            return f"Error: {e}"
    
    async def get_detailed_gpu_info(self, gpu_index: int) -> Dict[str, str]:
        """
        Get additional detailed info for a specific GPU using nvidia-smi -q
        """
        if not self.nvidia_smi_path:
            return {}
        
        cmd = f"{self.nvidia_smi_path} -i {gpu_index} -q"
        result = await self.executor.execute(cmd)
        
        if not result:
            return {}
        
        details = {}
        for line in result.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                details[key.strip()] = value.strip()
        
        return details
    
    async def list_proc_gpus(self) -> List[str]:
        """
        List all GPU directories in /proc/driver/nvidia/gpus/
        """
        if not self.PROC_DRIVER_GPUS_PATH.exists():
            return []
        
        try:
            return [d.name for d in self.PROC_DRIVER_GPUS_PATH.iterdir() if d.is_dir()]
        except Exception:
            return []



    
    async def run_all_checks(self) -> GPUHardwareResult:
        """
        Run all GPU hardware identification checks
        """
        result = GPUHardwareResult(timestamp=datetime.now())
        
        if not self.nvidia_smi_path:
            result.errors.append("nvidia-smi not found - cannot enumerate GPUs")
            return result
        
        # Enumerate GPUs
        result.gpus = await self.enumerate_gpus_basic()
        result.total_gpus = len(result.gpus)
        
        if result.total_gpus == 0:
            result.errors.append("No GPUs detected by nvidia-smi")
            return result
        
        # Get detailed information for each GPU
        for gpu in result.gpus:
            # Get /proc information
            if gpu.pci_bus_id:
                gpu.proc_information = await self.get_gpu_proc_information(gpu.pci_bus_id)
                gpu.power_state = await self.get_gpu_power_state(gpu.pci_bus_id)
                
                # Get sysfs power management info
                sysfs_power = await self.get_sysfs_power_info(gpu.pci_bus_id)
                gpu.sysfs_power_control = sysfs_power.get('control')
                gpu.sysfs_runtime_status = sysfs_power.get('runtime_status')
                gpu.sysfs_runtime_usage = sysfs_power.get('runtime_usage')
                
                # Get parent port power resources
                gpu.parent_power_resources_d3hot = await self.get_parent_power_resources(gpu.pci_bus_id)
                
                if not gpu.proc_information:
                    gpu.errors.append(
                        f"Could not read /proc/driver/nvidia/gpus/{self.normalize_pci_bus_id(gpu.pci_bus_id)}/information"
                    )
                
                if not gpu.power_state:
                    gpu.errors.append(
                        f"Could not read /proc/driver/nvidia/gpus/{self.normalize_pci_bus_id(gpu.pci_bus_id)}/power"
                    )
            
            ecc_error_message, retired_pages_message, clocks_throttle_message, pcie_link_message, pcie_link_width_message = gpu.check_all_errors()

            if ecc_error_message:
                result.errors.append(ecc_error_message)
            if retired_pages_message:
                result.warnings.append(retired_pages_message)
            if clocks_throttle_message:
                result.warnings.append(clocks_throttle_message)
            if pcie_link_message:
                result.warnings.append(pcie_link_message)
            if pcie_link_width_message:
                result.warnings.append(pcie_link_width_message)

   
        proc_gpus = await self.list_proc_gpus()
        smi_bus_ids_normalized = {
            self.normalize_pci_bus_id(gpu.pci_bus_id) 
            for gpu in result.gpus if gpu.pci_bus_id
        }
        
        for proc_gpu in proc_gpus:
            if proc_gpu.lower() not in smi_bus_ids_normalized:
                result.warnings.append(
                    f"GPU {proc_gpu} found in /proc but not reported by nvidia-smi"
                )
        
        return result
    
    def format_report(self, result: GPUHardwareResult) -> str:
        """
        Format results as human-readable report
        """
        lines = ["=" * 80]
        lines.append("GPU Hardware State & Identification")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append(f"Total GPUs: {result.total_gpus}")
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
        
        # GPU Details
        for gpu in result.gpus:
            lines.append(f"GPU {gpu.index}:")
            lines.append("-" * 80)
            lines.append(f"  Name:          {gpu.name}")
            lines.append(f"  PCI Bus ID:    {gpu.pci_bus_id}")
            
            if gpu.driver_version:
                lines.append(f"  Driver:        {gpu.driver_version}")
            
            if gpu.vbios_version:
                lines.append(f"  VBIOS:         {gpu.vbios_version}")
            
            if gpu.memory_total:
                lines.append(f"  Memory:        {gpu.memory_total}")
            
            if gpu.serial:
                lines.append(f"  Serial:        {gpu.serial}")
            
            if gpu.uuid:
                lines.append(f"  UUID:          {gpu.uuid}")
            
            # ECC Errors
            if any([gpu.ecc_errors_corrected_aggregate, gpu.ecc_errors_uncorrected_aggregate]):
                lines.append("")
                lines.append("  ECC Errors:")
                if gpu.ecc_errors_corrected_volatile:
                    lines.append(f"    Corrected (Volatile):     {gpu.ecc_errors_corrected_volatile}")
                if gpu.ecc_errors_corrected_aggregate:
                    lines.append(f"    Corrected (Aggregate):    {gpu.ecc_errors_corrected_aggregate}")
                if gpu.ecc_errors_uncorrected_volatile:
                    lines.append(f"    Uncorrected (Volatile):   {gpu.ecc_errors_uncorrected_volatile}")
                if gpu.ecc_errors_uncorrected_aggregate:
                    lines.append(f"    Uncorrected (Aggregate):  {gpu.ecc_errors_uncorrected_aggregate}")
            
            # Retired Pages
            if any([gpu.retired_pages_single_bit_ecc, gpu.retired_pages_double_bit, gpu.retired_pages_pending]):
                lines.append("")
                lines.append("  Retired Pages:")
                if gpu.retired_pages_single_bit_ecc:
                    lines.append(f"    Single Bit ECC:  {gpu.retired_pages_single_bit_ecc}")
                if gpu.retired_pages_double_bit:
                    lines.append(f"    Double Bit:      {gpu.retired_pages_double_bit}")
                if gpu.retired_pages_pending:
                    lines.append(f"    Pending:         {gpu.retired_pages_pending}")

            if any([gpu.temperature_gpu, gpu.clocks_throttle_reasons_active, gpu.clocks_throttle_reasons_hw_slowdown]):
                lines.append("")
                lines.append("  Temperature & Throttling:")
                if gpu.temperature_gpu:
                    lines.append(f"    Temperature:     {gpu.temperature_gpu}°C")
                if gpu.clocks_throttle_reasons_active:
                    lines.append(f"    Throttle Active: {gpu.clocks_throttle_reasons_active}")
                if gpu.clocks_throttle_reasons_hw_slowdown:
                    lines.append(f"    HW Slowdown:     {gpu.clocks_throttle_reasons_hw_slowdown}")
            
            # PCIe Link Status
            if any([gpu.pcie_link_gen_current, gpu.pcie_link_width_current]):
                lines.append("")
                lines.append("  PCIe Link Status:")
                if gpu.pcie_link_gen_current and gpu.pcie_link_gen_max:
                    lines.append(f"    Link Gen:   {gpu.pcie_link_gen_current} (max: {gpu.pcie_link_gen_max})")
                if gpu.pcie_link_width_current and gpu.pcie_link_width_max:
                    lines.append(f"    Link Width: x{gpu.pcie_link_width_current} (max: x{gpu.pcie_link_width_max})")
            
            # /proc information
            if gpu.proc_information:
                lines.append("")
                lines.append("  /proc/driver/nvidia/gpus/.../information:")
                for line in gpu.proc_information.split("\n"):
                    lines.append(f"    {line}")
            
            # Power state
            if gpu.power_state:
                lines.append("")
                lines.append("  Power State (/proc):")
                for line in gpu.power_state.split("\n"):
                    lines.append(f"    {line}")
            
            # Sysfs power management
            if any([gpu.sysfs_power_control, gpu.sysfs_runtime_status, gpu.sysfs_runtime_usage]):
                lines.append("")
                lines.append("  Runtime Power Management (/sys):")
                if gpu.sysfs_power_control:
                    lines.append(f"    Control:        {gpu.sysfs_power_control}")
                if gpu.sysfs_runtime_status:
                    lines.append(f"    Runtime Status: {gpu.sysfs_runtime_status}")
                if gpu.sysfs_runtime_usage:
                    lines.append(f"    Runtime Usage:  {gpu.sysfs_runtime_usage}")
                if gpu.parent_power_resources_d3hot:
                    lines.append(f"    Parent D3hot:   {gpu.parent_power_resources_d3hot}")
            
            # GPU-specific errors
            if gpu.errors:
                lines.append("")
                lines.append("  GPU Errors:")
                for error in gpu.errors:
                    lines.append(f"    - {error}")
            
            lines.append("")
        
        return "\n".join(lines)


async def run_gpu_hardware_diagnostics():
    """Example usage"""
    from termcolor import cprint
    diagnostics = GPUHardwareDiagnostics()
    result = await diagnostics.run_all_checks()
    cprint(diagnostics.format_report(result), "white")
    if len(result.errors) > 0:
        cprint(f"\nERROR: {len(result.errors)} error(s) detected in GPU hardware diagnostics", "red", attrs=["bold"])
    


if __name__ == "__main__":
    asyncio.run(run_gpu_hardware_diagnostics())

