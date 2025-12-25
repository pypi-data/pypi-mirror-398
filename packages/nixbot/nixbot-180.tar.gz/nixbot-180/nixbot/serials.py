# This file is placed in the Public Domain.


"realisation of serialisation"


import json
import types


class Encoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, dict):
            return o.items()
        if isinstance(o, list):
            return iter(o)
        if isinstance(o, types.MappingProxyType):
            return dict(o)
        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            try:
                return vars(o)
            except TypeError:
                return repr(o)


def dump(*args, **kw):
    "dump object to disk."
    kw["cls"] = Encoder
    return json.dump(*args, **kw)


def dumps(*args, **kw):
    "dump object to string."
    kw["cls"] = Encoder
    return json.dumps(*args, **kw)


def load(s, *args, **kw):
    "load object from disk."
    return json.load(s, *args, **kw)


def loads(s, *args, **kw):
    "load object from string."
    return json.loads(s, *args, **kw)


def __dir__():
    return (
       'dump',
       'dumps',
       'load',
       'loads'
    )
