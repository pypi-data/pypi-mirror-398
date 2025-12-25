# This file is placed in the Public Domain.


import base64
import logging
import os
import socket
import ssl
import textwrap
import threading
import time


from genocide.defines import Config as Main
from genocide.defines import Message, Object, Output
from genocide.defines import broker, command, edit, fmt, getpath, last, launch
from genocide.defines import keys, write
 
 
lock = threading.RLock()


def init():
    irc = IRC()
    irc.start()
    irc.events.joined.wait(30.0)
    if irc.events.joined.is_set():
        logging.warning("%s", fmt(irc.cfg, skip=["name", "word", "realname", "username"]))
    else:
        irc.stop()
    return irc


class Config(Object):

    channel = f"#{Main.name}"
    commands = True
    control = "!"
    ignore = ["PING", "PONG", "PRIVMSG"] 
    name = Main.name
    nick = Main.name
    word = ""
    port = 6667
    realname = Main.name
    sasl = False
    server = "localhost"
    servermodes = ""
    sleep = 60
    username = Main.name
    users = False
    version = 1

    def __init__(self):
        super().__init__()
        self.channel = Config.channel
        self.commands = Config.commands
        self.name = Config.name
        self.nick = Config.nick
        self.port = Config.port
        self.realname = Config.realname
        self.server = Config.server
        self.username = Config.username

    def __getattr__(self, name):
        if name not in self:
            return ""
        return self.__getattribute__(name)


class Event(Message):

    def __init__(self):
        super().__init__()
        self.args = []
        self.arguments = []
        self.command = ""
        self.channel = ""
        self.gets = {}
        self.nick = ""
        self.origin = ""
        self.rawstr = ""
        self.rest = ""
        self.sets = {}
        self.text = ""

    def dosay(self, txt):
        bot = broker(self.orig)
        bot.dosay(self.channel, txt)


class TextWrap(textwrap.TextWrapper):

    def __init__(self):
        super().__init__()
        self.break_long_words = False
        self.drop_whitespace = False
        self.fix_sentence_endings = True
        self.replace_whitespace = True
        self.tabsize = 4
        self.width = 400


wrapper = TextWrap()


