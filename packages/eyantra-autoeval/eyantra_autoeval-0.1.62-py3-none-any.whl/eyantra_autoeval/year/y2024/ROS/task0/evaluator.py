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

                            

cb_count = 0
seen_frames = set()

def evaluate():

    result = {}
    console = Console()
    
    with console.status("[bold green]Welcome to ROS2 MOOC...") as status:
        console.print(f"[bold green]Welcome to ROS2 MOOC...🤖[/bold green]")

    with console.status("[bold green]Gathering data🪄...") as status:

        console.print(f"[green]Gathering system information🪄[/green]")
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
    if (result["distro"]["name"] != "Ubuntu"
        or "22.04" not in result["distro"]["version"]
        or result["virtualized"]
        or result["dockerized"]):
        console.print(
            f"""You seem to be using [bold][blue]{result["distro"]["name"]} {result["distro"]["version"]} ({result["distro"]["machine"]}) on {"virtualized" if result["virtualized"] else ""}{"dockerized" if result["dockerized"] else ""} environment[/bold][/blue]. We only support [bold][blue]Ubuntu 22.04 on (x86_64) on baremetal[/bold][/blue]. You may continue to use the existing setup, and you shall not be penalized for the same. However, we’ll officially only support Ubuntu 22.04 as the OS of choice, and we won’t be to help you out with any installation related questions or package version incompatibility issues🙂."""
        )
    result["ros"] = {}


    with console.status("[bold green]Gathering data🪄...") as status:

        console.print(f"[green]Gathering information on python🪄[/green]")
        result["python"] = {}
        result["python"][
            "version"
        ] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        console.print(f"[green]Gathering information on ROS distribution🪄[/green]")
        
        result["ros"]["version"] = (
            subprocess.run(
                "source /opt/ros/humble/setup.bash && printenv ROS_DISTRO",
                capture_output=True,
                shell=True,
                executable="/bin/bash", 
            )
            .stdout.decode()
            .strip()
        )

        result["generate"] = True
        console.print(f"[bold][blue]Done 👍!!!")
        
        return result
