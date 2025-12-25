from __future__ import annotations

import os
from functools import cached_property
from typing import *

from petrus._core import utils
from petrus._core.calcs.BaseCalc import BaseCalc

if TYPE_CHECKING:
    from petrus._core.calcs.Prog import Prog


class File(BaseCalc):

    prog: Prog

    @staticmethod
    def _find(file: Any) -> Any:
        t: Any
        l: list[str]
        x: str
        if utils.isfile(file):
            return file
        t = os.path.splitext(file)[0]
        l = os.listdir()
        l.sort(reverse=True)
        for x in l:
            if t == os.path.splitext(x)[0]:
                return x
        return file

    core: Any

    @cached_property
    def core(self: Self) -> Any:
        return os.path.join("src", self.prog.project.name, "core", "__init__.py")

    def exists(self: Self, name: Any) -> bool:
        return os.path.exists(getattr(self, name))

    gitignore: str

    @property
    def gitignore(self: Self) -> str:
        return ".gitignore"

    license: Any

    @cached_property
    def license(self: Self) -> Any:
        ans: Any
        ans = self.prog.pp.get("project", "license", "file")
        if type(ans) is str:
            return ans
        return self._find("LICENSE.txt")

    main: Any

    @property
    def main(self: Self) -> Any:
        return os.path.join("src", self.prog.project.name, "__main__.py")

    init: Any

    @cached_property
    def init(self: Self) -> Any:
        return os.path.join("src", self.prog.project.name, "__init__.py")

    manifest: str

    @property
    def manifest(self: Self) -> str:
        return "MANIFEST.in"

    pp: str

    @property
    def pp(self: Self) -> str:
        return "pyproject.toml"

    readme: Any

    @cached_property
    def readme(self: Self) -> Any:
        ans: Any
        ans = self.prog.pp.get("project", "readme")
        if type(ans) is str and os.path.exists(ans):
            return ans
        return self._find("README.rst")

    setup: str

    @property
    def setup(self: Self) -> str:
        return "setup.cfg"
