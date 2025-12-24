import itertools

from ..repeatable import Repeatable


def permutations(iterable, r=None):
    '''
    Non-greedy version of `itertools.permutations` that handles an arbitrarily
    large, repeatable iterable without writing it to memory.

    Return successive r-length permutations of elements in the iterable.

    If r is not specified or is None, then r defaults to the length of the
    iterable and all possible full-length permutations are generated. If r is
    not specified AND the iterable is infinite, the generator will run forever
    without yielding any values.

    permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    permutations(range(3)) --> 012 021 102 120 201 210
    '''
    # pylint: disable=too-many-branches

    if not isinstance(iterable, Repeatable):
        yield from itertools.permutations(iterable, r)
        return

    if r is None:
        # The generator may loop forever here but this is intentional.
        # We do not know yet whether the iterable is finite, so starting to
        # build up a pool of iterators may consume memory indefinitely.
        # Instead, let's try to find its length by iterating over it once.
        # This is the only memory-safe way to proceed.
        iterator = iterable.__reiter__()

        r = 0
        while True:
            try:
                next(iterator)
            except StopIteration:
                # found `r`
                break
            else:
                r += 1

    iterators = [iterable.__reiter__() for _ in range(r)]

    try:
        # create a pool of iterators
        current = [next(it) for it in iterators]
    except StopIteration:
        # the iterable is empty: yield no responses
        return

    try:
        # try to create first output
        for i in range(r):
            # fast forward `iterators[i]` to position `i`
            for _ in range(i):
                current[i] = next(iterators[i])

        yield tuple(current)

    except StopIteration:
        # `r` is too large for the size of the iterator
        return

    # maintain the indices of the current elemnts' positions in the iterable:
    # used to "fast-forward" a restarted iterator over repeated indices
    indices = list(range(r))

    # set up a pointer to the iterator currently being stepped through
    ptr = r - 1

    while ptr >= 0:
        try:
            # step through the active iterator at least once
            current[ptr] = next(iterators[ptr])
            indices[ptr] += 1

            indices_used = set(indices[:ptr])

            # fast forward the active and all subsequent iterators to the next
            # unused index, ensuring `current` has no repeated input elements
            for i in range(ptr, r):
                # index count should only include the current element
                while indices[i] in indices_used:
                    current[i] = next(iterators[i])
                    indices[i] += 1

                indices_used.add(indices[i])

            yield tuple(current)

            # move the pointer to the end of the list
            ptr = len(current) - 1

        except StopIteration:
            if ptr == 0:
                # finished iterating through all inputs
                return

            # start the terminated generator again from the beginning
            iterators[ptr] = iterable.__reiter__()

            # first value after restarting should not raise StopIteration
            # pylint: disable=stop-iteration-return
            current[ptr] = next(iterators[ptr])
            indices[ptr] = 0

            # move the pointer back to the previous iterator
            ptr -= 1
