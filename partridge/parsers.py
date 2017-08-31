from datetime import datetime, date
import numpy as np
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
