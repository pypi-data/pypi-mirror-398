import importlib.metadata
import os
import string
import subprocess
import sys
from typing import *

import black
import bs4
import filelisting
import isort
import requests


def dict_match(a: Any, b: Any, /) -> bool:
    a = dict(a)
    b = dict(b)
    keys = set(a.keys()) & set(b.keys())
    ans = all(a[k] == b[k] for k in keys)
    return ans


def fix_dependency(line: str, /) -> str:
    ans: str = line.strip()
    chars: set = set(ans)
    chars -= set(string.ascii_letters)
    chars -= set(string.digits)
    chars -= set("-_")
    if len(chars):
        return ans
    version = _get_some_version(ans)
    if version is None:
        return ans
    opener: str = ""
    x: str
    for x in version:
        if x in string.digits:
            opener += x
        else:
            break
    limit: int = int(opener) + 1
    ans: str = f"{ans}>={version},<{limit}"
    return ans


def prettify_html(file: str) -> None:
    # Read the HTML file
    with open(file, "r", encoding="utf-8") as stream:
        content = stream.read()

    # Parse the HTML content
    soup = bs4.BeautifulSoup(content, "html.parser")

    # Beautify the HTML
    formatter = bs4.formatter.HTMLFormatter(indent=4)
    beautified_html = soup.prettify(formatter=formatter)

    # Save the beautified HTML to a new file
    with open(file, "w", encoding="utf-8") as stream:
        stream.write(beautified_html)


def run_black(path: Any) -> Any:
    try:
        return black.main([path])
    except:
        pass


def run_html_prettifier(path: Any) -> None:
    ext: Any
    file: str
    filename: Any
    for file in filelisting.file_generator(path):
        filename = os.path.basename(file)
        ext = os.path.splitext(filename)
        if ext != ".html":
            continue


def run_isort() -> None:
    files: list = []
    walk: Iterator = os.walk(os.getcwd())
    for root, dnames, fnames in walk:
        for fname in fnames:
            f = os.path.join(root, fname)
            files.append(f)
    for f in files:
        if os.path.splitext(f)[1] == ".py":
            isort.file(f)


def isdir(path: Any) -> bool:
    if not os.path.exists(path):
        return False
    if not os.path.isdir(path):
        raise ValueError
    return True


def isfile(path: Any) -> bool:
    if not os.path.exists(path):
        return False
    if not os.path.isfile(path):
        raise ValueError
    return True


def py(*args: Any) -> subprocess.CompletedProcess[bytes]:
    args: list = [sys.executable, "-m"] + list(args)
    return subprocess.run(args)


def walk(path: Any, *, recursively: Any) -> Generator:
    x: Any
    if not os.path.exists(path):
        return (x for x in ())
    if not recursively:
        ans = os.listdir(path)
        ans = (os.path.join(path, n) for n in ans)
        ans = filter(os.path.isfile, ans)
        for x in ans:
            yield x
        return
    for root, dnames, fnames in os.walk(path):
        for fname in fnames:
            yield os.path.join(root, fname)


def _get_some_version(pkg: Any, /) -> Any:
    return _get_local_version(pkg) or _get_latest_version(pkg)


def _get_local_version(pkg: Any, /) -> Any:
    try:
        ans = importlib.metadata.version(pkg)
    except:
        return None
    url: str = "https://pypi.org/pypi/%s/%s" % (pkg, ans)
    r = requests.get(url)
    if r.status_code == 404:
        return None
    return ans


def _get_latest_version(pkg: Any, /) -> Any:
    url: str = "https://pypi.org/pypi/%s/json" % pkg
    try:
        r = requests.get(url)
        return r.json()["info"]["version"]
    except:
        return None
