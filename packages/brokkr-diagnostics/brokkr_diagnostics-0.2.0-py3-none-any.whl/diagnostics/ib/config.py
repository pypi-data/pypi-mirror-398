from pathlib import Path

SYSFS_IB_PATH = Path("/sys/class/infiniband")

# Error counter fields to check
ERROR_COUNTERS = [
    'symbol_error', 'link_error_recovery', 'link_downed',
    'port_rcv_errors', 'port_rcv_remote_physical_errors',
    'vl15_dropped', 'excessive_buffer_overrun_errors',
    'port_xmit_discards', 'local_link_integrity_errors',
    'port_rcv_switch_relay_errors', 'port_rcv_constraint_errors',
    'port_xmit_constraint_errors'
]

# Traffic counter fields
TRAFFIC_COUNTERS = [
    'port_rcv_data', 'port_xmit_data',
    'port_rcv_packets', 'port_xmit_packets',
    'unicast_rcv_packets', 'unicast_xmit_packets',
    'multicast_rcv_packets', 'multicast_xmit_packets',
    'port_xmit_wait'
]