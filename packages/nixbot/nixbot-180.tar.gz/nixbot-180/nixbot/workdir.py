# This file is placed in the Public Domain.


"where objects are stored."


import os
import pathlib


from .utility import ident


class Workdir:

    wdr = ""


def getpath(obj):
    "return path for object."
    return storage(ident(obj))


def long(name):
    "match full qualified name by substring."
    split = name.split(".")[-1].lower()
    res = name
    for names in kinds():
        if split == names.split(".")[-1].lower():
            res = names
            break
    return res


def moddir(modname: str = ""):
    "return modules string."
    return os.path.join(Workdir.wdr, modname or "mods")


def pidname(name: str):
    "return name of pidfile."
    return os.path.join(Workdir.wdr, f"{name}.pid")


def skel():
    "create directories."
    path = storage()
    pth = pathlib.Path(path)
    pth.mkdir(parents=True, exist_ok=True)
    pth = pathlib.Path(moddir())
    pth.mkdir(parents=True, exist_ok=True)


def storage(fnm: str = ""):
    "return path to store."
    return os.path.join(Workdir.wdr, "store", fnm)


def kinds():
    "return stored types."
    return os.listdir(storage())


def __dir__():
    return (
        'Workdir',
        'getpath',
        'long',
        'moddir',
        'pidname',
        'skel',
        'storage',
        'types'
    )
