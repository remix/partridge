from collections import defaultdict
import datetime
import os
import shutil
import tempfile
import weakref

from isoweek import Week
import networkx as nx

from partridge.config import default_config, empty_config, reroot_graph
from partridge.gtfs import Feed
from partridge.parsers import vparse_date
from partridge.utilities import remove_node_attributes


DAY_NAMES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


"""Public"""


def load_feed(path, filters=None, config=None):
    """
    Multi-file feed filtering
    """
    config = default_config() if config is None else config
    filters = {} if filters is None else filters

    is_file, is_dir = os.path.isfile(path), os.path.isdir(path)
    assert is_file or is_dir, "File or path not found: {}".format(path)
    assert nx.is_directed_acyclic_graph(config), "Config must be a DAG"

    if is_file:
        return unpack_feed_(path, filters, config)

    return load_feed_(path, filters, config)


def load_raw_feed(path):
    return load_feed(path, filters={}, config=empty_config())


def unpack_feed_(path, filters, config):
    tmpdir = tempfile.mkdtemp()
    shutil.unpack_archive(path, tmpdir)
    feed = load_feed_(tmpdir, filters, config)

    # Eager cleanup
    feed._delete_after_reading = True

    # Lazy cleanup
    weakref.finalize(feed, lambda: shutil.rmtree(tmpdir))

    return feed


def load_feed_(path, filters, config):
    filter_config = remove_node_attributes(config, "converters")
    trip_ids = set(Feed(path, config=empty_config()).trips.trip_id)

    for filename, column_filters in filters.items():
        feed = Feed(
            path,
            config=reroot_graph(filter_config, filename),
            view={filename: column_filters},
        )
        trip_ids &= set(feed.trips.trip_id)

    view = {"trips.txt": {"trip_id": trip_ids}}
    return Feed(path, view, config)


def read_busiest_date(path):
    """Find the earliest date with the most trips"""
    feed = load_raw_feed(path)
    return _busiest_date(feed)


def read_busiest_week(path):
    """Find the earliest week with the most trips"""
    feed = load_raw_feed(path)
    return _busiest_week(feed)


def read_service_ids_by_date(path):
    """Find all service identifiers by date"""
    feed = load_raw_feed(path)
    return _service_ids_by_date(feed)


def read_dates_by_service_ids(path):
    """Find dates with identical service"""
    feed = load_raw_feed(path)
    return _dates_by_service_ids(feed)


def read_trip_counts_by_date(path):
    """A useful proxy for busyness"""
    feed = load_raw_feed(path)
    return _trip_counts_by_date(feed)


"""Private"""


def _busiest_date(feed):
    service_ids_by_date = _service_ids_by_date(feed)
    trip_counts_by_date = _trip_counts_by_date(feed)

    def max_by(kv):
        date, count = kv
        return count, -date.toordinal()

    date, _ = max(trip_counts_by_date.items(), key=max_by)
    service_ids = service_ids_by_date[date]

    return date, service_ids


def _busiest_week(feed):
    service_ids_by_date = _service_ids_by_date(feed)
    trip_counts_by_date = _trip_counts_by_date(feed)

    weekly_trip_counts = defaultdict(int)
    weekly_dates = defaultdict(list)
    for date in service_ids_by_date.keys():
        key = Week.withdate(date)
        weekly_trip_counts[key] += trip_counts_by_date[date]
        weekly_dates[key].append(date)

    def max_by(kv):
        week, count = kv
        return (count, -week.toordinal())

    week, _ = max(weekly_trip_counts.items(), key=max_by)
    dates = weekly_dates[week]

    return {date: service_ids_by_date[date] for date in dates}


def _service_ids_by_date(feed):
    results = defaultdict(set)
    removals = defaultdict(set)

    service_ids = set(feed.trips.service_id)
    calendar = feed.calendar
    caldates = feed.calendar_dates

    if not calendar.empty:
        # Only consider calendar.txt rows with applicable trips
        calendar = calendar[calendar.service_id.isin(service_ids)].copy()

    if not caldates.empty:
        # Only consider calendar_dates.txt rows with applicable trips
        caldates = caldates[caldates.service_id.isin(service_ids)].copy()

    if not calendar.empty:
        # Parse dates
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

    if not caldates.empty:
        # Parse dates
        caldates.date = vparse_date(caldates.date)

        # Split out additions and removals
        cdadd = caldates[caldates.exception_type == "1"]
        cdrem = caldates[caldates.exception_type == "2"]

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
