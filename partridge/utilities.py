import numpy as np
import pandas as pd
from pandas.core.common import flatten


def empty_df(columns=None):
    columns = [] if columns is None else columns
    empty = {col: [] for col in columns}
    return pd.DataFrame(empty, columns=columns, dtype=np.unicode)


def setwrap(value):
    return set(flatten([value]))
