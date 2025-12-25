# standard imports
import platform
import subprocess
import sys
import os

# third-party imprts
import distro
from eyantra_autoeval.utils.common import is_docker, run_shell_command
from rich import print
from rich.console import Console
from rich.prompt import Confirm

key = "eY@Ntr@2025"


def evaluate():
    result = {}
    console = Console()
    try:
        import cryptocode

    except ImportError:
        console.print("[red]cryptocode module is not installed. Please install it using 'pip3 install cryptocode'.[/red]")
        sys.exit(1)
    with console.status("[bold green]Gathering data...") as status:
        console.print(f"[green]Gathering system information[/green]")
        distribution = {
            "machine": cryptocode.encrypt(platform.machine(), key),
            "processor": cryptocode.encrypt(platform.processor(), key),
            "release": cryptocode.encrypt(platform.release(), key),
            "system": cryptocode.encrypt(platform.system(), key),
            "version": cryptocode.encrypt(distro.version(best=True), key),
            "name": cryptocode.encrypt(distro.name(), key),
        }
        result["distro"] = distribution

        result["virtualized"] = cryptocode.encrypt(str("hypervisor" in run_shell_command("cat /proc/cpuinfo")), key)

        result["dockerized"] = cryptocode.encrypt(str(is_docker()), key)

    self_os_declaration = False
    result["self_os_declaration_confirm"] = None
    
    if (
        cryptocode.decrypt(result["distro"]["name"], key) != "Ubuntu"
        or "22.04" not in cryptocode.decrypt(result["distro"]["version"], key)
        or cryptocode.decrypt(result["distro"]["machine"], key) != "x86_64"
        or cryptocode.decrypt(result["virtualized"], key) != "False"
        or cryptocode.decrypt(result["dockerized"], key) != "False"
    ):
        console.print(
            f"""You seem to be using [bold][blue]{cryptocode.decrypt(result["distro"]["name"], key)} {cryptocode.decrypt(result["distro"]["version"], key)} ({cryptocode.decrypt(result["distro"]["machine"], key)}) on {"virtualized" if cryptocode.decrypt(result["virtualized"], key) else ""}{"dockerized" if cryptocode.decrypt(result["dockerized"], key) else ""} environment[/bold][/blue]. We only support [bold][blue]Ubuntu 22.04 on (x86_64) on baremetal[/bold][/blue]. You may continue to use the existing setup, and you shall not be penalized for the same. However, we’ll officially only support Ubuntu 22.04 as the OS of choice, and we won’t be to help you out with any installation related questions or package version incompatibility issues."""
        )
        self_os_declaration = Confirm.ask(
            "Do you accept to take ownership of your setup and not seek help from e-Yantra for the same?"
        )
        result["self_os_declaration_confirm"] = cryptocode.encrypt(str(self_os_declaration), key)
    result["self-os-declaration"] = cryptocode.encrypt(str(self_os_declaration), key)

    with console.status("[bold green]Gathering data...") as status:
        console.print(f"[green]Gathering information on system packages[/green]")
        result["apt"] = {}
        result["apt"]["packages"] = {}
        packages = (
            subprocess.run(
                "apt list --installed",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .split("\n")
        )
        packages = packages[1:-1]
        packages = [p.split()[0:2] for p in packages]
        result["apt"]["packages"]["installed"] = packages

        console.print(f"[green]Gathering information on pip packages[/green]")
        packages = run_shell_command("pip3 freeze").split("\n")
        packages = [p.split("==") for p in packages]

        result["pip3"] = {}
        result["pip3"]["packages"] = {}
        result["pip3"]["packages"]["installed"] = packages

        console.print(f"[green]Gathering information on ROS packages[/green]")
        result["ros"] = {}
        # result["ros"]["version"] = run_shell_command("ROS_DISTRO")
        result["ros"]["version"] = cryptocode.encrypt((
            subprocess.run(
                "printenv ROS_DISTRO",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
        ), key)
        # result["ros"]["packages"] = {}
        # packages = run_shell_command("rosversion -a").split("\n")
        # packages = [p.split(": ") for p in packages]
        # result["ros"]["packages"]["installed"] = packages

        console.print(f"[green]Gathering information on gazebo[/green]")
        result["gazebo"] = {}
        result["gazebo"]["version"] = cryptocode.encrypt((
            subprocess.run(
                "ign gazebo --version | grep -oP '(?<=version )\S+'",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
        ), key)

        console.print(f"[green]Gathering information on python[/green]")
        result["python"] = {}
        result["python"]["version"] = cryptocode.encrypt((
            subprocess.run(
                "python3 -V",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
            .split()[1]
        ), key)

        console.print(f"[green]Gathering information on python[/green]")
        result["python"] = {}
        result["python"][
            "version"
        ] = cryptocode.encrypt(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", key)

        result["generate"] = True
        if cryptocode.decrypt(result["ros"]["version"], key) != "humble":
            result["generate"] = False
            console.print(f"[bold][red]ROS2 humble is not installed on this system.")

        if not cryptocode.decrypt(result["gazebo"]["version"], key).startswith("6"):
            result["generate"] = False
            console.print(f"[bold][red]Gazebo version 6.16.0 not found on this system.")

        # if result["python"]["version"] >= "3.10.0":
        #     result["generate"] = False
        #     console.print(f"[bold][red]Python version is not installed correctly on this system.")
        #     console.print(f"Python version: {result['python']['version']}")

        if result["self-os-declaration"] == False:
            if result["self_os_declaration_confirm"] == False:
                result["generate"] = False
                console.print(f"[bold][red]You have not agreed to take ownership for unsupported OS.")
        # Inform participants about the problem with installations
        if not result["generate"]:
            console.print(f"[bold][yellow]Detected Problems with Installations!")
            console.print(f"[bold][red]JSON file is not generated.")
            
        if result["generate"] == True:
            console.print(f"[bold][blue]You are all set to Fly!")

    
    return result
