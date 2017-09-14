from collections import defaultdict
import datetime
from itertools import chain
import os

import numpy as np

from partridge.config import default_config
from partridge.parsers import vparse_date



DAY_NAMES = (
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
    'saturday', 'sunday')



def read_trip_counts_by_date(feed):
    '''A useful proxy for busyness'''
    results = defaultdict(int)
    for service_ids, dates in feed.dates_by_service_ids.items():
        trip_count = feed.trips[feed.trips.service_id.isin(service_ids)].shape[0]
        for date in dates:
            results[date] += trip_count
    return dict(results)


def read_dates_by_service_ids(feed):
    '''Find dates with identical service'''
    results = defaultdict(set)
    for date, service_ids in feed.service_ids_by_date.items():
        results[service_ids].add(date)
    return dict(results)


def read_service_ids_by_date(feed):
    '''Find all service identifiers by date'''
    results = defaultdict(set)
    removals = defaultdict(set)

    service_ids = set(feed.trips.service_id)

    # Process calendar.txt if it exists
    if not feed.calendar.empty:
        calendar = feed.calendar[feed.calendar.service_id.isin(service_ids)].copy()

        # Ensure dates have been parsed
        calendar.start_date = vparse_date(calendar.start_date)
        calendar.end_date = vparse_date(calendar.end_date)

        # Build up results dict from calendar ranges
        for _, cal in calendar.iterrows():
            start = cal['start_date'].toordinal()
            end = cal['end_date'].toordinal()

            # Truncate sloppy date ranges like 2017-2099
            if end - start > 10000:
                end = start + 10000

            dow = {i: cal[day] for i, day in enumerate(DAY_NAMES)}
            for ordinal in range(start, end + 1):
                date = datetime.date.fromordinal(ordinal)
                if dow[date.weekday()]:
                    results[date].add(cal['service_id'])

    # Process calendar_dates.txt if it exists
    if not feed.calendar_dates.empty:
        calendar_dates = feed.calendar_dates[feed.calendar_dates.service_id.isin(service_ids)].copy()

        # Ensure dates have been parsed
        calendar_dates.date = vparse_date(calendar_dates.date)

        cdadd = calendar_dates[calendar_dates.exception_type.astype(int) == 1]
        cdrem = calendar_dates[calendar_dates.exception_type.astype(int) == 2]

        for _, cd in cdadd.iterrows():
            results[cd['date']].add(cd['service_id'])
        for _, cd in cdrem.iterrows():
            removals[cd['date']].add(cd['service_id'])

        # Finally, process removals by date
        for date in removals:
            for service_id in removals[date]:
                if service_id in results[date]:
                    results[date].remove(service_id)

            # Drop the key from results if no service present
            if not any(results[date]):
                del results[date]

    return {k: frozenset(v) for k, v in results.items()}
