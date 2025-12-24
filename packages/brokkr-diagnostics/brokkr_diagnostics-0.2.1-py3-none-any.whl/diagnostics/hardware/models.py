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


@dataclass
class GPUDevice:
    """Detailed information about a single GPU"""
    index: int
    name: str
    pci_bus_id: str
    driver_version: Optional[str] = None
    vbios_version: Optional[str] = None
    serial: Optional[str] = None
    uuid: Optional[str] = None
    memory_total: Optional[str] = None
    
    # From /proc/driver/nvidia/gpus/<BUS_ID>/information
    proc_information: Optional[str] = None
    
    # From /proc/driver/nvidia/gpus/<BUS_ID>/power
    power_state: Optional[str] = None
    
    # From /sys/bus/pci/devices/<BUS_ID>/power/* (lines 925-960)
    sysfs_power_control: Optional[str] = None
    sysfs_runtime_status: Optional[str] = None
    sysfs_runtime_usage: Optional[str] = None
    parent_power_resources_d3hot: Optional[str] = None
    
    # Additional details
    compute_mode: Optional[str] = None
    gpu_uuid: Optional[str] = None
    
    # ECC Errors
    ecc_errors_corrected_volatile: Optional[str] = None
    ecc_errors_corrected_aggregate: Optional[str] = None
    ecc_errors_uncorrected_volatile: Optional[str] = None
    ecc_errors_uncorrected_aggregate: Optional[str] = None
    
    # Retired Pages
    retired_pages_single_bit_ecc: Optional[str] = None
    retired_pages_double_bit: Optional[str] = None
    retired_pages_pending: Optional[str] = None
    
    # Temperature and Throttling
    temperature_gpu: Optional[str] = None
    clocks_throttle_reasons_active: Optional[str] = None
    clocks_throttle_reasons_hw_slowdown: Optional[str] = None
    
    # PCIe Link Status
    pcie_link_gen_current: Optional[str] = None
    pcie_link_gen_max: Optional[str] = None
    pcie_link_width_current: Optional[str] = None
    pcie_link_width_max: Optional[str] = None
    
    errors: List[str] = field(default_factory=list)

    def check_ecc_errors(self) -> Optional[str]:
        if self.ecc_errors_uncorrected_aggregate and self.ecc_errors_uncorrected_aggregate != 'N/A':
            try:
                uncorrected_count = int(self.ecc_errors_uncorrected_aggregate)
                if uncorrected_count > 0:
                    return f"GPU {self.index}: {uncorrected_count} uncorrected ECC errors detected"
            except ValueError:
                return f"GPU {self.index}: {self.ecc_errors_uncorrected_aggregate} uncorrected ECC errors detected"
        return None
    
    def check_retired_pages(self) -> Optional[str]:
        if self.retired_pages_pending and self.retired_pages_pending not in ['N/A', '0', 'None']:
            return f"GPU {self.index}: Retired pages pending - {self.retired_pages_pending}"
        return None

    def check_clocks_throttle(self) -> Optional[str]:
        if self.clocks_throttle_reasons_active and self.clocks_throttle_reasons_active != 'N/A':
            if 'Active' in self.clocks_throttle_reasons_active or self.clocks_throttle_reasons_active != '0x0000000000000000':
                return f"GPU {self.index}: Clock throttling active - {self.clocks_throttle_reasons_active}"
        return None
    
    def check_pcie_link(self) -> Optional[str]:
        if self.pcie_link_gen_current and self.pcie_link_gen_max:
            if self.pcie_link_gen_current != self.pcie_link_gen_max and self.pcie_link_gen_current not in ['N/A', 'None']:
                return f"GPU {self.index}: PCIe link speed degraded - running at Gen{self.pcie_link_gen_current} (max: Gen{self.pcie_link_gen_max})"

    def check_pcie_link_width(self) -> Optional[str]:
        if self.pcie_link_width_current and self.pcie_link_width_max:
            if self.pcie_link_width_current != self.pcie_link_width_max and self.pcie_link_width_current not in ['N/A', 'None']:
                return f"GPU {self.index}: PCIe link width degraded - running at x{self.pcie_link_width_current} (max: x{self.pcie_link_width_max})"
        return None
        
    def check_all_errors(self) -> Optional[str]:
        return [
            self.check_ecc_errors(),
            self.check_retired_pages(),
            self.check_clocks_throttle(),
            self.check_pcie_link(),
            self.check_pcie_link_width()
        ]

@dataclass
class GPUHardwareResult:
    """Results from GPU hardware diagnostics"""
    timestamp: datetime
    gpus: List[GPUDevice] = field(default_factory=list)
    total_gpus: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)