class IRC(Output):

    def __init__(self):
        Output.__init__(self)
        self.buffer = []
        self.cache = {}
        self.cfg = Config()
        self.channels = []
        self.events = Object()
        self.events.authed = threading.Event()
        self.events.connected = threading.Event()
        self.events.joined = threading.Event()
        self.events.logon = threading.Event()
        self.events.ready = threading.Event()
        self.silent = False
        self.sock = None
        self.state = Object()
        self.state.error = ""
        self.state.keeprunning = False
        self.state.last = time.time()
        self.state.lastline = ""
        self.state.nrconnect = 0
        self.state.nrerror = 0
        self.state.nrsend = 0
        self.state.pongcheck = False
        self.state.sleep = self.cfg.sleep
        self.state.stopkeep = False
        self.zelf = ""
        self.register("903", cb_h903)
        self.register("904", cb_h903)
        self.register("AUTHENTICATE", cb_auth)
        self.register("CAP", cb_cap)
        self.register("ERROR", cb_error)
        self.register("LOG", cb_log)
        self.register("NOTICE", cb_notice)
        self.register("PRIVMSG", cb_privmsg)
        self.register("QUIT", cb_quit)
        self.register("366", cb_ready)

    def announce(self, text):
        for channel in self.channels:
            self.say(channel, text)

    def connect(self, server, port=6667):
        self.state.nrconnect += 1
        self.events.connected.clear()
        self.events.joined.clear()
        if self.cfg.word or self.cfg.password:
            logging.debug("using SASL")
            self.cfg.sasl = True
            self.cfg.port = "6697"
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
            ctx.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = ctx.wrap_socket(sock)
            self.sock.connect((server, port))
            self.direct("CAP LS 302")
        else:
            addr = socket.getaddrinfo(server, port, socket.AF_INET)[-1][-1]
            addr = tuple(addr[:2])
            self.sock = socket.create_connection(addr)
            self.events.authed.set()
        if self.sock:
            os.set_inheritable(self.sock.fileno(), True)
            self.sock.setblocking(True)
            self.sock.settimeout(180.0)
            self.events.connected.set()
            logging.debug("connected %s:%s channel %s", self.cfg.server, self.cfg.port, self.cfg.channel)
            return True
        return False

    def direct(self, txt):
        with lock:
            time.sleep(2.0)
            self.raw(txt)

    def disconnect(self):
        try:
            self.sock.shutdown(2)
        except (ssl.SSLError, OSError, BrokenPipeError) as _ex:
            pass

    def display(self, event):
        for key in sorted(event.result):
            txt = event.result.get(key)
            if not txt:
                continue
            textlist = []
            txtlist = wrapper.wrap(txt)
            if len(txtlist) > 3:
                self.extend(event.channel, txtlist[3:])
                textlist = txtlist[:3]
            else:
                textlist = txtlist
            _nr = -1
            for text in textlist:
                _nr += 1
                self.dosay(event.channel, text)
            if len(txtlist) > 3:
                length = len(txtlist) - 3
                self.say(event.channel, f"use !mre to show more (+{length})")

    def docommand(self, cmd, *args):
        with lock:
            if not args:
                self.raw(cmd)
            elif len(args) == 1:
                self.raw(f"{cmd.upper()} {args[0]}")
            elif len(args) == 2:
                txt = " ".join(args[1:])
                self.raw(f"{cmd.upper()} {args[0]} :{txt}")
            elif len(args) >= 3:
                txt = " ".join(args[2:])
                self.raw("{cmd.upper()} {args[0]} {args[1]} :{txt}")
            if (time.time() - self.state.last) < 5.0:
                time.sleep(5.0)
            self.state.last = time.time()

    def doconnect(self, server, nck, port=6667):
        while 1:
            try:
                if self.connect(server, port):
                    self.logon(self.cfg.server, self.cfg.nick)
                    self.events.joined.wait(15.0)
                    if not self.events.joined.is_set():
                        self.disconnect()
                        self.events.joined.set()
                        continue
                    break
            except (socket.timeout, ssl.SSLError, OSError, ConnectionResetError) as ex:
                self.events.joined.set()
                self.state.error = str(ex)
                logging.debug("%s", str(type(ex)) + " " + str(ex))
            time.sleep(self.cfg.sleep)

    def dosay(self, channel, text):
        self.events.joined.wait()
        txt = str(text).replace("\n", "")
        txt = txt.replace("  ", " ")
        self.docommand("PRIVMSG", channel, txt)

    def event(self, txt):
        evt = self.parsing(txt)
        cmd = evt.command
        if cmd == "PING":
            self.state.pongcheck = True
            self.docommand("PONG", evt.text or "")
        elif cmd == "PONG":
            self.state.pongcheck = False
        if cmd == "001":
            self.state.needconnect = False
            if self.cfg.servermodes:
                self.docommand(f"MODE {self.cfg.nick} {self.cfg.servermodes}")
            self.zelf = evt.args[-1]
        elif cmd == "376":
            self.joinall()
        elif cmd == "002":
            self.state.host = evt.args[2][:-1]
        elif cmd == "366":
            self.state.error = ""
            self.events.joined.set()
        elif cmd == "433":
            self.state.error = txt
            nck = self.cfg.nick = self.cfg.nick + "_"
            self.docommand("NICK", nck)
        return evt

    def extend(self, channel, txtlist):
        if channel not in self.cache:
            self.cache[channel] = []
        chanlist = self.cache.get(channel)
        chanlist.extend(txtlist)

    def gettxt(self, channel):
        txt = None
        try:
            che = self.cache.get(channel, None)
            if che:
                txt = che.pop(0)
        except (KeyError, IndexError):
            pass
        return txt

    def joinall(self):
        for channel in self.channels:
            self.docommand("JOIN", channel)

    def keep(self):
        while True:
            if self.state.stopkeep:
                self.state.stopkeep = False
                break
            self.events.connected.wait()
            self.events.authed.wait()
            self.state.keeprunning = True
            self.state.latest = time.time()
            time.sleep(self.cfg.sleep)
            self.docommand("PING", self.cfg.server)
            if self.state.pongcheck:
                self.restart()

    def logon(self, server, nck):
        self.events.connected.wait()
        self.events.authed.wait()
        self.direct(f"NICK {nck}")
        self.direct(f"USER {nck} {server} {server} {nck}")

    def oput(self, event):
        if event.channel and event.channel not in self.cache:
            self.cache[event.channel] = []
        self.oqueue.put_nowait(event)

    def parsing(self, txt):
        rawstr = str(txt)
        rawstr = rawstr.replace("\u0001", "")
        rawstr = rawstr.replace("\001", "")
        rlog(txt)
        obj = Event()
        obj.args = []
        obj.rawstr = rawstr
        obj.command = ""
        obj.arguments = []
        arguments = rawstr.split()
        if arguments:
            obj.origin = arguments[0]
        else:
            obj.origin = self.cfg.server
        if obj.origin.startswith(":"):
            obj.origin = obj.origin[1:]
            if len(arguments) > 1:
                obj.command = arguments[1]
                obj.kind = obj.command
            if len(arguments) > 2:
                txtlist = []
                adding = False
                for arg in arguments[2:]:
                    if arg.count(":") <= 1 and arg.startswith(":"):
                        adding = True
                        txtlist.append(arg[1:])
                        continue
                    if adding:
                        txtlist.append(arg)
                    else:
                        obj.arguments.append(arg)
                obj.text = " ".join(txtlist)
        else:
            obj.command = obj.origin
            obj.origin = self.cfg.server
        try:
            obj.nick, obj.origin = obj.origin.split("!")
        except ValueError:
            obj.nick = ""
        target = ""
        if obj.arguments:
            target = obj.arguments[0]
        if target.startswith("#"):
            obj.channel = target
        else:
            obj.channel = obj.nick
        if not obj.text:
            obj.text = rawstr.split(":", 2)[-1]
        if not obj.text and len(arguments) == 1:
            obj.text = arguments[1]
        splitted = obj.text.split()
        if len(splitted) > 1:
            obj.args = splitted[1:]
        if obj.args:
            obj.rest = " ".join(obj.args)
        obj.orig = object.__repr__(self)
        obj.text = obj.text.strip()
        obj.kind = obj.command
        return obj

    def poll(self):
        self.events.connected.wait()
        if not self.buffer:
            try:
                self.some()
            except BlockingIOError as ex:
                time.sleep(1.0)
                return self.event(str(ex))
            except (
                OSError,
                socket.timeout,
                ssl.SSLError,
                ssl.SSLZeroReturnError,
                ConnectionResetError,
                BrokenPipeError,
            ) as ex:
                self.state.nrerror += 1
                self.state.error = str(type(ex)) + " " + str(ex)
                logging.debug(self.state.error)
                self.state.pongcheck = True
                self.stop()
                return None
        try:
            txt = self.buffer.pop(0)
        except IndexError:
            txt = ""
        return self.event(txt)

    def raw(self, text):
        text = text.rstrip()
        rlog(text)
        text = text[:500]
        text += "\r\n"
        text = bytes(text, "utf-8")
        if self.sock:
            try:
                self.sock.send(text)
            except (
                OSError,
                ssl.SSLError,
                ssl.SSLZeroReturnError,
                ConnectionResetError,
                BrokenPipeError,
                socket.timeout,
            ) as ex:
                logging.debug("%s", str(type(ex)) + " " + str(ex))
                self.events.joined.set()
                self.state.nrerror += 1
                self.state.error = str(ex)
                self.state.pongcheck = True
                self.stop()
                return
        self.state.last = time.time()
        self.state.nrsend += 1

    def reconnect(self):
        logging.debug("reconnecting %s:%s", self.cfg.server, self.cfg.port)
        self.disconnect()
        self.events.connected.clear()
        self.events.joined.clear()
        self.doconnect(self.cfg.server, self.cfg.nick, int(self.cfg.port))

    def restart(self):
        self.events.joined.set()
        self.state.pongcheck = False
        self.state.keeprunning = False
        self.state.stopkeep = True
        self.stop()
        launch(init)

    def size(self, chan):
        if chan in self.cache:
            return len(self.cache.get(chan, []))
        return 0

    def say(self, channel, text):
        event = Event()
        event.channel = channel
        event.reply(text)
        self.oput(event)

    def some(self):
        self.events.connected.wait()
        if not self.sock:
            return
        inbytes = self.sock.recv(512)
        text = str(inbytes, "utf-8")
        if text == "":
            raise ConnectionResetError
        self.state.lastline += text
        splitted = self.state.lastline.split("\r\n")
        for line in splitted[:-1]:
            self.buffer.append(line)
        self.state.lastline = splitted[-1]

    def start(self):
        last(self.cfg)
        if self.cfg.channel not in self.channels:
            self.channels.append(self.cfg.channel)
        self.events.ready.clear()
        self.events.connected.clear()
        self.events.joined.clear()
        Output.start(self)
        if not self.state.keeprunning:
            launch(self.keep)
        launch(
            self.doconnect,
            self.cfg.server or "localhost",
            self.cfg.nick,
            int(self.cfg.port) or 6667,
        )

    def stop(self):
        self.state.stopkeep = True
        Output.stop(self)

    def wait(self):
        self.events.ready.wait()


