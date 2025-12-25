# standard imports
import platform
import subprocess
import sys

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
    if (
        result["distro"]["name"] != "Ubuntu"
        or "20.04" not in result["distro"]["version"]
        or result["distro"]["machine"] != "x86_64"
        or result["virtualized"]
        or result["dockerized"]
    ):
        console.print(
            f"""You seem to be using [bold][blue]{result["distro"]["name"]} {result["distro"]["version"]} ({result["distro"]["machine"]}) on {"virtualized" if result["virtualized"] else ""}{"dockerized" if result["dockerized"] else ""} environment[/bold][/blue]. We only support [bold][blue]Ubuntu 20.04 on (x86_64) on baremetal[/bold][/blue]. You may continue to use the existing setup, and you shall not be penalized for the same. However, we’ll officially only support Ubuntu 20.04 as the OS of choice, and we won’t be to help you out with any installation related questions or package version incompatibility issues."""
        )
        self_os_declaration = Confirm.ask(
            "Do you accept to take ownership of your setup and not seek help from e-Yantra for the same?"
        )
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

        console.print(f"[green]Gathering information on ROS packages[/green]")
        result["ros"] = {}
        result["ros"]["version"] = run_shell_command("rosversion -d")
        result["ros"]["packages"] = {}
        packages = run_shell_command("rosversion -a").split("\n")
        packages = [p.split(": ") for p in packages]
        result["ros"]["packages"]["installed"] = packages

        console.print(f"[green]Gathering information on gazebo[/green]")
        result["gazebo"] = {}
        result["gazebo"]["version"] = (
            subprocess.run(
                "gazebo --version | grep 'Gazebo' | awk '{print $NF}'",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
        )

        console.print(f"[green]Gathering information on python[/green]")
        result["python"] = {}
        result["python"][
            "version"
        ] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        console.print(f"[green]Gathering information on GDAL[/green]")
        result["gdal"] = {}
        result["gdal"]["version"] = (
            subprocess.run(
                "gdalinfo --version | awk '{print $2}' | sed 's/\,//'",
                capture_output=True,
                shell=True,
            )
            .stdout.decode()
            .strip()
        )

        result["generate"] = True

        console.print(f"[bold][blue]Done!")

    return result
