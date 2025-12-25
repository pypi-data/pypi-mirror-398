# This file is placed in the Public Domain.


import logging
import random
import time


from genocide.defines import NoDate, Object, Timed
from genocide.defines import extract, hour, items, today, write
from genocide.defines import broker, elapsed, day, getpath, last, like


rand = random.SystemRandom()


def init():
    Timers.path = last(Timers.timers) or getpath(Timers.timers)
    remove = []
    for tme, args in items(Timers.timers):
        if not args:
            continue
        orig, channel, txt = args
        for origin in like(orig):
            if not origin:
                continue
            diff = float(tme) - time.time()
            if diff > 0:
                bot = broker(origin)
                timer = Timed(diff, bot.say, channel, txt)
                timer.start()
            else:
                remove.append(tme)
    for tme in remove:
        Timers.delete(tme)
    if Timers.timers:
        write(Timers.timers, Timers.path)
    logging.warning("%s timers", len(Timers.timers))


class Timer(Object):

    pass


class Timers(Object):

    path = ""
    timers = Timer()

    @staticmethod
    def add(tme, orig, channel,  txt):
        setattr(Timers.timers, str(tme), (orig, channel, txt))

    @staticmethod
    def delete(tme):
         delattr(Timers.timers, str(tme))


def tmr(event):
    result = ""
    if not event.rest:
        nmr = 0
        for tme, txt in items(Timers.timers):
            lap = float(tme) - time.time()
            if lap > 0:
                event.reply(f'{nmr} {" ".join(txt)} {elapsed(lap)}')
                nmr += 1
        if not nmr:
            event.reply("no timers.")
        return result
    seconds = 0
    line = ""
    for word in event.args:
        if word.startswith("+"):
            try:
                seconds = int(word[1:])
            except (ValueError, IndexError):
                event.reply(f"{seconds} is not an integer")
                return result
        else:
            line += word + " "
    if seconds:
        target = time.time() + seconds
    else:
        try:
            target = day(event.rest)
        except NoDate:
            target = extract(today())
        hours =  hour(event.rest)
        if hours:
            target += hours
    target += rand.random() 
    if not target or time.time() > target:
        event.reply("already passed given time.")
        return result
    diff = target - time.time()
    txt = " ".join(event.args[1:])
    Timers.add(target, event.orig, event.channel, txt)
    write(Timers.timers, Timers.path or getpath(Timers.timers))
    bot = broker(event.orig)
    timer = Timed(diff, bot.say, event.orig, event.channel, txt)
    timer.start()
    event.reply("ok " + elapsed(diff))
