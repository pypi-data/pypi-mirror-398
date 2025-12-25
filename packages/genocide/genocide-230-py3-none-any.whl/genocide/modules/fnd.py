# This file is placed in the Public Domain.


import time


from genocide.defines import elapsed, find, fmt, fntime, kinds


def fnd(event):
    if not event.rest:
        res = sorted([x.split('.')[-1].lower() for x in kinds()])
        if res:
            event.reply(",".join(res))
        else:
            event.reply("no data yet.")
        return
    otype = event.args[0]
    nmr = 0
    for fnm, obj in sorted(find(otype, event.gets), key=lambda x: fntime(x[0])):
        event.reply(f"{nmr} {fmt(obj)} {elapsed(time.time()-fntime(fnm))}")
        nmr += 1
    if not nmr:
        event.reply("no result")
