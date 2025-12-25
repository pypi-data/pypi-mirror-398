# standard imports
import os
import shlex
import subprocess

# third-party imprts
from rich import print


def is_docker():
    path = "/proc/self/cgroup"
    return (
        os.path.exists("/.dockerenv")
        or os.path.isfile(path)
        and any("docker" in line for line in open(path))
    )


def run_shell_command(command):
    try:
        return (
            subprocess.check_output(shlex.split(command)).decode().strip()
        )  # nosec B603
    except Exception as err:
        print(err)
        return ""
