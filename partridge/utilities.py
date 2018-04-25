try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

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


def detect_encoding(f):
    u = UniversalDetector()
    for line in f:
        line = bytearray(line)
        u.feed(line)
        if u.done:
            break
    u.close()
    return u.result['encoding']
