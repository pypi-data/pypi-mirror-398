#!/usr/bin/env python3
"""
Build script for creating self-contained collector binary
"""

import os
import subprocess
import sys


if os.path.basename(os.getcwd()) == "diagnostics":
    SCRIPT_PATH = "__main__.py"
    PATHS_ARG = os.path.dirname(os.getcwd())
else:
    SCRIPT_PATH = "diagnostics/__main__.py"
    PATHS_ARG = os.getcwd()

# Discovery tools to embed
binaries = [
    # Core system tools (for reading /proc, /sys)
    "lspci",
    "nvidia-smi",
    "nvidia-debugdump",
    "dmesg",
    "journalctl",
    "cat",
    "grep",
    # InfiniBand tools (optional)
    "ibstat",
    "ibstatus",
    "ibnetdiscover",
    "perfquery",
    # Basic utilities
    "which",
    "sudo",  # If needed
]

# Build PyInstaller arguments
args = ["uv", "run", "pyinstaller", "--onefile", "--name", "brokkr-diagnostics"]
                               
found = []

# Auto-discover and embed all available binaries
for binary in binaries:
    try:
        result = subprocess.run(["which", binary], capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.strip()
            args.extend(["--add-binary", f"{path}:."])
            found.append(binary)
        else:
            print(f"WARNING: {binary} not found")
    except Exception as e:
        print(f"ERROR finding {binary}: {e}")

# No additional arch-specific binaries needed for diagnostics

# Add required hidden imports for core libraries
hidden_imports = [
    # Core libraries
    "asyncio",
    "ctypes",
    "numpy",
    "numpy.core",
    "numpy.core._multiarray_umath",
    "datetime",
    "dataclasses",
    "pathlib",
    "termcolor",
    # Your diagnostics package
    "diagnostics",
    "diagnostics.common",
    "diagnostics.common.executor",
    "diagnostics.common.cuda_interface",
    "diagnostics.common.models",
    "diagnostics.common.reader",
    "diagnostics.drivers",
    "diagnostics.drivers.driver_version",
    "diagnostics.drivers.models",
    "diagnostics.hardware",
    "diagnostics.hardware.gpu_info",
    "diagnostics.hardware.lspci",
    "diagnostics.hardware.models",
    "diagnostics.services",
    "diagnostics.services.nvidia_services",
    "diagnostics.system",
    "diagnostics.system.kernel_logs",
    "diagnostics.system.proc",
    "diagnostics.ib",
    "diagnostics.ib.main",
    "diagnostics.ib.models",
    "diagnostics.ib.config",
    "diagnostics.tests",
    "diagnostics.tests.gpu_tests",
    "diagnostics.troubleshoot",
    "diagnostics.troubleshoot.main",
]

for import_name in hidden_imports:
    args.extend(["--hidden-import", import_name])

# Add paths so PyInstaller can find the diagnostics package
args.extend(["--paths", PATHS_ARG])

# Collect all numpy files (it has C extensions that need special handling)
args.extend(["--collect-all", "numpy"])

# Set output directory and use module entry point
args.extend(["--distpath", ".", SCRIPT_PATH])

print(f"Embedding {len(found)} binaries into self-contained executable:")
for binary in found:
    print(f"  ✅ {binary}")

print(f"\nBuilding with PyInstaller ({len(args)} arguments)...")
print(f"Full command: {' '.join(args)}")

# Run PyInstaller with captured output
result = subprocess.run(args, capture_output=True, text=True)

# Show PyInstaller output
print("\nPyInstaller stdout:")
print(result.stdout)
if result.stderr:
    print("\nPyInstaller stderr:")
    print(result.stderr)

print(f"\nPyInstaller exit code: {result.returncode}")

# Debug: Show what files exist after PyInstaller
print("\nFiles created after PyInstaller:")

for item in sorted(os.listdir(".")):
    if os.path.isfile(item):
        size = os.path.getsize(item)
        executable = "(executable)" if os.access(item, os.X_OK) else ""
        print(f"  {item} ({size} bytes) {executable}")

# Check specifically for the expected binary
expected_binary = "brokkr-diagnostics"
if os.path.exists(expected_binary):
    size = os.path.getsize(expected_binary)
    print(f"\n✅ Success: {expected_binary} created ({size} bytes)")
    # Test the binary
    try:
        test_result = subprocess.run(
            [f"./{expected_binary}"],
            input="help\nquit\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(f"Binary test: {test_result.returncode}")
        if "NVIDIA GPU DIAGNOSTICS" in test_result.stdout:
            print("✓ Binary runs successfully!")
    except Exception as e:
        print(f"Binary test failed: {e}")
else:
    print(f"\n❌ Error: {expected_binary} not found")
    # Look for any executable files
    executables = [
        f for f in os.listdir(".") if os.path.isfile(f) and os.access(f, os.X_OK)
    ]
    if executables:
        print(f"Found executable files: {executables}")
    else:
        print("No executable files found")

    # Check for PyInstaller dist directory
    if os.path.exists("dist"):
        print("\nChecking dist directory:")
        for item in os.listdir("dist"):
            path = os.path.join("dist", item)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                executable = "(executable)" if os.access(path, os.X_OK) else ""
                print(f"  dist/{item} ({size} bytes) {executable}")

# Exit with PyInstaller's exit code
if result.returncode != 0:
    print(f"\n❌ PyInstaller failed with exit code {result.returncode}")
exit(result.returncode)
