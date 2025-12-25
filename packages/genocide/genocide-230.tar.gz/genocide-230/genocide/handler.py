# This file is placed in the Public Domain.


"handle your own events"


import queue


from .threads import launch


class Handler:

    def __init__(self):
        self.cbs = {}
        self.queue = queue.Queue()

    def callback(self, event):
        "run callback function with event."
        func = self.cbs.get(event.kind, None)
        if not func:
            event.ready()
            return
        name = event.text and event.text.split()[0]
        event._thr = launch(func, event, name=name)

    def loop(self):
        "event loop."
        while True:
            event = self.poll()
            if not event:
                break
            event.orig = repr(self)
            self.callback(event)

    def poll(self):
        "return an event to process."
        return self.queue.get()

    def put(self, event):
        "put event on queue."
        self.queue.put(event)

    def register(self, kind, callback):
        "register callback."
        self.cbs[kind] = callback

    def start(self):
        "start event handler loop."
        launch(self.loop)

    def stop(self):
        "stop event handler loop."
        self.queue.put(None)


def __dir__():
    return (
        'CLI',
        'Client',
        'Output'
    )
