from collections import defaultdict
import datetime

from partridge.gtfs import feed as mkfeed, raw_feed
from partridge.parsers import vparse_date


DAY_NAMES = (
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
    'saturday', 'sunday')


'''Public'''


def get_representative_feed(path):
    feed = raw_feed(path)

    service_ids_by_date = _service_ids_by_date(feed)
    trip_counts_by_date = _trip_counts_by_date(feed)

    date, _ = max(trip_counts_by_date.items(), key=lambda p: p[1])
    service_ids = service_ids_by_date[date]
    view = {'trips.txt': {'service_id': service_ids}}

    return mkfeed(path, view=view)


def read_service_ids_by_date(path):
    '''Find all service identifiers by date'''
    feed = raw_feed(path)
    return _service_ids_by_date(feed)


def read_dates_by_service_ids(path):
    '''Find dates with identical service'''
    feed = raw_feed(path)
    return _dates_by_service_ids(feed)


def read_trip_counts_by_date(path):
    '''A useful proxy for busyness'''
    feed = raw_feed(path)
    return _trip_counts_by_date(feed)


'''Private'''


def _service_ids_by_date(feed):
    results = defaultdict(set)
    removals = defaultdict(set)

    calendar = feed.calendar
    caldates = feed.calendar_dates
    trips = feed.trips

    service_ids = set(trips.service_id)

    # Process calendar.txt if it exists
    if not calendar.empty:
        calendar = calendar[calendar.service_id.isin(service_ids)].copy()

        # Ensure dates have been parsed
        calendar.start_date = vparse_date(calendar.start_date)
        calendar.end_date = vparse_date(calendar.end_date)

        # Build up results dict from calendar ranges
        for _, cal in calendar.iterrows():
            start = cal.start_date.toordinal()
            end = cal.end_date.toordinal()

            dow = {i: cal[day] for i, day in enumerate(DAY_NAMES)}
            for ordinal in range(start, end + 1):
                date = datetime.date.fromordinal(ordinal)
                if int(dow[date.weekday()]):
                    results[date].add(cal.service_id)

    # Process calendar_dates.txt if it exists
    if not caldates.empty:
        caldates = caldates[caldates.service_id.isin(service_ids)].copy()

        # Ensure dates have been parsed
        caldates.date = vparse_date(caldates.date)

        # Split out additions and removals
        cdadd = caldates[caldates.exception_type == '1']
        cdrem = caldates[caldates.exception_type == '2']

        # Add to results by date
        for _, cd in cdadd.iterrows():
            results[cd.date].add(cd.service_id)

        # Collect removals
        for _, cd in cdrem.iterrows():
            removals[cd.date].add(cd.service_id)

        # Finally, process removals by date
        for date in removals:
            for service_id in removals[date]:
                if service_id in results[date]:
                    results[date].remove(service_id)

            # Drop the key from results if no service present
            if len(results[date]) == 0:
                del results[date]

    return {k: frozenset(v) for k, v in results.items()}


def _dates_by_service_ids(feed):
    results = defaultdict(set)
    for date, service_ids in _service_ids_by_date(feed).items():
        results[service_ids].add(date)
    return dict(results)


def _trip_counts_by_date(feed):
    results = defaultdict(int)
    trips = feed.trips
    for service_ids, dates in _dates_by_service_ids(feed).items():
        trip_count = trips[trips.service_id.isin(service_ids)].shape[0]
        for date in dates:
            results[date] += trip_count
    return dict(results)
