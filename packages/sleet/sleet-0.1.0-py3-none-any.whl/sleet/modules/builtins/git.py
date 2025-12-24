from sleet.modules.helpers import run_command

class Module:

    def init(self, params: dict):
        command = "git init"

        command_params = {"command": command}
        run_command(command_params)

    def commit(self, params: dict):
        params.setdefault("message", "Initial Commit Using Sleet")

        command = "git add ."
        run_command({"command": command})

        command = ["git", "commit", "-m", params["message"]]
        run_command({"command-list": command})


    def __init__(self, Registry):
        Registry.register("git-init", self.init)
        Registry.register("git-commit", self.commit)