# This file is placed in the Public Domain.


"functions with an object as the first argument"


from .objects import Default, items


def deleted(obj):
    "check whether obj had deleted flag set."
    return "__deleted__" in dir(obj) and obj.__deleted__


def edit(obj, setter={}, skip=False):
    "update object with dict."
    for key, val in items(setter):
        if skip and val == "":
            continue
        try:
            setattr(obj, key, int(val))
            continue
        except ValueError:
            pass
        try:
            setattr(obj, key, float(val))
            continue
        except ValueError:
            pass
        if val in ["True", "true"]:
            setattr(obj, key, True)
        elif val in ["False", "false"]:
            setattr(obj, key, False)
        else:
            setattr(obj, key, val)


def fmt(obj, args=[], skip=[], plain=False, empty=False):
    "format object info printable string."
    if args == []:
        args = list(obj.__dict__.keys())
    txt = ""
    for key in args:
        if key.startswith("__"):
            continue
        if key in skip:
            continue
        value = getattr(obj, key, None)
        if value is None:
            continue
        if not empty and not value:
            continue
        if plain:
            txt += f"{value} "
        elif isinstance(value, str):
            txt += f'{key}="{value}" '
        elif isinstance(value, (int, float, dict, bool, list)):
            txt += f"{key}={value} "
        else:
            txt += f"{key}={fqn(value)}((value))"
    if txt == "":
        txt = "{}"
    return txt.strip()


def fqn(obj):
    "full qualified name."
    kin = str(type(obj)).split()[-1][1:-2]
    if kin == "type":
        tpe = type(obj)
        kin = f"{tpe.__module__}.{tpe.__name__}"
    return kin


def parse(obj, text):
    "parse text for command."
    data = {
        "args": [],
        "cmd": "",
        "gets": Default(),
        "index": None,
        "init": "",
        "opts": "",
        "otxt": text,
        "rest": "",
        "silent": Default(),
        "sets": Default(),
        "text": text
    }
    for k, v in data.items():
        setattr(obj, k, getattr(obj, k, v) or v)
    args = []
    nr = -1
    for spli in text.split():
        if spli.startswith("-"):
            try:
                obj.index = int(spli[1:])
            except ValueError:
                obj.opts += spli[1:]
            continue
        if "-=" in spli:
            key, value = spli.split("-=", maxsplit=1)
            setattr(obj.silent, key, value)
            setattr(obj.gets, key. value)
            continue
        if "==" in spli:
            key, value = spli.split("==", maxsplit=1)
            setattr(obj.gets, key, value)
            continue
        if "=" in spli:
            key, value = spli.split("=", maxsplit=1)
            setattr(obj.sets, key, value)
            continue
        nr += 1
        if nr == 0:
            obj.cmd = spli
            continue
        args.append(spli)
    if args:
        obj.args = args
        obj.text  = obj.cmd or ""
        obj.rest = " ".join(obj.args)
        obj.text  = obj.cmd + " " + obj.rest
    else:
        obj.text = obj.cmd or ""


def search(obj, selector={}, matching=False):
    "check whether object matches search criteria."
    res = False
    for key, value in items(selector):
        val = getattr(obj, key, None)
        if not val:
            res = False
            break
        if matching and value != val:
            res = False
            break
        if str(value).lower() not in str(val).lower():
            res = False
            break
        res = True
    return res


def __dir__():
    return (
        'deleted',
        'edit',
        'fmt',
        'fqn',
        'parse',
        'search'
    )
