import numpy as np
import pandas as pd
from pandas.core.common import flatten


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
