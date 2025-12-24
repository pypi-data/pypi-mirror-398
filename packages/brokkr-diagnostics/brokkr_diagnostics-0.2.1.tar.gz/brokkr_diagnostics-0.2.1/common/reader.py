from pathlib import Path
from typing import Optional


class SysfsReader:
    """
    Read sysfs files.
    """


    def read_sysfs_int(self, path: Path) -> int:
        """Read a sysfs file as integer, return 0 if error"""
        try:
            if path.exists() and path.is_file():
                val = path.read_text().strip()
                return int(val)
        except Exception:
            pass
        return 0
    
    def read_sysfs_file(self, path: Path) -> Optional[str]:
        """Read a sysfs file, return None if not exists or error"""
        try:
            if path.exists() and path.is_file():
                return path.read_text().strip()
        except Exception:
            pass
        return None