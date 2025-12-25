from typing import *

from .BaseCalc import BaseCalc


class Text(BaseCalc):
    def __getattr__(self: Self, name: Any) -> Any:
        ans: Any
        name_: str
        name_ = str(name)
        if hasattr(type(self), name_):
            return object.__getattribute__(self, name_)
        if name_.startswith("_"):
            raise AttributeError(name_)
        if name_ in self._lock:
            raise Exception
        self._lock.add(name_)
        try:
            ans = self._calc(name_)
            object.__setattr__(self, name_, ans)
        finally:
            self._lock.remove(name_)
        return ans

    def __post_init__(self: Self) -> None:
        self._lock = set()

    def _calc(self: Self, name: Any) -> Any:
        file: Any
        lines: Optional[list]
        method: Callable
        stream: Any
        file = getattr(self.prog.file, name)
        try:
            with open(file, "r") as stream:
                lines = stream.readlines()
        except FileNotFoundError:
            lines = None
        if lines is not None:
            lines = list(map(str.rstrip, lines))
            lines = "\n".join(lines)
            return lines
        try:
            method = getattr(self, "_calc_" + name)
        except Exception:
            method = str
        return method()

    def _calc_core(self: Self) -> Any:
        n = self.prog.project.name
        return self.prog.draft.getitem("core").format(project=n)

    def _calc_gitignore(self: Self) -> Any:
        return self.prog.draft.getitem("gitignore")

    def _calc_init(self: Self) -> Any:
        n = self.prog.project.name
        return self.prog.draft.getitem("init").format(project=n)

    def _calc_license(self: Self) -> Any:
        d = dict()
        d["year"] = self.prog.year
        d["author"] = self.prog.author[0]
        ans = self.prog.draft.getitem("license").format(**d)
        return ans

    def _calc_main(self: Self) -> Any:
        n = self.prog.project.name
        return self.prog.draft.getitem("main").format(project=n)

    def _calc_manifest(self: Self) -> Any:
        n = self.prog.project.name
        return self.prog.draft.getitem("manifest").format(project=n)

    def _calc_readme(self: Self) -> Any:
        return self.prog.block.text
