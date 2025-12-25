import importlib.resources
from typing import *

from petrus._core.calcs.BaseCalc import BaseCalc


class Draft(BaseCalc):

    def __getattr__(self: Self, name: str) -> Any:
        return self.getitem(name)

    def __post_init__(self: Self) -> None:
        self._data = dict()

    def getitem(self: Self, key: str, /) -> str:
        if key not in self._data.keys():
            self._data[key] = importlib.resources.read_text(
                "petrus.drafts", "%s.txt" % key
            )
        return self._data[key]
