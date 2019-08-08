import datetime
import pytest

import partridge as ptg
from partridge.config import default_config, empty_config
from partridge.gtfs import Feed

from .helpers import fixture, fixtures_dir


def test_invalid_source():
    with pytest.raises(ValueError, match=r"Invalid source"):
        Feed(fixture("missing"))


def test_duplicate_files():
    with pytest.raises(ValueError, match=r"More than one"):
        Feed(fixtures_dir)


def test_bad_edge_config():
    config = default_config()

    # Remove the `dependencies` key from an edge config
    config.edges["stop_times.txt", "trips.txt"].pop("dependencies")

    feed = Feed(fixture("caltrain-2017-07-24"), config=config)

    with pytest.raises(ValueError, match=r"Edge missing `dependencies` attribute"):
        feed.stop_times


def test_set():
    feed = Feed(fixture("caltrain-2017-07-24"))
    newval = object()
    feed.set("newkey", newval)
    assert feed.get("newkey") is newval


@pytest.mark.parametrize(
    "path,dates,shapes",
    [
        (
            fixture("caltrain-2017-07-24"),
            [],
            {
                "agency.txt": (1, 6),
                "calendar.txt": (3, 10),
                "calendar_dates.txt": (642, 3),
                "fare_attributes.txt": (6, 6),
                "fare_rules.txt": (144, 4),
                "routes.txt": (4, 7),
                "shapes.txt": (3008, 5),
                "stops.txt": (64, 12),
            },
        ),
        (
            fixture("caltrain-2017-07-24"),
            [datetime.date(2017, 8, 6)],
            {
                "agency.txt": (1, 6),
                "calendar.txt": (1, 10),
                "calendar_dates.txt": (6, 3),
                "fare_attributes.txt": (4, 6),
                "fare_rules.txt": (48, 4),
                "routes.txt": (3, 7),
                "shapes.txt": (1094, 5),
                "stops.txt": (50, 12),
            },
        ),
        (
            fixture("nested"),
            [datetime.date(2017, 8, 6)],
            {
                "agency.txt": (1, 6),
                "calendar.txt": (1, 10),
                "calendar_dates.txt": (6, 3),
                "fare_attributes.txt": (4, 6),
                "fare_rules.txt": (48, 4),
                "routes.txt": (3, 7),
                "shapes.txt": (1094, 5),
                "stops.txt": (50, 12),
            },
        ),
        (
            fixture("amazon-2017-08-06"),
            [],
            {
                "agency.txt": (1, 7),
                "calendar.txt": (2, 10),
                "calendar_dates.txt": (2, 3),
                "fare_attributes.txt": (0, 5),
                "fare_rules.txt": (0, 1),
                "routes.txt": (50, 9),
                "shapes.txt": (12032, 5),
                "stops.txt": (35, 12),
            },
        ),
        (
            fixture("amazon-2017-08-06"),
            [datetime.date(2017, 8, 5)],
            {
                "agency.txt": (1, 7),
                "calendar.txt": (1, 10),
                "calendar_dates.txt": (2, 3),
                "fare_attributes.txt": (0, 5),
                "fare_rules.txt": (0, 1),
                "routes.txt": (1, 9),
                "shapes.txt": (3, 5),
                "stops.txt": (2, 12),
            },
        ),
        (
            fixture("region-nord-v2"),
            [],
            {
                "agency.txt": (1, 7),
                "calendar.txt": (0, 10),
                "calendar_dates.txt": (333, 3),
                "fare_attributes.txt": (0, 5),
                "fare_rules.txt": (0, 1),
                "routes.txt": (181, 12),
                "shapes.txt": (0, 4),
                "stops.txt": (3693, 15),
            },
        ),
    ],
)
def test_read_file(path, dates, shapes):
    service_ids_by_date = ptg.read_service_ids_by_date(path)

    service_ids = {
        service_id
        for date in dates
        if date in service_ids_by_date
        for service_id in service_ids_by_date[date]
    }

    if service_ids:
        feed = Feed(path, view={"trips.txt": {"service_id": service_ids}})
    else:
        feed = Feed(path)

    for filename, shape in shapes.items():
        assert (
            feed.get(filename).shape == shape
        ), "{}/{} dataframe shape was incorrect".format(path, filename)


@pytest.mark.parametrize(
    "path,shapes",
    [
        (
            fixture("empty"),
            {
                "agency.txt": (0, 3),
                "calendar.txt": (0, 0),
                "calendar_dates.txt": (0, 3),
                "fare_attributes.txt": (0, 5),
                "fare_rules.txt": (0, 1),
                "routes.txt": (0, 4),
                "stops.txt": (0, 4),
            },
        ),
        (
            fixture("caltrain-2017-07-24"),
            {
                "agency.txt": (1, 6),
                "calendar.txt": (3, 10),
                "calendar_dates.txt": (642, 3),
                "fare_attributes.txt": (6, 6),
                "fare_rules.txt": (144, 4),
                "routes.txt": (4, 7),
                "shapes.txt": (3008, 5),
                "stops.txt": (64, 12),
            },
        ),
        (
            fixture("amazon-2017-08-06"),
            {
                "agency.txt": (1, 7),
                "calendar.txt": (3, 10),
                "calendar_dates.txt": (2, 3),
                "fare_attributes.txt": (0, 0),
                "fare_rules.txt": (0, 0),
                "routes.txt": (50, 9),
                "shapes.txt": (12032, 5),
                "stops.txt": (35, 12),
            },
        ),
        (
            fixture("region-nord-v2"),
            {
                "agency.txt": (1, 7),
                "calendar.txt": (0, 0),
                "calendar_dates.txt": (333, 3),
                "fare_attributes.txt": (0, 0),
                "fare_rules.txt": (0, 0),
                "routes.txt": (181, 12),
                "shapes.txt": (0, 0),
                "stops.txt": (3693, 15),
            },
        ),
    ],
)
def test_raw_feed(path, shapes):
    feed = Feed(path, config=empty_config())

    for filename, shape in shapes.items():
        assert (
            feed.get(filename).shape == shape
        ), "{}/{} dataframe shape was incorrect".format(path, filename)


@pytest.mark.parametrize(
    "path", [fixture("amazon-2017-08-06"), fixture("caltrain-2017-07-24")]
)
def test_filtered_columns(path):
    service_ids_by_date = ptg.read_service_ids_by_date(path)
    service_ids = list(service_ids_by_date.values())[0]

    feed_full = Feed(path)
    feed_view = Feed(path, view={"trips.txt": {"service_id": service_ids}})
    feed_null = Feed(path, view={"trips.txt": {"service_id": "never-match"}})

    assert set(feed_full.trips.columns) == set(feed_view.trips.columns)
    assert set(feed_full.trips.columns) == set(feed_null.trips.columns)
