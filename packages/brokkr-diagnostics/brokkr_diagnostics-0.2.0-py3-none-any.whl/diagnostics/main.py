
from .drivers import run_driver_diagnostics
from .hardware import run_gpu_hardware_diagnostics, run_lspci_diagnostics
from .services import run_nvidia_services_diagnostics
from .system import run_kernel_logs_diagnostics, run_proc_diagnostics
from .ib import run_ib_diagnostics
import asyncio

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
    print(banner)


def print_help():
    """Print available commands"""
    print("\nAvailable Commands:")
    print("-" * 80)
    print("  driver      - NVIDIA driver version & installation checks")
    print("  gpu         - GPU hardware state & identification")
    print("  lspci       - PCIe bus topology & link status")
    print("  pcie        - Alias for 'lspci'")
    print("  services    - SystemD service status (suspend/resume/persistence)")
    print("  kernel      - Kernel messages & error detection")
    print("  logs        - Alias for 'kernel'")
    print("  system      - System information (/proc files, NUMA)")
    print("  proc        - Alias for 'system'")
    print("  ib          - InfiniBand diagnostics")
    print("  all         - Run all diagnostics")
    print("  help        - Show this help message")
    print("  quit/exit   - Exit the program")
    print("-" * 80)


def run_all_diagnostics():
    """Run all diagnostic modules"""
    print("\n" + "=" * 80)
    print("RUNNING ALL DIAGNOSTICS")
    print("=" * 80 + "\n")
    
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
        print(f"\n{'=' * 80}")
        print(f"Running: {name}")
        print("=" * 80)
        try:
            asyncio.run(func())
        except Exception as e:
            print(f"\nERROR running {name}: {e}")
        print("\n")


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
                    print("\nExiting Brokkr Host Manager Diagnostics...")
                    break
                
                case _:
                    print(f"\nUnknown command: '{choice}'")
                    print("Type 'help' to see available commands.")
        
        except KeyboardInterrupt:
            print("\n\nExiting Brokkr Host Manager Diagnostics...")
            break
        except EOFError:
            print("\n\nExiting Brokkr Host Manager Diagnostics...")
            break
