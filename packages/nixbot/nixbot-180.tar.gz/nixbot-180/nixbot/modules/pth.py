# This file is placed in the Public Domain.


import os


from nixbot.defines import Config, where


def pth(event):
    fn = where(Config)
    path = os.path.join(fn, 'network', 'html', "index.html")
    event.reply(f"file://{path}")
