"""
evaluator.py

This file is used to evaluate task 0 of AstroTinker Bot theme
in participant systems locally.
This will help the participants to rectify any installation problems
that they can rectify it.

"""
# standard imports
import platform
import subprocess

# third-party imports
import distro
from eyantra_autoeval.utils.common import run_shell_command
from rich.console import Console
from rich.prompt import Confirm

# AB Task 0 Evaluator Function
def evaluate():
    """
    Function Name : evaluate
    Arguments     : None
    Description   : Checks the platform information of participants and
                    evaluates them for theme suitability.
    """

    result = {}
    console = Console()
    # Setting "generate" to false will not generate json file
    result["generate"] = False
    # Gather System Information
    with console.status("[bold green]Gathering data...") as status:
        console.print(f"[green]Gathering system information[/green]")
        distribution = {
            "machine": platform.machine(),
            "version": distro.version(best=True),
            "name": distro.name(),
        }
        result["distro"] = distribution

    # Warning Participants if they are not using recommend OS.
    self_os_declaration = True
    if (
        result["distro"]["name"] != "Ubuntu"
        or "22.04" not in result["distro"]["version"]
        or result["distro"]["machine"] != "x86_64"
    ):
        console.print(
            f"""You seem to be using [bold][blue]{result["distro"]["name"]} {result["distro"]["version"]} ({result["distro"]["machine"]}) on environment[/bold][/blue]. We only support [bold][blue]Ubuntu 22.04 on (x86_64) on baremetal or Windows with WSL[/bold][/blue]. You may continue to use the existing setup, and you shall not be penalized for the same. However, we’ll officially only support Ubuntu 22.04 as the OS of choice, and we won’t be to help you out with any installation related questions or software compatibility issues."""
        )
        self_os_declaration = Confirm.ask(
            "Do you accept to take ownership of your setup and not seek help from e-Yantra for the same?"
        )
    elif result["distro"]["name"] == "Ubuntu":
        # Check if participants uses wsl
        uname = run_shell_command("uname -r")
        uname = uname.split('-')
        if uname[-1] == "Microsoft":
            console.print(f"""[bold][yellow]You are using {result["distro"]["name"]} {result["distro"]["version"]} ({result["distro"]["machine"]}) in WSL""")
            result["wsl"] = True
        else:
            console.print(f"""[bold][yellow]You are using standalone {result["distro"]["name"]} {result["distro"]["version"]} ({result["distro"]["machine"]}) system""")
            result["wsl"] = False
    else:
        console.print(f"[bold][red]You are neither using Ubuntu or WSL which is not allowed")
        result["generate"] = False

    result["self-os-declaration"] = self_os_declaration

    # Get all the package information
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
        risc_flag = False
        packages = packages[1:-1]
        packages = [p.split()[0:2] for p in packages]
        for i in packages:
            # Check If risc-v compiler is present
            if (i[0] == 'gcc-riscv64-unknown-elf/jammy,now'):
                result["apt"]["packages"]["installed"] = i
                risc_flag = True
                break
        if risc_flag:
            result["generate"] = True
            console.print(f"[bold][blue]Done!")
            console.print(f"[bold][blue]You are all set to enjoy our theme!")
        else:
            console.print(f"riscv-gcc-compiler is not installed.")

        if result["self-os-declaration"] == False:
            result["generate"] = False
            console.print(f"[bold][green]You have not agreed to take ownership for unsupported OS.")
        # Inform participants about the problem with installations
        if not result["generate"]:
            console.print(f"[bold][blue]Detected Problems with Installations!")
            console.print(f"[bold][red]JSON file is not generated.")

    return result