"callbacks"


def cb_auth(evt):
    bot = broker(evt.orig)
    bot.docommand(f"AUTHENTICATE {bot.cfg.word or bot.cfg.password}")


def cb_cap(evt):
    bot = broker(evt.orig)
    if (bot.cfg.word or bot.cfg.password) and "ACK" in evt.arguments:
        bot.direct("AUTHENTICATE PLAIN")
    else:
        bot.direct("CAP REQ :sasl")


def cb_error(evt):
    bot = broker(evt.orig)
    bot.state.nrerror += 1
    bot.state.error = evt.text
    logging.debug(fmt(evt))


def cb_h903(evt):
    bot = broker(evt.orig)
    bot.direct("CAP END")
    bot.events.authed.set()


def cb_h904(evt):
    bot = broker(evt.orig)
    bot.direct("CAP END")
    bot.events.authed.set()


def cb_kill(evt):
    pass


def cb_log(evt):
    pass


def cb_ready(evt):
    bot = broker(evt.orig)
    bot.events.ready.set()


def cb_001(evt):
    bot = broker(evt.orig)
    bot.events.logon.set()


def cb_notice(evt):
    bot = broker(evt.orig)
    if evt.text.startswith("VERSION"):
        txt = f"\001VERSION {Config.name.upper()} {Config.version} - {bot.cfg.username}\001"
        bot.docommand("NOTICE", evt.channel, txt)


