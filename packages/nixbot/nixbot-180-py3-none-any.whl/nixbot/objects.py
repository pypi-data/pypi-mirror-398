# This file is placed in the Public Domain.


"a clean namespace"


import types


class Reserved(Exception):

    pass


class Object:

    def __contains__(self, key):
        return key in dir(self)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


def construct(obj, *args, **kwargs):
    "object contructor."
    if args:
        val = args[0]
        if isinstance(val, zip):
            update(obj, dict(val))
        elif isinstance(val, dict):
            update(obj, val)
        else:
            update(obj, vars(val))
    if kwargs:
        update(obj, kwargs)


def asdict(obj):
    "return object as dictionary."
    res = {}
    for key in dir(obj):
        if key.startswith("_"):
            continue
        res[key] = getattr(obj, key)
    return res


def items(obj):
    "return object's key,valye pairs."
    if isinstance(obj, dict):
        return obj.items()
    if isinstance(obj, types.MappingProxyType):
        return obj.items()
    res = []
    for key in dir(obj):
        if key.startswith("_"):
            continue
        res.append((key, getattr(obj, key)))
    return res


def keys(obj):
    "return object keys."
    if isinstance(obj, dict):
        return obj.keys()
    return obj.__dict__.keys()
    

def update(obj, data, empty=True):
    "update object,"
    if isinstance(obj, type):
        for k, v in items(data):
            if isinstance(getattr(obj, k, None), types.MethodType):
                raise Reserved(k)
            setattr(obj, k, v)
    elif isinstance(obj, dict):
        for k, v in items(data):
            setattr(obj, k, v)
    else:
        for key, value in items(data):
            if not empty and not value:
                continue
            setattr(obj, key, value)

def values(obj):
    "return object's values/"
    if isinstance(obj, dict):
        return obj.values()
    res = []
    for key in dir(obj):
        if key.startswith("_"):
            continue
        res.append(getattr(obj, key))
    return res


class Default(Object):

    def __getattr__(self, key):
        return self.__dict__.get(key, "")


def __dir__():
    return (
        'Default',
        'Object',
        'asdict',
        'construct',
        'items',
        'keys',
        'update',
        'values'
    )
