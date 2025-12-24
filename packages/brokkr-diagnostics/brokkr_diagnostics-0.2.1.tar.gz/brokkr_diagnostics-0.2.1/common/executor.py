import asyncio
import subprocess
from typing import List, Optional, Tuple, Union
from termcolor import cprint

class Executor:
    """Executes commands and returns results"""
    async def execute(self, command: Union[List[str], str], timeout: int = 30) -> Optional[str]:
        """Execute a command and return the output"""
        try:
            result = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
            if result.returncode != 0:
                raise Exception(f"Command {command} failed with return code {result.returncode}: {stderr.decode().strip()}")
            return stdout.decode().strip() if result.returncode == 0 else None
        except Exception as e:
            cprint(f"Error executing {command}: {e}", "red")
            return None
    
    def find_binary(self, binary_name: str) -> Optional[str]:
        """Locate lspci binary"""
        try:
            result = subprocess.run(
                ["which", binary_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return None