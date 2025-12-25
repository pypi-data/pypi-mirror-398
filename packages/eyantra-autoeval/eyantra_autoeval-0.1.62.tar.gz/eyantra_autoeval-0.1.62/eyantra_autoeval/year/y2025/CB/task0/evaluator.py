"""
*****************************************************************************************
*
*   ===================================================
*       CropDrop Bot (CB) Theme [eYRC 2025-26]
*   ===================================================
*
*  This script is intended to check the versions of the installed
*  software/libraries in Task 0 of CropDrop Bot (CB) Theme [eYRC 2025-26].
*
*  Filename:		evaluator.py
*  Created:			14/08/2025
*  Last Modified:	14/08/2025
*  Author:			e-Yantra Team
*  
*  This software is made available on an "AS IS WHERE IS BASIS".
*  Licensee/end user indemnifies and will keep e-Yantra indemnified from
*  any and all claim(s) that emanate from the use of the Software or
*  breach of the terms of this agreement.
*  
*  e-Yantra - An MHRD project under National Mission on Education using ICT (NMEICT)
*
*****************************************************************************************
"""

# ===== Standard imports =====
import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path
import psutil

# ===== Third-party imports =====
import distro
from rich.console import Console
from rich.prompt import Confirm
from eyantra_autoeval.utils.common import run_shell_command

# ===== Helper functions =====
def check_gcc_or_gplusplus():
    return shutil.which("gcc") is not None or shutil.which("g++") is not None

def check_python3_version():
    return sys.version_info.major >= 3

def find_file(filename, search_paths):
    """Search for a file in given paths recursively"""
    for base_path in search_paths:
        base_path = Path(base_path).expanduser()
        if base_path.exists():
            for root, dirs, files in os.walk(base_path):
                if filename in files:
                    return True
    return False

def Check_running(app):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and app  in proc.info['name']:
            return True
    return False

# ===== Main Evaluator =====
def evaluate():
    result = {}
    console = Console()
    result["generate"] = False

    # ===== OS Information =====
    with console.status("[bold green]Gathering system information..."):
        distribution = {
            "machine": platform.machine(),
            "version": distro.version(best=True),
            "name": distro.name(),
        }
        result["os_info"] = distribution
        result["os_type"] = platform.system()

    # ===== OS Compatibility Check =====
    self_os_declaration = True
    os_name = result["os_info"]["name"]
    os_version = result["os_info"]["version"]
    os_machine = result["os_info"]["machine"]
    os_type = result["os_type"]

    # WSL detection using uname -r
    uname = run_shell_command("uname -r").split("-")
    is_wsl = "Microsoft" in uname[-1] or "WSL" in uname[-1]

    # Case 1: Ubuntu 22.04 or 24.04 ()
    if os_name == "Ubuntu" and os_machine == "x86_64" and ("22.04" in os_version or "24.04" in os_version):
        if is_wsl:
            console.print("[red]Ubuntu in WSL is not supported. Please use baremetal Ubuntu.[/red]")
            result["generate"] = False
        else:
            console.print(f"[yellow]You are using Ubuntu {os_version} (baremetal)[/yellow]")
            result["wsl"] = False

    # Case 2: Windows (baremetal only)
    elif os_type == "Windows" and (os_machine == "x86_64" or os_machine == "AMD64"):
        console.print(f"[yellow]You are using Windows {os_version}[/yellow]")
        result["wsl"] = False

    # Unsupported OS
    else:
        console.print(
            f"""[yellow]You are using [bold blue]{os_name} {os_version} ({os_machine})[/bold blue].  
    We officially support Ubuntu 22.04 and 24.04 or Windows. You may continue, but e-Yantra will not help with OS-specific installation issues.[/yellow]"""
        )
        self_os_declaration = Confirm.ask(
            "Do you accept to take ownership of your setup and not seek OS-specific help from e-Yantra?"
        )

    result["self-os-declaration"] = self_os_declaration

    # ===== Installation Checks =====
    with console.status("[bold green]Checking required tools and software..."):
        result["gcc_or_g++_installed"] = check_gcc_or_gplusplus()
        result["python3_version_ok"] = check_python3_version()
        result["coppeliasim_installed"] = Check_running("coppeliaSim")
        result["stm32cubeide_installed"] = Check_running("stm32cubeide")


    # ===== Summary =====
    console.print("\n[bold underline]Installation Check Results:[/bold underline]")
    for key, value in {
        "GCC or G++": result["gcc_or_g++_installed"],
        "Python 3 Version OK": result["python3_version_ok"],
        "CoppeliaSim Installed": result["coppeliasim_installed"],
        "STM32CubeIDE Installed": result["stm32cubeide_installed"],
    }.items():
        status = "[green]✓[/green]" if value else "[red]✗[/red]"
        console.print(f"{status} {key}")

    # ===== Final Verdict =====
    if all([
        result["gcc_or_g++_installed"],
        result["python3_version_ok"],
        result["coppeliasim_installed"],
        result["stm32cubeide_installed"],
        self_os_declaration
    ]):
        console.print("\n[bold green]✅ All checks passed. Task 0 Output is correct![/bold green]")
        console.print("[bold yellow]JSON File Created.[/bold yellow]")
        result["generate"] = True
    else:
        console.print("\n[bold red]❌ Task 0 Output is incorrect! Please verify installations.[/bold red]")
        console.print("[bold yellow] JSON File Not Created.[/bold yellow]")
        
        result["generate"] = False

    return result


# if __name__ == "__main__":
#     evaluate()

