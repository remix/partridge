try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

from datetime import datetime
from functools import partial
import numpy as np
import pandas as pd

DATE_FORMAT = "%Y%m%d"


# Why 2^17? See https://git.io/vxB2P.
@lru_cache(maxsize=2 ** 17)
def parse_time(val):
    if val is np.nan:
        return val

    val = val.strip()

    if val == "":
        return np.nan

    h, m, s = val.split(":")
    ssm = int(h) * 3600 + int(m) * 60 + int(s)

    # pandas doesn't have a NaN int, use floats
    return np.float64(ssm)


def parse_date(val):
    return datetime.strptime(val, DATE_FORMAT).date()


# Vectorized parse operations
vparse_date = np.vectorize(parse_date)
vparse_time = np.vectorize(parse_time)
vparse_numeric = partial(pd.to_numeric, errors="raise")
