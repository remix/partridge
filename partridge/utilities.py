try:
    from functools import lru_cache, wraps
except ImportError:
    from functools32 import lru_cache, wraps

import weakref

from chardet import UniversalDetector
import numpy as np
import pandas as pd
from pandas.core.common import flatten


__all__ = [
    'detect_encoding',
    'empty_df',
    'lru_cache',
    'remove_node_attributes',
    'setwrap',
]


def empty_df(columns=None):
    columns = [] if columns is None else columns
    empty = {col: [] for col in columns}
    return pd.DataFrame(empty, columns=columns, dtype=np.unicode)


def setwrap(value):
    """
    Returns a flattened and stringified set from the given object or iterable.

    For use in public functions which accept argmuents or kwargs that can be
    one object or a list of objects.
    """
    return set(map(np.unicode, set(flatten([value]))))


def remove_node_attributes(G, attributes):
    """
    Return a copy of the graph with the given attributes
    deleted from all nodes.
    """
    G = G.copy()
    for _, data in G.nodes(data=True):
        for attribute in setwrap(attributes):
            if attribute in data:
                del data[attribute]
    return G


def detect_encoding(f, limit=100):
    u = UniversalDetector()
    for line in f:
        line = bytearray(line)
        u.feed(line)

        limit -= 1
        if u.done or limit < 1:
            break

    u.close()
    if u.result['encoding'] == 'ascii':
        return 'utf-8'
    else:
        return u.result['encoding']


def lru_method_cache(*lru_args, **lru_kwargs):
    """
    An LRU cache decorator for methods. It keeps a
    cache per instance and allows the instance to
    be properly garbage collected.

    Credit: https://stackoverflow.com/a/33672499
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(self, *args, **kwargs):
            self_weak = weakref.ref(self)

            @wraps(func)
            @lru_cache(*lru_args, **lru_kwargs)
            def cached_method(*args, **kwargs):
                return func(self_weak(), *args, **kwargs)

            setattr(self, func.__name__, cached_method)
            return cached_method(*args, **kwargs)
        return wrapped_func
    return decorator
