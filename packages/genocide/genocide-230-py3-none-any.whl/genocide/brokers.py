# This file is placed in the Public Domain.


"an object for a string."


class Broker:

    objects = {}


def add(obj):
    "add object to the broker, key is repr(obj)."
    Broker.objects[repr(obj)] = obj


def broker(origin):
    "return object by repr(obj)."
    return Broker.objects.get(origin)


def objs(attr):
    "return object with a certain attribute."
    for obj in Broker.objects.values():
        if attr in dir(obj):
            yield obj


def like(txt):
    "return all objects that have a substring in their key."
    for orig in Broker.objects:
        if orig.split()[0] in orig.split()[0]:
            yield orig


def __dir__():
    return (
        'add',
        'broker',
        'like',
        'objs'
    )
