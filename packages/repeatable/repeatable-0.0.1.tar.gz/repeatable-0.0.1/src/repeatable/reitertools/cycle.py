import itertools

from ..repeatable import Repeatable


def cycle(iterable):
    '''
    Non-greedy version of `itertools.cycle` that handles an arbitrarily large,
    repeatable iterable without writing it to memory.

    Return elements from the iterable until it is exhausted.
    Then repeat the sequence indefinitely.
    '''

    if not isinstance(iterable, Repeatable):
        yield from itertools.cycle(iterable)
        return

    while True:
        iterator = iterable.__reiter__()

        empty = True

        for x in iterator:
            empty = False
            yield x

        if empty:
            # empty input iterable
            return
