import subprocess
from sleet.modules.helpers import run_command

class Module:

    def run(self, params: dict):

        params.setdefault("show-output", None)
        params.setdefault("command-list", None)
        params.setdefault("command", None)

        command_params = {
            "command": params["command"],
            "command-list": params["command-list"],
            "show-output": params["show-output"]
        }

        run_command(command_params)


    def __init__(self, Registry):
        Registry.register("command-run", self.run)