from typing import *


class BaseCalc:

    def __delattr__(self: Self, name: Any) -> None:
        self.__check(name)
        object.__delattr__(self, name)

    def __init__(self: Self, prog: Any, /) -> None:
        self.prog = prog
        getattr(self, "__post_init__", int)()

    def __setattr__(self: Self, name: Any, value: Any) -> None:
        self.__check(name)
        object.__setattr__(self, name, value)

    def __check(self: Self, name: Any) -> None:
        if name.startswith("_"):
            return
        if not hasattr(super(), name):
            return
        raise AttributeError("readonly")
