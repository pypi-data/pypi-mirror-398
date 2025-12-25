# This file is placed in the Public Domain.


"things are repeating."


import threading
import time


from .threads import launch, name


class Timy(threading.Timer):

    def __init__(self, sleep, func, *args, **kwargs):
        super().__init__(sleep, func)
        self.name = kwargs.get("name", name(func))
        self.sleep = sleep
        self.state = {}
        self.state["latest"] = time.time()
        self.state["starttime"] = time.time()
        self.starttime = time.time()


class Timed:

    def __init__(self, sleep, func, *args, thrname="", **kwargs):
        self.args = args
        self.func = func
        self.kwargs = kwargs
        self.sleep = sleep
        self.name = thrname or kwargs.get("name", name(func))
        self.target = time.time() + self.sleep
        self.timer = None

    def run(self):
        "run timed function."
        self.timer.latest = time.time()
        self.func(*self.args)

    def start(self):
        "start timer."
        self.kwargs["name"] = self.name
        timer = Timy(self.sleep, self.run, *self.args, **self.kwargs)
        timer.start()
        self.timer = timer

    def stop(self):
        "stop timer."
        if self.timer:
            self.timer.cancel()


class Repeater(Timed):

    def run(self):
        "run function and launch timer for next run."
        launch(self.start)
        super().run()


def __dir__():
    return (
        'Repeater',
        'Timed',
    )
