import subprocess
from sleet.modules.helpers import run_command

class Module:

    def install(self, params: dict):
        params.setdefault("dev", False)

        command = f"uv add {" ".join(params["names"])} {"--dev" if params["dev"] else None}"
        run_command({"command": command})

    def remove(self, params: dict):
        params.setdefault("dev", False)

        command = f"uv remove {" ".join(params["names"])} {"--group dev" if params["dev"] else None}"
        run_command({"command": command})

    def venv(self, params: dict):
        params.setdefault("version", None)

        command = f"uv venv {f"--python {params["version"]}" if params["version"] else None}"
        run_command({"command": command})

    def init(self, params: dict):
        command = "uv init"
        run_command({"command": command})



    def __init__(self, Registry):
        Registry.register("uv-install", self.install)
        Registry.register("uv-remove", self.remove)
        Registry.register("uv-venv", self.venv)
        Registry.register("uv-init", self.init)