# This file is placed in the Public Domain.


"only message."


import threading
import time


from .brokers import broker
from .objects import Default


class Message(Default):

    def __init__(self):
        super().__init__()
        self._ready = threading.Event()
        self.result = {}
        self.thr = None
        self.args = []
        self.index = 0
        self.kind = "event"
        self.orig = ""

    def display(self):
        "call display on originating client."
        bot = broker(self.orig)
        bot.display(self)

    def ready(self):
        "flag message as ready."
        self._ready.set()

    def reply(self, text):
        "add text to result."
        self.result[time.time()] = text

    def wait(self, timeout=0.0):
        "wait for completion."
        if self.thr:
            self.thr.join(timeout)
        self._ready.wait(timeout or None)


def __dir__():
    return (
        'Message',
    )
