import datetime
from functools import lru_cache
import numpy as np

DATE_FORMAT = "%Y%m%d"


# Why 2^17? See https://git.io/vxB2P.
@lru_cache(maxsize=2 ** 17)
def parse_time(val: str) -> np.float64:
    if val is np.nan:
        return val

    val = val.strip()

    if val == "":
        return np.nan

    h, m, s = val.split(":")
    ssm = int(h) * 3600 + int(m) * 60 + int(s)

    # pandas doesn't have a NaN int, use floats
    return np.float64(ssm)


def parse_date(val: str) -> datetime.date:
    return datetime.datetime.strptime(val, DATE_FORMAT).date()


vparse_date = np.vectorize(parse_date)
vparse_time = np.vectorize(parse_time)
