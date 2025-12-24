import typer
from sleet.taskmaster import TaskMaster
from sleet.libs.configloader import ConfigMan
from pathlib import Path
import sleet.libs.logformatter as log
from platformdirs import user_config_path

app = typer.Typer()

@app.command()
def run(config: str, debug: bool = False):
    tm = TaskMaster()
    configPath = user_config_path("sleet", "Cheetah") / "configs"
    cfgl = ConfigMan(str(configPath))

    tm.executeConfig(cfgl.loadConfig(config), config)

@app.command()
def listData():
    log.printDataMessage()
    log.printDataRow("Config Path", str(user_config_path("sleet", "Cheetah") / "configs"), last=True)
