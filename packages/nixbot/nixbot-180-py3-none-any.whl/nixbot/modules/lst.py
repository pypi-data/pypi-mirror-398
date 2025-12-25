# This file is been placed in the Public Domain.


from nixbot.defines import kinds


def lst(event):
    tps = kinds()
    if tps:
        event.reply(",".join({x.split(".")[-1].lower() for x in tps}))
    else:
        event.reply("no data yet.")
