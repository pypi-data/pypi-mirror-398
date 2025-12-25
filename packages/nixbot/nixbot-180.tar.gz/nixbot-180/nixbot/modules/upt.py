# This file is placed in the Public Domain.


import time


from nixbot.defines import elapsed


STARTTIME = time.time()


def upt(event):
    event.reply(elapsed(time.time()-STARTTIME))
