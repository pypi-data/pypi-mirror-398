"""
InfiniBand Hardware Diagnostics
Reads /sys/class/infiniband/ to diagnose IB device health and connectivity
"""
from pathlib import Path
from typing import Optional
from datetime import datetime
from .models import IBDevice, IBPort, IBDiagnosticsResult
from .config import SYSFS_IB_PATH, ERROR_COUNTERS, TRAFFIC_COUNTERS
from ..common import SysfsReader


class InfinibandDiagnostics(SysfsReader):
    """
    Comprehensive InfiniBand diagnostics from sysfs
    Reads /sys/class/infiniband/ for device health, port status, and error counters
    """
    def __init__(self):
        super().__init__()
        self.SYSFS_IB_PATH = SYSFS_IB_PATH
        self.ERROR_COUNTERS = ERROR_COUNTERS
        self.TRAFFIC_COUNTERS = TRAFFIC_COUNTERS
        
    
    def _read_device_info(self, device_path: Path) -> Optional[IBDevice]:
        """Read device-level information"""
        device_name = device_path.name
        
        # Required fields
        node_guid = self.read_sysfs_file(device_path / 'node_guid')
        if not node_guid:
            return None
        
        device = IBDevice(
            name=device_name,
            node_guid=node_guid,
            sys_image_guid=self.read_sysfs_file(device_path / 'sys_image_guid') or '',
            fw_ver=self.read_sysfs_file(device_path / 'fw_ver') or '',
            hw_rev=self.read_sysfs_file(device_path / 'hw_rev') or '',
            board_id=self.read_sysfs_file(device_path / 'board_id') or '',
            hca_type=self.read_sysfs_file(device_path / 'hca_type') or '',
            node_type=self.read_sysfs_file(device_path / 'node_type') or '',
            node_desc=self.read_sysfs_file(device_path / 'node_desc') or ''
        )
        
        # PCIe link status (from device/ symlink)
        device_link = device_path / 'device'
        if device_link.exists():
            device.pcie_current_speed = self.read_sysfs_file(device_link / 'current_link_speed')
            device.pcie_current_width = self.read_sysfs_file(device_link / 'current_link_width')
            device.pcie_max_speed = self.read_sysfs_file(device_link / 'max_link_speed')
            device.pcie_max_width = self.read_sysfs_file(device_link / 'max_link_width')
            
            # Check for PCIe link degradation
            if device.pcie_current_speed and device.pcie_max_speed:
                if device.pcie_current_speed != device.pcie_max_speed:
                    device.warnings.append(
                        f"PCIe link speed degraded: {device.pcie_current_speed} (max: {device.pcie_max_speed})"
                    )
            
            if device.pcie_current_width and device.pcie_max_width:
                if device.pcie_current_width != device.pcie_max_width:
                    device.warnings.append(
                        f"PCIe link width degraded: x{device.pcie_current_width} (max: x{device.pcie_max_width})"
                    )
        
        return device
    
    def _read_port_info(self, port_path: Path, device_name: str) -> Optional[IBPort]:
        """Read port-level information"""
        port_num = int(port_path.name)
        
        # Required fields
        state = self.read_sysfs_file(port_path / 'state')
        phys_state = self.read_sysfs_file(port_path / 'phys_state')
        
        if not state or not phys_state:
            return None
        
        port = IBPort(
            port_num=port_num,
            state=state,
            phys_state=phys_state,
            rate=self.read_sysfs_file(port_path / 'rate') or '',
            link_layer=self.read_sysfs_file(port_path / 'link_layer') or '',
            lid=self.read_sysfs_file(port_path / 'lid') or '',
            sm_lid=self.read_sysfs_file(port_path / 'sm_lid') or '',
            sm_sl=self.read_sysfs_file(port_path / 'sm_sl'),
            lid_mask_count=self.read_sysfs_file(port_path / 'lid_mask_count')
        )
        
        # Read error counters
        counters_path = port_path / 'counters'
        if counters_path.exists():
            for counter_name in self.ERROR_COUNTERS:
                value = self.read_sysfs_int(counters_path / counter_name)
                setattr(port, counter_name, value)
            
            # Read traffic counters
            for counter_name in self.TRAFFIC_COUNTERS:
                value = self.read_sysfs_int(counters_path / counter_name)
                setattr(port, counter_name, value)
        
        # Analyze port status and flag issues
        self._analyze_port_status(port, device_name)
        
        return port
    
    def _analyze_port_status(self, port: IBPort, device_name: str):
        """Analyze port status and flag errors/warnings"""
        port_id = f"{device_name}/port{port.port_num}"
        
        # Check port state
        if "DOWN" in port.state.upper() or "Disabled" in port.phys_state:
            if port.link_layer == "InfiniBand":
                # InfiniBand port down is a warning (might be intentional)
                port.warnings.append(
                    f"{port_id}: InfiniBand port DOWN (state: {port.state}, phys: {port.phys_state})"
                )
            else:
                # Ethernet port down is just info (expected if not using IB mode)
                pass  # Don't spam warnings for unused Ethernet ports
        
        elif "ACTIVE" in port.state.upper():
        
            error_checks = [
                (port.symbol_error > 0, f"{port_id}: Symbol errors detected ({port.symbol_error}) - physical/cable issue"),
                (port.link_downed > 0, f"{port_id}: Link went down {port.link_downed} time(s)"),
                (port.port_rcv_errors > 0, f"{port_id}: Receive errors ({port.port_rcv_errors})"),
                (port.port_rcv_remote_physical_errors > 0, f"{port_id}: Remote physical errors ({port.port_rcv_remote_physical_errors})"),
            ]
            
            for condition, message in error_checks:
                if condition:
                    port.errors.append(message)
            
            # Warnings
            warning_checks = [
                (port.link_error_recovery > 0, f"{port_id}: Link error recovery events ({port.link_error_recovery}) - unstable link"),
                (port.vl15_dropped > 0, f"{port_id}: VL15 dropped ({port.vl15_dropped}) - Subnet Manager traffic issues"),
                (port.port_xmit_discards > 0, f"{port_id}: Transmit discards ({port.port_xmit_discards}) - congestion or buffer issues"),
                (port.excessive_buffer_overrun_errors > 0, f"{port_id}: Excessive buffer overruns ({port.excessive_buffer_overrun_errors})"),
                (port.local_link_integrity_errors > 0, f"{port_id}: Local link integrity errors ({port.local_link_integrity_errors})"),
            ]
            
            for condition, message in warning_checks:
                if condition:
                    port.warnings.append(message)
    
    def run_all_checks(self) -> IBDiagnosticsResult:
        """Run all InfiniBand diagnostics"""
        result = IBDiagnosticsResult(timestamp=datetime.now())
        
        if not self.SYSFS_IB_PATH.exists():
            result.errors.append(f"{self.SYSFS_IB_PATH} does not exist - no InfiniBand support")
            return result
        
        # Enumerate all IB devices
        device_paths = sorted([d for d in self.SYSFS_IB_PATH.iterdir() if d.is_dir()])
        
        if not device_paths:
            result.warnings.append("No InfiniBand devices found")
            return result
        
        result.total_devices = len(device_paths)
        
        for device_path in device_paths:
            device = self._read_device_info(device_path)
            if not device:
                result.warnings.append(f"Could not read device info for {device_path.name}")
                continue
            
            # Read ports
            ports_path = device_path / 'ports'
            if ports_path.exists():
                port_dirs = sorted([p for p in ports_path.iterdir() if p.is_dir()])
                
                for port_dir in port_dirs:
                    port = self._read_port_info(port_dir, device.name)
                    if port:
                        device.ports.append(port)
                        
                        # Count port types
                        if "ACTIVE" in port.state.upper():
                            if port.link_layer == "InfiniBand":
                                result.active_ib_ports += 1
                            else:
                                result.ethernet_ports += 1
                        elif "DOWN" in port.state.upper():
                            result.down_ports += 1
                        
                        # Collect port errors/warnings
                        device.errors.extend(port.errors)
                        device.warnings.extend(port.warnings)
            
            result.devices.append(device)
            result.errors.extend(device.errors)
            result.warnings.extend(device.warnings)
        
        # Summary info
        result.info.append(f"Total devices: {result.total_devices}")
        result.info.append(f"Active InfiniBand ports: {result.active_ib_ports}")
        result.info.append(f"Active Ethernet ports: {result.ethernet_ports}")
        result.info.append(f"Down ports: {result.down_ports}")
        
        return result
    
    def format_report(self, result: IBDiagnosticsResult) -> str:
        """Format results as human-readable report"""
        lines = ["=" * 80]
        lines.append("InfiniBand Hardware Diagnostics")
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        if result.info:
            lines.append("SUMMARY:")
            for info in result.info:
                lines.append(f"  {info}")
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
        
        # Device details
        for device in result.devices:
            lines.append("=" * 80)
            lines.append(f"DEVICE: {device.name}")
            lines.append("=" * 80)
            lines.append(f"  Node GUID:      {device.node_guid}")
            lines.append(f"  Firmware:       {device.fw_ver}")
            lines.append(f"  HCA Type:       {device.hca_type}")
            lines.append(f"  Board ID:       {device.board_id}")
            lines.append(f"  Node Type:      {device.node_type}")
            lines.append(f"  Node Desc:      {device.node_desc}")
            
            if device.pcie_current_speed:
                lines.append("")
                lines.append("  PCIe Link:")
                lines.append(f"    Current: {device.pcie_current_speed} x{device.pcie_current_width}")
                lines.append(f"    Max:     {device.pcie_max_speed} x{device.pcie_max_width}")
            
            # Ports
            for port in device.ports:
                lines.append("")
                lines.append(f"  Port {port.port_num}:")
                lines.append(f"    State:       {port.state}")
                lines.append(f"    Phys State:  {port.phys_state}")
                lines.append(f"    Rate:        {port.rate}")
                lines.append(f"    Link Layer:  {port.link_layer}")
                
                if port.link_layer == "InfiniBand":
                    lines.append(f"    LID:         {port.lid}")
                    lines.append(f"    SM LID:      {port.sm_lid}")
                
                # Show error counters if any non-zero
                has_errors = any([
                    port.symbol_error, port.link_error_recovery, port.link_downed,
                    port.port_rcv_errors, port.port_rcv_remote_physical_errors,
                    port.vl15_dropped, port.port_xmit_discards,
                    port.excessive_buffer_overrun_errors
                ])
                
                if has_errors:
                    lines.append("")
                    lines.append("    Error Counters:")
                    if port.symbol_error:
                        lines.append(f"      Symbol errors: {port.symbol_error}")
                    if port.link_error_recovery:
                        lines.append(f"      Link error recovery: {port.link_error_recovery}")
                    if port.link_downed:
                        lines.append(f"      Link downed: {port.link_downed}")
                    if port.port_rcv_errors:
                        lines.append(f"      RCV errors: {port.port_rcv_errors}")
                    if port.port_rcv_remote_physical_errors:
                        lines.append(f"      Remote physical errors: {port.port_rcv_remote_physical_errors}")
                    if port.vl15_dropped:
                        lines.append(f"      VL15 dropped: {port.vl15_dropped}")
                    if port.port_xmit_discards:
                        lines.append(f"      XMIT discards: {port.port_xmit_discards}")
                    if port.excessive_buffer_overrun_errors:
                        lines.append(f"      Buffer overruns: {port.excessive_buffer_overrun_errors}")
                
                # Show traffic stats if port is active
                if "ACTIVE" in port.state.upper():
                    lines.append("")
                    lines.append("    Traffic Stats:")
                    lines.append(f"      RCV data:     {port.port_rcv_data} bytes")
                    lines.append(f"      XMIT data:    {port.port_xmit_data} bytes")
                    lines.append(f"      RCV packets:  {port.port_rcv_packets}")
                    lines.append(f"      XMIT packets: {port.port_xmit_packets}")
            
            lines.append("")
        
        return "\n".join(lines)


async def run_ib_diagnostics():
    """Example usage"""
    from termcolor import cprint
    diagnostics = InfinibandDiagnostics()
    result = diagnostics.run_all_checks()
    cprint(diagnostics.format_report(result), "white")
    if len(result.errors) > 0:
        cprint(f"\nERROR: {len(result.errors)} error(s) detected in InfiniBand diagnostics", "red", attrs=["bold"])


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_ib_diagnostics())
