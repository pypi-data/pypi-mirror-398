from typing import Callable

class Registry:
    def __init__(self):
        self.registry = {}

    
    def register(self, name: str, fnc: Callable):
        self.registry[name] = fnc