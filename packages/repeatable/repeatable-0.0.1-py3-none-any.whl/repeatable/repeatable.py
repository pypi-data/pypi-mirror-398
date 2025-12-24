import collections.abc
from functools import partial, wraps


class Repeatable(collections.abc.Iterator, collections.abc.Iterable):
    '''
    Repeatable class definition

    A Repeatable (or "Reiterable") is a generator-like object that implements
    `__reiter__` and `restart` methods to allow multiple iteration passes.
    It takes in a generator function at created time and caches it, calling
    the generator function each time it needs to reiterate through its values.

    Take care when passing arbitraty generator functions to this class, as side
    effects may be triggered multiple times.
    '''

    def __init__(self, generator_func):
        self.__gen_func = generator_func
        self.__gen_factory = None
        self.__gen = None

    def __call__(self, *args, **kwargs):
        self.__gen_factory = partial(self.__gen_func, *args, **kwargs)
        self.__gen = self.__gen_factory()

        return self

    def __iter__(self):
        resp = self.__gen.__iter__()
        return resp

    def __reiter__(self):
        self.restart()

        return self.__iter__()

    def __next__(self):
        return self.__gen.__next__()

    def restart(self):
        self.__gen = self.__gen_factory()

    def send(self, *args, **kwargs):
        return self.__gen.send(*args, **kwargs)

    def throw(self, *args, **kwargs):
        return self.__gen.throw(*args, **kwargs)

    def close(self, *args, **kwargs):
        return self.__gen.close(*args, **kwargs)


def repeatable(generator_func):
    '''
    Decorator that turns a generator function into a function that returns a
    `Repeatable` iterable.
    '''

    @wraps(generator_func)
    def wrapper(*args, **kwargs):
        return Repeatable(generator_func)(*args, **kwargs)

    return wrapper