def cb_privmsg(evt):
    bot = broker(evt.orig)
    if not bot.cfg.commands:
        return
    if evt.text:
        if evt.text[0] in [
            "!",
        ]:
            evt.text = evt.text[1:]
        elif evt.text.startswith(f"{bot.cfg.nick}:"):
            evt.text = evt.text[len(bot.cfg.nick) + 1 :]
        else:
            return
        if evt.text:
            evt.text = evt.text[0].lower() + evt.text[1:]
        if evt.text:
            launch(command, evt)


def cb_quit(evt):
    bot = broker(evt.orig)
    logging.debug("quit from %s", bot.cfg.server)
    bot.state.nrerror += 1
    bot.state.error = evt.text
    if evt.orig and evt.orig in bot.zelf:
        bot.stop()


"commands"


def cfg(event):
    config = Config()
    fnm = last(config)
    if not event.sets:
        event.reply(
            fmt(
                config,
                keys(config),
                skip="control,name,word,realname,sleep,username".split(",")
            )
        )
    else:
        edit(config, event.sets)
        write(config, fnm or getpath(config))
        event.reply("ok")


def mre(event):
    if not event.channel:
        event.reply("channel is not set.")
        return
    bot = broker(event.orig)
    if "cache" not in dir(bot):
        event.reply("bot is missing cache")
        return
    if event.channel not in bot.cache:
        event.reply(f"no output in {event.channel} cache.")
        return
    for _x in range(3):
        txt = bot.gettxt(event.channel)
        event.reply(txt)
    size = bot.size(event.channel)
    if size != 0:
        event.reply(f"{size} more in cache")


def pwd(event):
    if len(event.args) != 2:
        event.reply("pwd <nick> <password>")
        return
    arg1 = event.args[0]
    arg2 = event.args[1]
    txt = f"\x00{arg1}\x00{arg2}"
    enc = txt.encode("ascii")
    base = base64.b64encode(enc)
    dcd = base.decode("ascii")
    event.reply(dcd)


"utility"


def rlog(txt):
    for ign in Config.ignore:
        if ign in str(txt):
            return
    logging.debug(txt)
