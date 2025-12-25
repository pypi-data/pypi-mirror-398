# This file is placed in the Public Domain.


import threading
import time


from genocide.defines import elapsed


STARTTIME = time.time()


def thr(event):
    result = []
    for thread in sorted(threading.enumerate(), key=lambda x: x.name):
        if str(thread).startswith("<_"):
            continue
        if getattr(thread, "state", None) and getattr(thread, "sleep", None):
            uptime = thread.sleep - int(time.time() - thread.state["latest"])
        elif getattr(thread, "starttime", None):
            uptime = time.time() - thread.starttime
        else:
            uptime = time.time() - STARTTIME
        result.append((uptime, thread.name))
    res = []
    for uptime, txt in sorted(result, key=lambda x: x[0]):
        lap = elapsed(uptime)
        res.append(f"{txt}/{lap}")
    if res:
        event.reply(" ".join(res))
    else:
        event.reply("no threads")
