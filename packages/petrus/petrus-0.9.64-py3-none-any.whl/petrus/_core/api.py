import argparse
import contextlib
import dataclasses
import functools
import os
import tomllib
import types
import typing
from importlib import metadata, resources
from typing import *

from petrus._core.calcs.Prog import Prog
from petrus._core.consts.Const import Const

__all__ = ["main", "run"]


def _cfgfile() -> Any:
    return resources.files("petrus").joinpath("config.toml")


def _desc() -> str:
    return Const.const.data["CONST"]["DESC"] % (str(_cfgfile()), _link())


def _inputs() -> dict:
    pairs: list
    pairs = list(Const.const.data["INPUTS"].items())
    pairs = list(_input_format(*x) for x in pairs)
    pairs.sort(key=_inputs_sortkey)
    return dict(pairs)


def _input_format(x: Any, y: Any, /) -> tuple:
    return x.strip(), y.strip()


def _inputs_sortkey(pair: tuple) -> Any:
    if pair[0] in {"help", "path", "version"}:
        raise KeyError
    if "-" in pair[0]:
        raise KeyError
    return pair[0]


def _link() -> str:
    return Const.const.data["CONST"]["LINK"]


def _run_deco(old: Any, /) -> types.FunctionType:
    doc = _desc()
    doc += "\n"
    for k, v in _inputs().items():
        old.__annotations__[k] = typing.Optional[str]
        field = dataclasses.field(
            default=None,
            kw_only=True,
        )
        setattr(old, k, field)
        doc += f"\n{k}: {v}"
    old = dataclasses.dataclass(old, frozen=True)

    @functools.wraps(old)
    def new(*args: Any, **kwargs: Any) -> None:
        old(*args, **kwargs)

    new.__doc__ = doc
    return new


def main(args=None) -> None:
    parser: argparse.ArgumentParser
    parser = argparse.ArgumentParser(
        description=_desc(),
        fromfile_prefix_chars="@",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        dest="version",
        version=metadata.version("petrus"),
    )
    parser.add_argument(
        "path",
        nargs="?",
        help=Const.const.data["CONST"]["PATH_HELP"],
    )
    for k, v in _inputs().items():
        opt = "--" + k.replace("_", "-")
        parser.add_argument(opt, help=v)
    ns = parser.parse_args(args)
    kwargs = vars(ns)
    _prog(**kwargs)


@_run_deco
class run:
    path: typing.Optional[str] = None

    def __post_init__(self: Self) -> None:
        kwargs = dataclasses.asdict(self)
        _prog(**kwargs)


def _prog(path: Any, **kwargs: Any) -> Any:
    try:
        cfg = _cfgfile().read_text()
    except:
        cfg = ""
    cfg = tomllib.loads(cfg)
    default = cfg.get("default", {})
    for k in kwargs.keys():
        if kwargs[k] is None:
            kwargs[k] = str(default.get(k, ""))
    try:
        root = cfg["general"]["root"]
    except KeyError:
        root = None
    paths = [os.getcwd(), root, path]
    paths = filter(lambda x: x is not None, paths)
    paths = [_normpath(x) for x in paths]
    wd = os.path.join(*paths)
    if not os.path.isdir(wd):
        os.mkdir(wd)
    with contextlib.chdir(wd):
        Prog(kwargs)


def _normpath(path: Any) -> Any:
    ans: Any
    ans = path
    ans = os.path.expanduser(ans)
    ans = os.path.expandvars(ans)
    ans = os.path.normpath(ans)
    return ans
