import inspect
import os
import string
import sys
from functools import cached_property
from typing import *

from identityfunction import identityfunction

from petrus._core import utils
from petrus._core.calcs.BaseCalc import BaseCalc
from petrus._core.consts.Const import Const


class _empty:
    pass


class Project(BaseCalc):

    authors: Any
    classifiers: Any
    dependencies: Any
    description: Any
    keywords: Any
    license: Any
    name: Any
    readme: Any
    requires_python: Any
    urls: Any
    version: Any

    def __post_init__(self: Self) -> None:
        self._version = _empty

    @cached_property
    def authors(self: Self) -> Any:
        ans: Any
        author: dict
        used: Any
        fit: Any
        i: Any
        ans = self.get("authors", default=[])
        if type(ans) is not list:
            return ans
        ans = list(ans)
        author = dict()
        if self.prog.kwargs["author"]:
            author["name"] = self.prog.kwargs["author"]
        if self.prog.kwargs["email"]:
            author["email"] = self.prog.kwargs["email"]
        author = self.prog.easy_dict(author)
        used = False
        for i in range(len(ans)):
            try:
                ans[i] = dict(ans[i])
            except Exception:
                continue
            fit = utils.dict_match(ans[i], author)
            if fit and not used:
                ans[i].update(author)
            ans[i] = self.prog.easy_dict(ans[i])
            used |= fit
        if not used:
            ans.insert(0, author)
        return ans

    @cached_property
    def classifiers(self: Self) -> Any:
        preset: Any
        mit: str
        kwarg: Any
        ans: Any
        prefix: Any
        cleaned: Any
        x: Any
        status: Any
        preset = self.get("classifiers", default=[])
        if type(preset) is not list:
            return preset
        if utils.isfile(self.prog.file.license):
            mit = ""
        else:
            mit = Const.const.data["CONST"]["MIT"]
        kwarg = self.prog.kwargs["classifiers"]
        if kwarg == "":
            preset = utils.easy_list(preset)
            return preset
        ans = kwarg
        preset = ", ".join(preset)
        ans = ans.format(preset=preset, mit=mit)
        ans = ans.split(",")
        ans = self.format_classifiers(ans)
        if self.prog.development_status == "":
            ans = self.prog.easy_list(ans)
            return ans
        prefix = "Development Status :: "
        cleaned = list()
        for x in ans:
            if x.lower().startswith(prefix.lower()):
                continue
            cleaned.append(x)
        ans = cleaned
        status = prefix + self.prog.development_status
        ans.append(status)
        ans = self.format_classifiers(ans)
        ans = self.prog.easy_list(ans)
        return ans

    @cached_property
    def dependencies(self: Self) -> Any:
        x: Any
        y: list
        x = self.get("dependencies", default=[])
        if type(x) is not list:
            return x
        y = list(map(utils.fix_dependency, x))
        y = self.prog.easy_list(y)
        return y

    @cached_property
    def description(self: Self) -> Any:
        if self.prog.kwargs["description"]:
            return self.prog.kwargs["description"]
        if self.get("description") is not None:
            return self.get("description")
        return self.name

    @cached_property
    def keywords(self: Self) -> Any:
        return self.get("keywords", default=[])

    @cached_property
    def license(self: Self) -> Any:
        ans: Any
        ans = self.get("license")
        if ans is None:
            ans = dict()
        if type(ans) is not dict:
            return ans
        if "file" not in ans.keys():
            ans["file"] = self.prog.file.license
        return ans

    @classmethod
    def format_classifiers(cls: type, value: Iterable, /) -> list:
        ans: list
        ans = list(value)
        ans = [x.replace("::", " :: ") for x in ans]
        ans = [" ".join(x.split()) for x in ans]
        ans = list(map(str.strip, ans))
        ans = list(filter(identityfunction, ans))
        return ans

    def get(self: Self, *args: Any, default: Any = None) -> Any:
        return self.prog.pp.get("project", *args, default=default)

    @cached_property
    def name(self: Self) -> str:
        basename: Any
        raw: str
        ans: Any
        x: str
        basename = os.path.basename(os.getcwd())
        raw = str(self.get("name") or basename)
        ans = ""
        for x in raw:
            if x in (string.ascii_letters + string.digits):
                ans += x
            else:
                ans += "_"
        return ans

    @property
    def readme(self: Self) -> Any:
        return self.prog.file.readme

    @cached_property
    def requires_python(self: Self) -> Any:
        kwarg: Any
        preset: Any
        current: Any
        kwarg = self.prog.kwargs["requires_python"]
        preset = self.get("requires-python", default="")
        current = ">={0}.{1}.{2}".format(*sys.version_info)
        if kwarg == "":
            return preset
        kwarg = kwarg.format(preset=preset, current=current)
        kwarg = kwarg.split("\\|")
        kwarg = list(map(str.strip, kwarg))
        kwarg = next(filter(identityfunction, kwarg), None)
        return kwarg

    def todict(self: Self) -> Any:
        ans: Any
        x: Any
        y: Any
        ans = self.get(default={})
        for x in Const.const.data["CONST"]["PROJECT-KEYS"]:
            y = getattr(self, x)
            if y is None:
                continue
            x = x.replace("_", "-")
            ans[x] = y
        ans = self.prog.easy_dict(ans)
        return ans

    @cached_property
    def urls(self: Self) -> Any:
        ans: Any
        p: str
        ans = self.get("urls")
        if ans is None:
            ans = dict()
        if type(ans) is not dict:
            return ans
        if self.prog.github:
            ans.setdefault("Source", self.prog.github)
        p = f"https://pypi.org/project/{self.name}/"
        ans.setdefault("Index", p)
        p = f"https://pypi.org/project/{self.name}/#files"
        ans.setdefault("Download", p)
        ans = self.prog.easy_dict(ans)
        return ans

    @property
    def version(self: Self) -> Any:
        if self._version is _empty:
            self._version = self.prog.version_formatted
        return self._version
