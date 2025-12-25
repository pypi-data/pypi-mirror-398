# This file is placed in the Public Domain.


"write your own commands."


import inspect


from .methods import parse
from .utility import spl


class Commands:

    cmds = {}
    names = {}


def cmds(cmd):
    "return command."
    return Commands.cmds.get(cmd, None)


def command(evt):
    "command callback."
    parse(evt, evt.text)
    func = cmds(evt.cmd)
    if func:
        func(evt)
        evt.display()
    evt.ready()


def enable(*args):
    "add functions to commands."
    for func in args:
        name = func.__name__
        Commands.cmds[name] = func
        Commands.names[name] = func.__module__.split(".")[-1]


def scan(module):
    "scan a module for command, function with event as first argument."
    for key, cmdz in inspect.getmembers(module, inspect.isfunction):
        if 'event' not in inspect.signature(cmdz).parameters:
            continue
        enable(cmdz)


def scanner(pkg, names=None):
    "scan package for commands."
    if names is None:
        names = ",".join(dir(pkg))
    mods = []
    for name in spl(names):
        module = getattr(pkg, name, None)
        if not module:
            continue
        scan(module)
    return mods


def __dir__():
    return (
        'Commands',
        'cmds',
        'command',
        'enable',
        'scan'
    )
