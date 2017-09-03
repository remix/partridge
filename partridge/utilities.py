from functools import lru_cache


def cached_property(func, maxsize=None):
    func = lru_cache(maxsize=maxsize)(func)
    func = property(func)
    return func


def setwrap(value):
    return set(flatten([value]))


def flatten(iterable):
    for x in iterable:
        if hasattr(x, '__iter__') and not isinstance(x, str):
            for y in flatten(x):
                yield y
        else:
            yield x


if __name__ == '__main__':
    assert setwrap('2530.TA.2-T1-A-sj2-2.28.H') == {'2530.TA.2-T1-A-sj2-2.28.H'}
    assert setwrap(['a']) == {'a'}
    assert setwrap({'a'}) == {'a'}
