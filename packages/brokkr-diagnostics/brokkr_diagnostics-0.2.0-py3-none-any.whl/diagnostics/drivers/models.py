from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModuleInfo:
    """Information about a kernel module"""
    name: str
    version: Optional[str] = None
    vermagic: Optional[str] = None
    loaded: bool = False
    parameters: Dict[str, str] = field(default_factory=dict)
    filename: Optional[str] = None


@dataclass
class DriverInstallation:
    """Driver installation information"""
    installer_log: Optional[str] = None
    uninstaller_log: Optional[str] = None
    dkms_logs: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class DriverVersionResult:
    """Results from driver version diagnostics"""
    timestamp: datetime
    nvidia_smi_version: Optional[str] = None
    driver_version: Optional[str] = None
    vbios_versions: List[str] = field(default_factory=list)
    proc_driver_version: Optional[str] = None
    proc_params: Dict[str, str] = field(default_factory=dict)
    proc_registry: Optional[str] = None
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    installation: Optional[DriverInstallation] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

