# This file is placed in the Public Domain.


"fields"


from genocide.defines import attrs, kinds


def atr(event):
    if not event.rest:
        res = sorted({x.split('.')[-1].lower() for x in kinds()})
        if res:
            event.reply(",".join(res))
        else:
            event.reply("no types")
        return
    itms = attrs(event.args[0])
    if not itms:
        event.reply("no fields")
    else:
        event.reply(",".join(itms))
