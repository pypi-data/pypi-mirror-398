from ..repeatable import Repeatable


def product(*iterables, repeat=1):
    '''
    Non-greedy version of `itertools.product` that handles arbitrarily large,
    repeatable iterables without writing them to memory.

    Cartesian product of input iterables. Equivalent to nested for-loops.

    For example, product(A, B) is equivalent to: ((x,y) for x in A for y in B).
    The leftmost iterators are in the outermost for-loop, so the output tuples
    cycle in a manner similar to an odometer (with the rightmost element
    changing on every iteration).

    To compute the product of an iterable with itself, specify the number
    of repetitions with the optional repeat keyword argument. For example,
    product(A, repeat=4) means the same as product(A, A, A, A).

    product('ab', range(3)) --> ('a',0) ('a',1) ('a',2) ('b',0) ('b',1) ('b',2)
    product((0,1), (0,1), (0,1)) --> (0,0,0) (0,0,1) (0,1,0) (0,1,1) (1,0,0)...
    '''

    iterable_pool = tuple(
        a if isinstance(a, Repeatable) else tuple(a)
        for a in iterables
    ) * repeat

    # create a pool of iterators to step through
    iterators = [
        i.__reiter__() if hasattr(i, '__reiter__')
        else iter(i)
        for i in iterable_pool
    ]

    try:
        # try to create first output
        current = [next(it) for it in iterators]
        yield tuple(current)

    except StopIteration:
        # one of the inputs is empty: yield no responses
        return

    # set up a pointer to the iterator currently being stepped through
    ptr = len(current) - 1

    while ptr >= 0:
        try:
            # step once through the active iterator
            current[ptr] = next(iterators[ptr])
            yield tuple(current)

            # move the pointer to the end of the list
            ptr = len(current) - 1

        except StopIteration:
            if ptr == 0:
                # finished iterating through all inputs
                return

            # start the terminated generator again from the beginning
            it = iterable_pool[ptr % len(iterable_pool)]
            iterators[ptr] = (
                it.__reiter__() if hasattr(it, '__reiter__')
                else iter(it)
            )
            # first value after restarting should not raise StopIteration
            # pylint: disable=stop-iteration-return
            current[ptr] = next(iterators[ptr])

            # move the pointer back to the previous iterator
            ptr -= 1
