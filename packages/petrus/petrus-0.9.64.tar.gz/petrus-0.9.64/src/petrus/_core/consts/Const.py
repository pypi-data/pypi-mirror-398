import enum
import tomllib
from functools import cached_property
from importlib import resources
from typing import *


class Const(enum.Enum):
    const = None

    @cached_property
    def data(self: Self) -> dict:
        "This cached property holds the cfg data."
        text: str = resources.read_text("petrus._core.consts", "consts.toml")
        ans: dict = tomllib.loads(text)
        return ans
