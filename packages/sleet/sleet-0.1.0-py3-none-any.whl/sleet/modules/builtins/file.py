from os import remove

class Module:

    def write(self, params: dict):
        with open(params["path"], "w") as f:
            f.write(params["content"])

    def delete(self, params: dict):
        remove(params["path"])


    def __init__(self, Registry):
        Registry.register("file-write", self.write)
        Registry.register("file-delete", self.delete)