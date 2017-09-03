from functools import lru_cache
import numpy as np
import pandas as pd


def cached_property(func, maxsize=None):
    func = lru_cache(maxsize=maxsize)(func)
    func = property(func)
    return func


def empty_df(columns=None):
    columns = [] if columns is None else columns
    empty = {col: [] for col in columns}
    return pd.DataFrame(empty, columns=columns, dtype=np.unicode)


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
