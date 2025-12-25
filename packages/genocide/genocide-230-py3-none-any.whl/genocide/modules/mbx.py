# This file is placed in the Public Domain.


import mailbox
import os
import time


from genocide.defines import MONTH, Object, date, elapsed, find, keys, update
from genocide.defines import fmt, write


class Email(Object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = ""


def todate(date):
    date = date.replace("_", ":")
    res = date.split()
    ddd = ""
    try:
        if "+" in res[3]:
            raise ValueError
        if "-" in res[3]:
            raise ValueError
        int(res[3])
        ddd = "{:4}-{:#02}-{:#02} {:6}".format(res[3], MONTH[res[2]], int(res[1]), res[4])
    except (IndexError, KeyError, ValueError) as ex:
        try:
            if "+" in res[4]:
                raise ValueError from ex
            if "-" in res[4]:
                raise ValueError from ex
            int(res[4])
            ddd = "{:4}-{:#02}-{:02} {:6}".format(res[4], MONTH[res[1]], int(res[2]), res[3])
        except (IndexError, KeyError, ValueError):
            try:
                ddd = "{:4}-{:#02}-{:02} {:6}".format(res[2], MONTH[res[1]], int(res[0]), res[3])
            except (IndexError, KeyError):
                try:
                    ddd = "{:4}-{:#02}-{:02}".format(res[2], MONTH[res[1]], int(res[0]))
                except (IndexError, KeyError):
                    try:
                        ddd = "{:4}-{:#02}".format(res[2], MONTH[res[1]])
                    except (IndexError, KeyError):
                        try:
                            ddd = "{:4}".format(res[2])
                        except (IndexError, KeyError):
                            ddd = ""
    return ddd


def eml(event):
    nrs = -1
    args = ["From", "Subject"]
    if len(event.args) > 1:
        args.extend(event.args[1:])
    if event.gets:
        args.extend(keys(event.gets))
    for key in event.silent:
        if key in args:
            args.remove(key)
    args = set(args)
    result = sorted(
                    find("email", event.gets),
                    key=lambda x: date(todate(getattr(x[1], "Date", "")))
                   )
    if event.index:
        obj = result[event.index]
        if obj:
            obj = obj[-1]
            tme = getattr(obj, "Date", "")
            event.reply(f'{event.index} {fmt(obj, args, plain=True)} {elapsed(time.time() - date(todate(tme)))}')
    else:
        for _fn, obj in result:
            nrs += 1
            tme = getattr(obj, "Date", "")
            event.reply(f'{nrs} {fmt(obj, args, plain=True)} {elapsed(time.time() - date(todate(tme)))}')
    if not result:
        event.reply("no emails found.")


def mbx(event):
    if not event.args:
        event.reply("mbx <path>")
        return
    fnm = os.path.expanduser(event.args[0])
    event.reply("reading from %s" % fnm)
    if os.path.isdir(fnm):
        thing = mailbox.Maildir(fnm, create=False)
    elif os.path.isfile(fnm):
        thing = mailbox.mbox(fnm, create=False)
    else:
        return
    try:
        thing.lock()
    except FileNotFoundError:
        pass
    nrs = 0
    for mail in thing:
        obj = Email()
        update(obj, dict(mail._headers))
        obj.text = ""
        for payload in mail.walk():
            if payload.get_content_type() == 'text/plain':
                obj.text += payload.get_payload()
        obj.text = obj.text.replace("\\n", "\n")
        write(obj)
        nrs += 1
    if nrs:
        event.reply("ok %s" % nrs)
