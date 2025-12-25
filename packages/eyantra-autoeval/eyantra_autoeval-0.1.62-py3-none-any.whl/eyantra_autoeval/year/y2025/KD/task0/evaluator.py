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


def evaluate():
    result = {}
    console = Console()
    with console.status("[bold green]Gathering data...") as status:
        console.print(f"[green]Gathering system information[/green]")
        distribution = {
            "machine": platform.machine(),
            "release": platform.release(),
            "system": platform.system(),
            "version": distro.version(best=True),
            "name": distro.name(),
        }
        result["distro"] = distribution

        result["virtualized"] = "hypervisor" in run_shell_command("cat /proc/cpuinfo")

        result["dockerized"] = is_docker()

    self_os_declaration = False
    result["self_os_declaration_confirm"] = None
    
    if (
        result["distro"]["name"] != "Ubuntu"
        or "22.04" not in result["distro"]["version"]
        or result["distro"]["machine"] != "x86_64"
        or result["virtualized"]
        or result["dockerized"]
    ):
        console.print(
            f"""You seem to be using [bold][blue]{result["distro"]["name"]} {result["distro"]["version"]} ({result["distro"]["machine"]}) on {"virtualized" if result["virtualized"] else ""}{"dockerized" if result["dockerized"] else ""} environment[/bold][/blue]. We only support [bold][blue]Ubuntu 22.04 on (x86_64) on baremetal[/bold][/blue]. You may continue to use the existing setup, and you shall not be penalized for the same. However, we’ll officially only support Ubuntu 22.04 as the OS of choice, and we won’t be to help you out with any installation related questions or package version incompatibility issues."""
        )
        self_os_declaration = Confirm.ask(
            "Do you accept to take ownership of your setup and not seek help from e-Yantra for the same?"
        )
        result["self_os_declaration_confirm"] = self_os_declaration
    result["self-os-declaration"] = self_os_declaration

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

        console.print(f"[green]Gathering information on ROS version[/green]")
        result["ros"] = {}
        # result["ros"]["version"] = run_shell_command("ROS_DISTRO")
        result["ros"]["version"] = (
            subprocess.run(
                "printenv ROS_DISTRO",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
        )
        # result["ros"]["packages"] = {}
        # packages = run_shell_command("rosversion -a").split("\n")
        # packages = [p.split(": ") for p in packages]
        # result["ros"]["packages"]["installed"] = packages

        console.print(f"[green]Gathering information on gazebo[/green]")
        result["gazebo"] = {}
        result["gazebo"]["version"] = (
            subprocess.run(
                "ign gazebo --version | grep 'Gazebo' | awk '{print $NF}'",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
        )

        console.print(f"[green]Gathering information on python[/green]")
        result["python"] = {}
        result["python"]["version"] = (
            subprocess.run(
                "python3 -V",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
            .split()[1]
        )

        console.print(f"[green]Gathering information on ros_gz_bridge[/green]")
        result["ros_gz_bridge"] = {}
        result["ros_gz_bridge"] = (
            subprocess.run(
                "ros2 pkg prefix ros_gz_bridge",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
        )

        if result["ros_gz_bridge"] != "/opt/ros/humble":
            result["generate"] = False
            console.print(f"[bold][red]ros_gz_bridge is not found on this system.")
        else:
            console.print(f"[bold][green]ros_gz_bridge is succesfully installed on this system.")

        result["generate"] = True
        if result["ros"]["version"] != "humble":
            result["generate"] = False
            console.print(f"[bold][red]ROS2 humble is not installed on this system.")
        else:
            console.print(f"[bold][green]ROS2 humble is succesfully installed on this system.")

        if result["gazebo"]["version"] != "6.17.0":
            result["generate"] = False
            console.print(f"[bold][red]Gazebo fortress not found on this system.")
        else:
            console.print(f"[bold][green]Gazebo fortress is succesfully installed on this system.")

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
