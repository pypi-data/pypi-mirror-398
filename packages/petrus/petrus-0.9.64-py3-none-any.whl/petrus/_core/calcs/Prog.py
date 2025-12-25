import datetime
import os
import shutil
import string
import subprocess
import sys
from functools import cached_property
from typing import Any, Iterable, Self

import tomlhold
import v440

from petrus._core import utils
from petrus._core.calcs.BaseCalc import BaseCalc
from petrus._core.calcs.Block import Block
from petrus._core.calcs.Draft import Draft
from petrus._core.calcs.File import File
from petrus._core.calcs.Git import Git
from petrus._core.calcs.Project import Project
from petrus._core.calcs.Text import Text


class Prog(BaseCalc):

    def __init__(self: Self, kwargs: Any, /) -> None:
        self.kwargs = kwargs
        self.__post_init__()

    def __post_init__(self: Self) -> None:
        self.git.init()
        self.git.ignore()
        for p in self.packages:
            self.tests(p)
        self.pp["project"] = self.project.todict()
        self.pp["build-system"] = self.build_system
        self.pp.data = self.easy_dict(self.pp.data)
        self.text.pp = self.pp.dumps()
        self.save("license")
        self.save("manifest")
        self.save("pp")
        self.save("readme")
        self.save("setup")
        utils.run_isort()
        utils.run_black(os.getcwd())
        utils.run_html_prettifier(os.getcwd())
        self.git.commit_version()
        self.git.push()
        self.pypi()

    @cached_property
    def author(self: Self) -> Any:
        f = lambda z: str(z).strip()
        n = f(self.kwargs["author"])
        e = f(self.kwargs["email"])
        x = n, e
        authors = self.project.authors
        if type(authors) is not list:
            return x
        for a in authors:
            if type(a) is not dict:
                continue
            n = f(a.get("name", ""))
            e = f(a.get("email", ""))
            y = n, e
            if y != ("", ""):
                return y
        return x

    @cached_property
    def block(self: Self) -> Block:
        return Block(self)

    @cached_property
    def build_system(self: Self) -> Any:
        ans = self.pp.get("build-system")
        if type(ans) is dict:
            return self.easy_dict(ans)
        if ans is not None:
            return ans
        ans = dict()
        ans["requires"] = ["setuptools>=64.0"]
        ans["build-backend"] = "setuptools.build_meta"
        ans = self.easy_dict(ans)
        return ans

    @cached_property
    def development_status(self: Self) -> Any:
        kwarg: Any
        values: Any
        i: Any
        ans: Any
        x: Any
        j: Any
        kwarg = self.kwargs["development_status"]
        if kwarg == "infer":
            kwarg = self.development_status_infered
        if kwarg == "":
            return ""
        kwarg = kwarg.strip().lower()
        values = [
            "1 - Planning",
            "2 - Pre-Alpha",
            "3 - Alpha",
            "4 - Beta",
            "5 - Production/Stable",
            "6 - Mature",
            "7 - Inactive",
        ]
        i = float("inf")
        ans = list()
        for x in values:
            try:
                j = x.lower().index(kwarg)
            except ValueError:
                continue
            if j == i:
                ans.append(x)
            if j < i:
                ans = [x]
                i = j
        (ans,) = ans
        return ans

    @cached_property
    def development_status_infered(self: Self) -> str:
        v: v440.Version
        try:
            v = v440.Version(self.project.version)
        except:
            return ""
        if v.public.qual.pre.lit == "a":
            return "alpha"
        if v.public.qual.pre.lit == "b":
            return "beta"
        if v == self.version_default:
            return "planning"
        if v.public.base.release < v440.core.Release.Release("0.1"):
            return "pre"
        if v.public.qual.isdevrelease():
            return "alpha"
        if v.public.qual.pre.lit == "rc":
            return "beta"
        if not v.public.qual.ispostrelease():
            if v.public.base.release.major < 1:
                return "alpha"
            if v.public.base.release.major > 1900:
                return "beta"
        if v.public.base.release.major < 4:
            return "stable"
        return "mature"

    @cached_property
    def draft(self: Self) -> Draft:
        return Draft(self)

    @staticmethod
    def easy_dict(dictionary: Any, *, purge: Any = False) -> dict:
        d: dict
        keys: Iterable
        ans: dict
        d = dict(dictionary)
        keys = sorted(list(d.keys()))
        ans = {k: d[k] for k in keys}
        return ans

    @staticmethod
    def easy_list(iterable: Iterable) -> list:
        ans = list(set(iterable))
        ans.sort()
        return ans

    @cached_property
    def file(self: Self) -> File:
        return File(self)

    @cached_property
    def git(self: Self) -> Git:
        return Git(self)

    @cached_property
    def github(self: Self) -> str:
        u: Any
        u = self.kwargs["github"]
        if u == "":
            return ""
        return f"https://github.com/{u}/{self.project.name}/"

    def ispkg(self: Self, path: Any, *, todir: Any = True) -> bool:
        root: Any
        name: Any
        tr: Any
        ext: Any
        init: Any
        pro: Any
        root, name = os.path.split(path)
        tr, ext = os.path.splitext(name)
        if os.path.isdir(path):
            init = os.path.join(path, "__init__.py")
            if not os.path.exists(init):
                return False
            if not os.path.isfile(init):
                raise FileExistsError
            if ext != "":
                raise Exception(ext)
            return True
        if os.path.isfile(path):
            if ext != ".py":
                return False
            if not todir:
                return True
            pro = os.path.join(root, tr)
            init = os.path.join(pro, "__init__.py")
            if os.path.exists(init):
                raise FileExistsError
            self.mkdir(pro)
            self.git.move(path, init)
            return True
        return False

    @classmethod
    def mkdir(cls: type, path: Any) -> None:
        if utils.isdir(path):
            return
        os.mkdir(path)

    def mkpkg(self: Self, path: Any) -> None:
        f: Any
        if self.ispkg(path):
            return
        self.mkdir(path)
        f = os.path.join(path, "__init__.py")
        self.touch(f)

    @cached_property
    def packages(self: Self) -> list:
        ans: list
        self.mkdir("src")
        ans = []
        for x in os.listdir("src"):
            y = os.path.join("src", x)
            if self.ispkg(y):
                ans.append(y)
        if len(ans):
            return self.easy_list(ans)
        for x in os.listdir():
            if self.ispkg(x, todir=False):
                ans.append(x)
        if len(ans):
            return self.easy_list(ans)
        if self.file.exists("pp"):
            return list()
        pro = os.path.join("src", self.project.name)
        if not self.ispkg(pro):
            self.save("core")
            self.save("init")
            self.save("main")
        return [pro]

    @staticmethod
    def parse_bump(line: Any) -> Any:
        line = line.strip()
        if not line.startswith("bump"):
            raise ValueError
        line = line[4:].lstrip()
        if not line.startswith("("):
            raise ValueError
        line = line[1:].lstrip()
        if not line.endswith(")"):
            raise ValueError
        line = line[:-1].rstrip()
        if line.endswith(","):
            line = line[:-1].rstrip()
        chars = string.digits + string.whitespace + ",-"
        if line.strip(chars):
            raise ValueError
        line = line.split(",")
        line = [int(x.strip()) for x in line]
        return line

    @cached_property
    def pp(self: Self) -> tomlhold.TOMLHolder:
        return tomlhold.TOMLHolder.loads(self.text.pp)

    @cached_property
    def project(self: Self) -> Project:
        return Project(self)

    @staticmethod
    def py(*args: Any) -> Any:
        args_: list
        args_ = [sys.executable, "-m"] + list(args)
        return subprocess.run(args_)

    def pypi(self: Self) -> None:
        args: list
        token: Any
        shutil.rmtree("dist", ignore_errors=True)
        if utils.py("build").returncode:
            return
        args = ["twine", "upload", "dist/*"]
        token = self.kwargs["token"]
        if token != "":
            args += ["-u", "__token__", "-p", token]
        subprocess.run(args)

    def save(self: Self, name: Any, /) -> None:
        file: Any
        text: Any
        root: Any
        roots: Any
        stream: Any
        file = getattr(self.file, name)
        text = getattr(self.text, name)
        roots = list()
        root = file
        while True:
            root = os.path.dirname(root)
            if not root:
                break
            if os.path.exists(root):
                break
            roots.append(root)
        while roots:
            root = roots.pop()
            os.mkdir(root)
        with open(file, "w") as stream:
            stream.write(text)

    def tests(self: Self, pkg: Any) -> None:
        a: Any
        b: Any
        file: Any
        stream: Any
        text: Any
        base: Any
        a = os.path.join(pkg)
        b = os.path.join(pkg, "tests")
        self.mkpkg(a)
        if self.ispkg(b):
            return
        self.mkdir(b)
        file = os.path.join(b, "__init__.py")
        if not utils.isfile(file):
            text = self.draft.getitem("tests")
            base = os.path.basename(pkg)
            text = text.format(pkg=base)
            with open(file, "w") as stream:
                stream.write(text)
        for file in os.listdir(b):
            if file == "__init__.py":
                continue
            if file.startswith("."):
                continue
            return
        file = os.path.join(b, "test_1984.py")
        with open(file, "w") as stream:
            stream.write(self.draft.getitem("test_1984"))

    @cached_property
    def text(self: Self) -> Text:
        return Text(self)

    @staticmethod
    def touch(file: Any) -> None:
        if utils.isfile(file):
            return
        with open(file, "w"):
            pass

    @cached_property
    def version_default(self: Self) -> str:
        return "0.0.0.dev0"

    @cached_property
    def version_formatted(self: Self) -> str:
        ans: Any
        kwarg: Any
        ans = self.version_unformatted
        kwarg = self.kwargs["vformat"]
        try:
            ans = v440.Version(ans)
            ans = format(ans, kwarg)
        except v440.VersionError:
            pass
        return str(ans)

    @cached_property
    def version_unformatted(self: Self) -> Any:
        args: Any
        a: Any
        b: Any
        a = self.kwargs["v"]
        b = self.project.get("version")
        if a == "":
            if b is None:
                return self.version_default
            else:
                return b
        try:
            args = self.parse_bump(a)
        except ValueError:
            return a
        if b is None:
            return self.version_default
        try:
            c = v440.Version(b)
            c.release.bump(*args)
        except v440.VersionError as e:
            print(e, file=sys.stderr)
            return b
        return str(c)

    @cached_property
    def year(self: Self) -> Any:
        ans: Any
        current: str
        ans = self.kwargs["year"]
        current = str(datetime.datetime.now().year)
        ans = ans.format(current=current)
        return ans
