from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class IBPort:
    """InfiniBand port information"""
    port_num: int
    state: str
    phys_state: str
    rate: str
    link_layer: str
    lid: str
    sm_lid: str
    sm_sl: Optional[str] = None
    lid_mask_count: Optional[str] = None
    
    # Error counters
    symbol_error: int = 0
    link_error_recovery: int = 0
    link_downed: int = 0
    port_rcv_errors: int = 0
    port_rcv_remote_physical_errors: int = 0
    vl15_dropped: int = 0
    excessive_buffer_overrun_errors: int = 0
    port_xmit_discards: int = 0
    local_link_integrity_errors: int = 0
    port_rcv_switch_relay_errors: int = 0
    port_rcv_constraint_errors: int = 0
    port_xmit_constraint_errors: int = 0
    port_xmit_wait: int = 0
    
    # Traffic stats
    port_rcv_data: int = 0
    port_xmit_data: int = 0
    port_rcv_packets: int = 0
    port_xmit_packets: int = 0
    unicast_rcv_packets: int = 0
    unicast_xmit_packets: int = 0
    multicast_rcv_packets: int = 0
    multicast_xmit_packets: int = 0
    
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


    


@dataclass
class IBDevice:
    """InfiniBand device information"""
    name: str
    node_guid: str
    sys_image_guid: str
    fw_ver: str
    hw_rev: str
    board_id: str
    hca_type: str
    node_type: str
    node_desc: str
    
    # PCIe link status
    pcie_current_speed: Optional[str] = None
    pcie_current_width: Optional[str] = None
    pcie_max_speed: Optional[str] = None
    pcie_max_width: Optional[str] = None
    
    ports: List[IBPort] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class IBDiagnosticsResult:
    """Results from InfiniBand diagnostics"""
    timestamp: datetime
    devices: List[IBDevice] = field(default_factory=list)
    total_devices: int = 0
    active_ib_ports: int = 0
    down_ports: int = 0
    ethernet_ports: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)


