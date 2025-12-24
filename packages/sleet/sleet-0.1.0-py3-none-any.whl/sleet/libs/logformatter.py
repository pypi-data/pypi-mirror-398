import termcolor as tc 

# Project Creation

def printInit(configName: str):
    print(f"{tc.colored('[⧗]', 'blue')} Starting project setup using config '{tc.colored(configName, "green")}'")

def printTaskDone(taskName: str, taskNum: int, taskCount: int):
    print(f"{tc.colored('[✔]', 'green')} ({taskNum}/{taskCount}) Completed task '{tc.colored(taskName, 'green')}'")

def printTaskFailed(taskName: str, taskNum: int, taskCount: int):
    print(f"{tc.colored('[✘]', 'red')} ({taskNum}/{taskCount}) Failed task '{tc.colored(taskName, 'red')}'")

def printDone():
    print(f"{tc.colored('[⧗]', 'blue')} Finished project setup!")

def printDoneFailed(failedTaskName: str, errorCode: str, errorMsg: str):
    print(f" ┣━ {tc.colored('Error:', 'red')} {errorMsg}")
    print(f" ┣━ {tc.colored('Error Code:', 'red')} {errorCode}")
    print(f" ┗━ {tc.colored('[✘]', 'red')} Project setup failed!")


# Data Log Command

def printDataMessage():
    print(f"{tc.colored("[🗁]", "blue")} Sleet data:")

def printDataRow(dataName: str, dataValue: str, last: bool = False):
    if last:
        print(f" ┗━ {tc.colored(dataName, "light_green")}: {dataValue}")
    else:
        print(f" ┣━ {tc.colored(dataName, "light_green")}: {dataValue}")