
from .drivers import run_driver_diagnostics
from .hardware import run_gpu_hardware_diagnostics, run_lspci_diagnostics
from .services import run_nvidia_services_diagnostics
from .system import run_kernel_logs_diagnostics, run_proc_diagnostics
from .ib import run_ib_diagnostics
import asyncio
from termcolor import cprint

def print_banner():
    """Print welcome banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                                                                            ║
    ║                          ⟨⟨═══════════════════⟩⟩                          ║
    ║                       ⟨⟨     ╱◖ ◗╲   ╱◖ ◗╲   ╱◖ ◗╲    ⟩⟩                  ║
    ║                     ⟨⟨      ╱ ◉ ◉ ╲ ╱ ◉ ◉ ╲ ╱ ◉ ◉ ╲    ⟩⟩                 ║
    ║                    ⟨⟨      ╱   ▼   ╲   ▼   ╲   ▼   ╲   ⟩⟩                ║
    ║                   ⟨⟨       │ ╲═══╱ │ ╲═══╱ │ ╲═══╱ │   ⟩⟩                ║
    ║                   ⟨⟨        ╲     ╱ ╲     ╱ ╲     ╱    ⟩⟩                 ║
    ║                   ⟨⟨         ╲___╱   ╲___╱   ╲___╱     ⟩⟩                 ║
    ║                   ⟨⟨          ╲│      │╲      │╱        ⟩⟩                 ║
    ║                   ⟨⟨           ╲╲    ╱│╲╲    ╱╱         ⟩⟩                 ║
    ║                    ⟨⟨           ╲╲__╱ │ ╲╲__╱╱         ⟩⟩                  ║
    ║                     ⟨⟨           ╲╲___│___╱╱          ⟩⟩                   ║
    ║                       ⟨⟨          ╲╲__│__╱╱          ⟩⟩                    ║
    ║                          ⟨⟨═════════╲│╱═════════⟩⟩                        ║
    ║                                                                            ║
    ║                  ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗  ██╗██████╗        ║
    ║                  ██╔══██╗██╔══██╗██╔═══██╗██║ ██╔╝██║ ██╔╝██╔══██╗       ║
    ║                  ██████╔╝██████╔╝██║   ██║█████╔╝ █████╔╝ ██████╔╝       ║
    ║                  ██╔══██╗██╔══██╗██║   ██║██╔═██╗ ██╔═██╗ ██╔══██╗       ║
    ║                  ██████╔╝██║  ██║╚██████╔╝██║  ██╗██║  ██╗██║  ██║       ║
    ║                  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝       ║
    ║                                                                            ║
    ║                       NVIDIA GPU DIAGNOSTICS TOOLKIT                      ║
    ║                         Hardware • Drivers • Kernel                       ║
    ║                                                                            ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """
    cprint(banner, "cyan", attrs=["bold"])


def print_help():
    """Print available commands"""
    cprint("\nAvailable Commands:", "cyan", attrs=["bold"])
    cprint("-" * 80, "cyan")
    cprint("  driver      - NVIDIA driver version & installation checks", "white")
    cprint("  gpu         - GPU hardware state & identification", "white")
    cprint("  lspci       - PCIe bus topology & link status", "white")
    cprint("  pcie        - Alias for 'lspci'", "white")
    cprint("  services    - SystemD service status (suspend/resume/persistence)", "white")
    cprint("  kernel      - Kernel messages & error detection", "white")
    cprint("  logs        - Alias for 'kernel'", "white")
    cprint("  system      - System information (/proc files, NUMA)", "white")
    cprint("  proc        - Alias for 'system'", "white")
    cprint("  ib          - InfiniBand diagnostics", "white")
    cprint("  all         - Run all diagnostics", "white")
    cprint("  help        - Show this help message", "white")
    cprint("  quit/exit   - Exit the program", "white")
    cprint("-" * 80, "cyan")


def run_all_diagnostics():
    """Run all diagnostic modules"""
    cprint("\n" + "=" * 80, "cyan")
    cprint("RUNNING ALL DIAGNOSTICS", "cyan", attrs=["bold"])
    cprint("=" * 80 + "\n", "cyan")
    
    diagnostics = [
        ("Driver Version & Installation", run_driver_diagnostics),
        ("PCIe Bus & Hardware", run_lspci_diagnostics),
        ("GPU Hardware State", run_gpu_hardware_diagnostics),
        ("System Information", run_proc_diagnostics),
        ("NVIDIA Services", run_nvidia_services_diagnostics),
        ("Kernel Messages", run_kernel_logs_diagnostics),
        ("InfiniBand", run_ib_diagnostics),
    ]
    
    for name, func in diagnostics:
        cprint(f"\n{'=' * 80}", "cyan")
        cprint(f"Running: {name}", "yellow", attrs=["bold"])
        cprint("=" * 80, "cyan")
        try:
            asyncio.run(func())
        except Exception as e:
            cprint(f"\nERROR running {name}: {e}", "red", attrs=["bold"])
        cprint("\n", "white")


if __name__ == "__main__":
    print_banner()
    print_help()
    
    while True:
        try:
            choice = input("\nbrokkr-diagnostics> ").strip().lower()
            
            if not choice:
                continue
            
            match choice:
                case "driver":
                    asyncio.run(run_driver_diagnostics())
                
                case "gpu":
                    asyncio.run(run_gpu_hardware_diagnostics())
                
                case "lspci" | "pcie":
                    asyncio.run(run_lspci_diagnostics())
                
                case "services":
                    asyncio.run(run_nvidia_services_diagnostics())
                
                case "kernel" | "logs":
                    asyncio.run(run_kernel_logs_diagnostics())
                
                case "system" | "proc":
                    asyncio.run(run_proc_diagnostics())
                
                case "ib":
                    asyncio.run(run_ib_diagnostics())
                
                case "all":
                    run_all_diagnostics()
                
                case "help" | "h" | "?":
                    print_help()
                
                case "quit" | "exit" | "q":
                    cprint("\nExiting Brokkr Host Manager Diagnostics...", "red")
                    break
                
                case _:
                    cprint(f"\nUnknown command: '{choice}'", "red")
                    cprint("Type 'help' to see available commands.", "yellow")
        
        except KeyboardInterrupt:
            cprint("\n\nExiting Brokkr Host Manager Diagnostics...", "red")
            break
        except EOFError:
            cprint("\n\nExiting Brokkr Host Manager Diagnostics...", "red")
            break
