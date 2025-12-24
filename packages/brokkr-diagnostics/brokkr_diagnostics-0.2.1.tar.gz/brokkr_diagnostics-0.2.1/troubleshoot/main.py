import asyncio
from ..common.executor import Executor
from typing import List
from termcolor import cprint

class TroubleShoot:
    def __init__(self):
        self.executor = Executor()
        self.services = []
        self.modules = []
        self.processes = []

    @classmethod
    async def create(cls) -> "TroubleShoot":
        instance = cls()
        await instance.find_nvidia_modules()
        await instance.find_services_using_gpu()
        await instance.find_processes_using_gpu()
        return instance

    async def find_nvidia_modules(self) -> None:
        command = "sudo lsmod | grep nvidia | awk '{print $1}'"
        result = await self.executor.execute(command)
        self.modules = result.split("\n")

    async def find_services_using_gpu(self) -> None:
        command = "sudo systemctl list-units --type=service | grep nvidia | awk '{print $1}'"
        result = await self.executor.execute(command)
        self.services = result.split("\n")

    async def find_processes_using_gpu(self) -> List[int]:
        command = "sudo lsof /dev/nvidia* 2>/dev/null | awk 'NR>1 {print $2}' | sort -u"
        result = await self.executor.execute(command)
        self.processes = result.split("\n") if result else []

    async def reset_all_gpus(self) -> bool:
        """Reset all GPUs using the proven sequence"""
        cprint("="*80, "cyan")
        cprint("GPU RESET SEQUENCE", "cyan", attrs=["bold"])
        cprint("="*80, "cyan")
        
        # Step 1: Stop services
        cprint("\n[1/5] Stopping NVIDIA services...", "yellow")
        for service in self.services:
            if service.strip():
                cprint(f"  Stopping {service}...", "yellow")
                await self.executor.execute(f"sudo systemctl stop {service}")
        
        # Step 2: Unload kernel modules (reverse dependency order)
        cprint("\n[2/5] Unloading kernel modules...", "yellow")
        module_unload_order = ["nvidia_uvm", "nvidia_drm", "nvidia_modeset", "nvidia"]
        for module in module_unload_order:
            if module in self.modules:
                cprint(f"  Unloading {module}...", "yellow")
                result = await self.executor.execute(f"sudo modprobe -r {module}")
                if result is None:
                    cprint(f"    Module {module} unloaded", "green")
        
        # Step 3: Reload nvidia module
        cprint("\n[3/5] Reloading nvidia module...", "yellow")
        await self.executor.execute("sudo modprobe nvidia")
        cprint("  nvidia module reloaded", "green")
        
        # Step 4: Reset GPUs
        cprint("\n[4/5] Resetting all GPUs...", "yellow")
        result = await self.executor.execute("sudo nvidia-smi --gpu-reset")
        if result and "successfully reset" in result:
            cprint("  GPUs reset successfully!", "green", attrs=["bold"])
            cprint(result, "green")
            success = True
        else:
            cprint("  ERROR: GPU reset failed!", "red", attrs=["bold"])
            if result:
                cprint(result, "red")
            success = False
        
        # Step 5: Restart services
        cprint("\n[5/5] Restarting NVIDIA services...", "yellow")
        for service in self.services:
            if service.strip():
                cprint(f"  Starting {service}...", "yellow")
                await self.executor.execute(f"sudo systemctl start {service}")
        
        cprint("\n" + "="*80, "cyan")
        if success:
            cprint("GPU RESET COMPLETE", "green", attrs=["bold"])
        else:
            cprint("GPU RESET FAILED", "red", attrs=["bold"])
        cprint("="*80, "cyan")
        
        return success



async def run_gpu_reset():
    """Run GPU reset for CLI"""
    troubleshoot = await TroubleShoot.create()
    await troubleshoot.reset_all_gpus()
   


if __name__ == "__main__":
    asyncio.run(run_gpu_reset())