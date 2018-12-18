from collections import defaultdict
import datetime
import os
import shutil
import tempfile
from typing import DefaultDict, Dict, FrozenSet, Optional, Set, Tuple
import weakref

from isoweek import Week
import networkx as nx

from .config import default_config, empty_config, reroot_graph
from .gtfs import Feed
from .parsers import vparse_date
from .types import View
from .utilities import remove_node_attributes


DAY_NAMES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def load_feed(
    path: str, view: Optional[View] = None, config: Optional[nx.DiGraph] = None
) -> Feed:
    config = default_config() if config is None else config
    view = {} if view is None else view

    if not nx.is_directed_acyclic_graph(config):
        raise ValueError("Config must be a DAG")

    if os.path.isdir(path):
        feed = _load_feed(path, view, config)
    elif os.path.isfile(path):
        feed = _unpack_feed(path, view, config)
    else:
        raise ValueError("File or path not found: {}".format(path))

    return feed


def load_raw_feed(path: str) -> Feed:
    return load_feed(path, view={}, config=empty_config())


def read_busiest_date(path: str) -> Tuple[datetime.date, FrozenSet[str]]:
    """Find the earliest date with the most trips"""
    feed = load_raw_feed(path)
    return _busiest_date(feed)


def read_busiest_week(path: str) -> Dict[datetime.date, FrozenSet[str]]:
    """Find the earliest week with the most trips"""
    feed = load_raw_feed(path)
    return _busiest_week(feed)


def read_service_ids_by_date(path: str) -> Dict[datetime.date, FrozenSet[str]]:
    """Find all service identifiers by date"""
    feed = load_raw_feed(path)
    return _service_ids_by_date(feed)


def read_dates_by_service_ids(
    path: str
) -> Dict[FrozenSet[str], FrozenSet[datetime.date]]:
    """Find dates with identical service"""
    feed = load_raw_feed(path)
    return _dates_by_service_ids(feed)


def read_trip_counts_by_date(path: str) -> Dict[datetime.date, int]:
    """A useful proxy for busyness"""
    feed = load_raw_feed(path)
    return _trip_counts_by_date(feed)


def _unpack_feed(path: str, view: View, config: nx.DiGraph) -> Feed:
    tmpdir = tempfile.mkdtemp()
    shutil.unpack_archive(path, tmpdir)
    feed: Feed = _load_feed(tmpdir, view, config)

    # Eager cleanup
    feed._delete_after_reading = True

    def finalize() -> None:
        shutil.rmtree(tmpdir)

    # Lazy cleanup
    weakref.finalize(feed, finalize)

    return feed


def _load_feed(path: str, view: View, config: nx.DiGraph) -> Feed:
    """Multi-file feed filtering"""
    config_ = remove_node_attributes(config, "converters")
    feed_ = Feed(path, view={}, config=config_)
    for filename, column_filters in view.items():
        config_ = reroot_graph(config_, filename)
        view_ = {filename: column_filters}
        feed_ = Feed(feed_, view=view_, config=config_)
    return Feed(feed_, config=config)


def _busiest_date(feed: Feed) -> Tuple[datetime.date, FrozenSet[str]]:
    service_ids_by_date = _service_ids_by_date(feed)
    trip_counts_by_date = _trip_counts_by_date(feed)

    def max_by(kv: Tuple[datetime.date, int]) -> Tuple[int, int]:
        date, count = kv
        return count, -date.toordinal()

    date, _ = max(trip_counts_by_date.items(), key=max_by)
    service_ids = service_ids_by_date[date]

    return date, service_ids


def _busiest_week(feed: Feed) -> Dict[datetime.date, FrozenSet[str]]:
    service_ids_by_date = _service_ids_by_date(feed)
    trip_counts_by_date = _trip_counts_by_date(feed)

    weekly_trip_counts: DefaultDict[Week, int] = defaultdict(int)
    weekly_dates: DefaultDict[Week, Set[datetime.date]] = defaultdict(set)
    for date in service_ids_by_date.keys():
        key = Week.withdate(date)
        weekly_trip_counts[key] += trip_counts_by_date[date]
        weekly_dates[key].add(date)

    def max_by(kv: Tuple[Week, int]) -> Tuple[int, int]:
        week, count = kv
        return count, -week.toordinal()

    week, _ = max(weekly_trip_counts.items(), key=max_by)
    dates = sorted(weekly_dates[week])

    return {date: service_ids_by_date[date] for date in dates}


def _service_ids_by_date(feed: Feed) -> Dict[datetime.date, FrozenSet[str]]:
    results: DefaultDict[datetime.date, Set[str]] = defaultdict(set)
    removals: DefaultDict[datetime.date, Set[str]] = defaultdict(set)

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

    assert results, "No service found in feed."

    return {k: frozenset(v) for k, v in results.items()}


def _dates_by_service_ids(feed: Feed) -> Dict[FrozenSet[str], FrozenSet[datetime.date]]:
    results: DefaultDict[FrozenSet[str], Set[datetime.date]] = defaultdict(set)
    for date, service_ids in _service_ids_by_date(feed).items():
        results[service_ids].add(date)
    return {k: frozenset(v) for k, v in results.items()}


def _trip_counts_by_date(feed: Feed) -> Dict[datetime.date, int]:
    results: DefaultDict[datetime.date, int] = defaultdict(int)
    trips = feed.trips
    for service_ids, dates in _dates_by_service_ids(feed).items():
        trip_count = trips[trips.service_id.isin(service_ids)].shape[0]
        for date in dates:
            results[date] += trip_count
    return dict(results)
