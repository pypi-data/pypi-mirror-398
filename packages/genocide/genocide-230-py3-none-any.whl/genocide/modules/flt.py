# This file is placed in the Public Domain.


from genocide.defines import fmt, name, objs


def flt(event):
    clts = objs("announce")
    if event.args:
        index = int(event.args[0])
        if index < len(clts):
            event.reply(fmt(list(clts)[index]), empty=True)
        else:
            event.reply(f"only {len(clts)} clients in fleet.")
        return
    event.reply(' | '.join([name(o) for o in clts]))
