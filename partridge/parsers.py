from datetime import datetime, date
from functools import partial
import numpy as np
import pandas as pd
import six

DATE_FORMAT = '%Y%m%d'

def parse_time(timestr):
    if type(timestr) not in six.string_types:
        return np.nan

    if timestr.strip() == '':
        return np.nan

    h, m, s = timestr.split(':')
    seconds = int(h) * 3600 + int(m) * 60 + int(s)

    return np.float64(seconds)


def parse_date(datestr):
    if isinstance(datestr, date):
        return datestr

    return datetime.strptime(datestr, DATE_FORMAT).date()


# Vectorized parse operations
vparse_date = np.vectorize(parse_date)
vparse_time = np.vectorize(parse_time)
vparse_numeric = partial(pd.to_numeric, errors='raise')
