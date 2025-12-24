import itertools

from ..repeatable import Repeatable


def combinations(iterable, r):
    '''
    Non-greedy version of `itertools.combinations` that handles an arbitrarily
    large, repeatable iterable without writing it to memory.

    Return successive r-length combinations of elements in the iterable.

    combinations(range(4), 3) --> (0,1,2), (0,1,3), (0,2,3), (1,2,3)
    '''

    if not isinstance(iterable, Repeatable):
        yield from itertools.combinations(iterable, r)
        return

    iterators = [iterable.__reiter__() for _ in range(r)]

    try:
        # create a pool of iterators
        current = [next(it) for it in iterators]
    except StopIteration:
        # the iterable is empty: yield no responses
        return

    # maintain the indices of the current elements' positions in the iterable:
    # used to "fast-forward" a restarted iterator to the correct state
    indices = [0] * r

    try:
        # try to create first output
        for i in range(r):
            # fast forward `iterators[i]` to position `i`
            for _ in range(i):
                current[i] = next(iterators[i])
                indices[i] += 1

        yield tuple(current)

    except StopIteration:
        # `r` is too large for the size of the iterator
        return

    # set up a pointer to the iterator currently being stepped through
    ptr = r - 1

    while ptr >= 0:
        try:
            # step once through the active iterator (should never throw)
            current[ptr] = next(iterators[ptr])
            indices[ptr] += 1

            # fast forward all subsequent iterators ahead of their previous,
            # ensuring that `current` is sorted according to the input order
            for i in range(ptr + 1, r):
                while indices[i] <= indices[i - 1]:
                    # may throw StopIteration here
                    current[i] = next(iterators[i])
                    indices[i] += 1

            yield tuple(current)

            # move the pointer to the end of the list
            ptr = len(current) - 1

        except StopIteration:
            if ptr == 0:
                # first index is too far through the iterable to allow any
                # more sorted inputs, i.e. `indices[ptr] >= len(iterable) - r`
                return

            # start the terminated generator again from the beginning
            iterators[ptr] = iterable.__reiter__()

            # first value after restarting should not raise StopIteration
            # pylint: disable=stop-iteration-return
            current[ptr] = next(iterators[ptr])
            indices[ptr] = 0

            # move the pointer back to the previous iterator
            ptr -= 1
