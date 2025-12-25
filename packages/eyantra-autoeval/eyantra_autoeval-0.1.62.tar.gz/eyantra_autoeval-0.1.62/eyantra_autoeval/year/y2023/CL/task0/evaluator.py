# standard imports
import platform
import subprocess
import sys
import os
import json

# third-party imprts
import distro
from eyantra_autoeval.utils.common import is_docker, run_shell_command
from rich import print
from rich.console import Console
from rich.prompt import Confirm

cb_count = 0
seen_frames = set()
cl_secret_pw = "ajracl2324"
base_link_to_frames = ['FWR', 'FWL', 'RWR', 'RWL']


def tf_callback(msg):
    global cb_count, seen_frames
    for transform in msg.transforms:
        if transform.header.frame_id == 'ebot_base_link' and transform.child_frame_id in base_link_to_frames:
            if transform.child_frame_id not in seen_frames:
                seen_frames.add(transform.child_frame_id)
    cb_count += 1


def get_joint_states(console):
    try:
        source_output = subprocess.run("bash -c 'source /opt/ros/humble/setup.bash'", shell=True)
        if source_output.returncode == 0:
            import rclpy
            from tf2_msgs.msg import TFMessage
            from rclpy.duration import Duration
        elif source_output.returncode == 1:
            console.print(f'[red]-> Failed to source ros setup. Try first running :\n\n\t\'source /opt/ros/humble/setup.bash\'\n[/red]')
            return ""
    except Exception as e:
        console.print(f'[red]-> Failed to import \'rclpy\'. Try first running :\n\n\t\'source /opt/ros/humble/setup.bash\'\n[/red]')

    global cb_count
      
    rclpy.init(args=None)
    node = rclpy.create_node('tf_subscriber_once_node')
    subscription = node.create_subscription(TFMessage, '/tf', tf_callback, 10)

    try:
        timeout_duration = Duration(seconds=3)
        timeout_seconds = timeout_duration.nanoseconds / 1e9
        start_time = node.get_clock().now()
        while rclpy.ok() and cb_count < 20 and (node.get_clock().now() - start_time) < timeout_duration:
            rclpy.spin_once(node, timeout_sec=timeout_seconds)
        if cb_count == 0:
            return ""
    except Exception as e:
        console.print(f'[red]-> Error casued due to: {str(e)}[/red]')
        return ""

    node.destroy_node()
    rclpy.shutdown()

    return list(seen_frames)


def evaluate():

    result = {}
    console = Console()

    with console.status("[bold green]Gathering data...") as status:

        result["autoeval_version"] = "0.1.1"

        console.print(f"[green]\n##############################################\nGathering system information[/green]")
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


    self_os_declaration = True
    if (result["distro"]["name"] != "Ubuntu"
        or "22.04" not in result["distro"]["version"]
        # or result["distro"]["machine"] != "x86_64"
        or result["virtualized"]
        or result["dockerized"]):
        console.print(
            f"""You seem to be using [bold][blue]{result["distro"]["name"]} {result["distro"]["version"]} ({result["distro"]["machine"]}) on {"virtualized" if result["virtualized"] else ""}{"dockerized" if result["dockerized"] else ""} environment[/bold][/blue]. We only support [bold][blue]Ubuntu 22.04 on (x86_64) on baremetal[/bold][/blue]. You may continue to use the existing setup, and you shall not be penalized for the same. However, we’ll officially only support Ubuntu 22.04 as the OS of choice, and we won’t be to help you out with any installation related questions or package version incompatibility issues."""
        )
        self_os_declaration = Confirm.ask("Do you accept to take ownership of your setup and not seek help from e-Yantra for the same?")
    result["self-os-declaration"] = self_os_declaration

    if self_os_declaration:
        result["generate"] = True
    else:
        result["generate"] = False
        console.print(f"[bold][blue]Sorry, without providing confirmation, we can't proceed :(")
        console.print(f"[bold][red]JSON file is not generated.")
        return result

    with console.status("[bold green]Gathering data...") as status:

        console.print(f"[green]Gathering information on python[/green]")
        result["python"] = {}
        result["python"][
            "version"
        ] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        console.print(f"[green]Gathering information on ROS distribution[/green]")
        result["ros"] = {}
        result["ros"]["version"] = os.getenv("ROS_DISTRO")
        
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

        console.print(f"[green]Gathering information on gazebo real time factor[/green]")
        try:
            source_output = subprocess.run("bash -c 'gz stats -p -d 1'", shell=True, capture_output=True)
            if source_output.returncode == 0:
                if source_output.stderr.decode() == "An instance of Gazebo is not running.\n":
                    console.print(f'[red]-> Gazebo instance is not running. Launch ebot warehouse first :([/red]')
                    result["gazebo"]["RTF"] = ""
                else:
                    lines = source_output.stdout.decode().split('\n')
                    rtf_values = [line.split(',')[0].strip() for line in lines[1:-1]]
                    rtf_values = [float(value) for value in rtf_values]
                    if len(rtf_values) == 0:
                        console.print(f'[red]-> Real Time Factor for gazebo not found. Check if gazebo is properly running :([/red]')
                        result["gazebo"]["RTF"] = ""
                    else:
                        result["gazebo"]["RTF"] = rtf_values[-1]
            elif source_output.returncode == 127 and source_output.stderr.decode() == "bash: line 1: gz: command not found\n":
                console.print(f'[red]-> Gazebo not found. Try installing gazebo first.[/red]')
                result["gazebo"]["RTF"] = ""
            else:
                console.print(f'[red]-> Failed to get real time factor from gazebo. Try again :([/red]')
                result["gazebo"]["RTF"] = ""
        except Exception as e:
            console.print(f'[red]-> Gazebo not found. Check if gazebo is properly installed :([/red]')
            result["gazebo"]["RTF"] = ""

        console.print(f"[green]Gathering information on robot joint states[/green]")
        result["gazebo"]["joint_states"] = get_joint_states(console)

        console.print(f"[bold][blue]Done!")

        # console.print(result)

    return result




