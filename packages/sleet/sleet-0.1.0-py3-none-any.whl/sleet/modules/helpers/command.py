import subprocess

def run_command(command_params):

    command_params.setdefault("show-output", None)
    command_params.setdefault("command-list", [])
    command_params.setdefault("command", None)

    subprocess.run(
        command_params["command"].split(" ") if command_params["command"] else command_params["command-list"],
        stdout=None if command_params["show-output"] else subprocess.DEVNULL,
        stderr=None if command_params["show-output"] else subprocess.DEVNULL,
        check=True
    )