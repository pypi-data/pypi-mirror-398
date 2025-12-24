import importlib
import pkgutil
from pathlib import Path

from sleet.libs.registry import Registry
from sleet.libs.constants import const
import sleet.libs.logformatter as log

class TaskMaster:
    def __init__(self) -> None:
        self.registry = Registry()

        self.modules = []
        self.load_modules()

    def load_modules(self) -> None:
        builtins = "sleet.modules.builtins"
        builtinsPath = Path(__file__).parent / "modules" / "builtins"

        for moduleInfo in pkgutil.iter_modules([str(builtinsPath)]):
            moduleName = moduleInfo.name

            importPath = f"{builtins}.{moduleName}"
            module = importlib.import_module(importPath)

            if hasattr(module, "Module"):
                moduleClass = getattr(module, "Module")
                instance = moduleClass(self.registry)
                self.modules.append(instance)


    def executeConfig(self, config: dict, configName: str) -> None:
        tasks = config["exec"]
        totalTasks = len(tasks)

        log.printInit(configName)
       
        for i in range(totalTasks):
            task = tasks[i]
            taskName = next(iter(task))
            taskData = task[taskName]
            taskType = taskData["type"]

            try:
                task = self.registry.registry[taskType]
                task(taskData)
            except KeyError:
                print(self.registry.registry)
                log.printTaskFailed(taskName, i + 1, totalTasks)
                log.printDoneFailed(taskName, "001", f"Unknown task type: {taskType}")
                return

            log.printTaskDone(taskName, i + 1, totalTasks)

        log.printDone()