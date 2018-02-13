from datetime import datetime, date
from functools import partial
import numpy as np
import pandas as pd

DATE_FORMAT = '%Y%m%d'


def parse_time(val):
    if val is np.nan:
        return val

    val = val.strip()

    if val == '':
        return np.nan

    h, m, s = val.split(':')
    ssm = int(h) * 3600 + int(m) * 60 + int(s)

    # pandas doesn't have a NaN int, use floats
    return np.float64(ssm)


def parse_bool(val):
    return bool(val)


def parse_date(val):
    if isinstance(val, date):
        return val

    return datetime.strptime(val, DATE_FORMAT).date()


# Vectorized parse operations
vparse_bool = np.vectorize(parse_bool)
vparse_date = np.vectorize(parse_date)
vparse_time = np.vectorize(parse_time)
vparse_numeric = partial(pd.to_numeric, errors='raise')
