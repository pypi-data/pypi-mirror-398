import yaml, pathlib

class ConfigMan:
    def __init__(self, configPath: str) -> None:
        self.configPath = configPath

    def loadConfig(self, configName: str = "default"):
        filePath = self.configPath / pathlib.Path(f"{configName}.yaml")

        with open(filePath, "r") as f:
                    config = yaml.safe_load(f)

        return config