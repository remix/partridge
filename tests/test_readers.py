import datetime

import numpy as np
import partridge as ptg
import pytest

from .helpers import fixture, zip_file


def test_load_feed():
    feed = ptg.load_feed(fixture("amazon-2017-08-06"))
    assert feed.stop_times.dtypes["stop_id"] == np.object
    assert feed.stop_times.dtypes["stop_sequence"] == np.int64
    assert feed.stop_times.dtypes["arrival_time"] == np.float64


def test_load_geo_feed():
    gpd = pytest.importorskip("geopandas")

    feed = ptg.load_geo_feed(fixture("amazon-2017-08-06"))
    assert isinstance(feed.shapes, gpd.GeoDataFrame)
    assert isinstance(feed.stops, gpd.GeoDataFrame)
    assert {"LineString"} == set(feed.shapes.geom_type)
    assert {"Point"} == set(feed.stops.geom_type)
    assert feed.shapes.crs == {"init": "EPSG:4326"}
    assert feed.stops.crs == {"init": "EPSG:4326"}
    assert ["shape_id", "geometry"] == list(feed.shapes.columns)
    assert [
        "stop_id",
        "stop_code",
        "stop_name",
        "stop_desc",
        "zone_id",
        "stop_url",
        "location_type",
        "parent_station",
        "stop_timezone",
        "wheelchair_boarding",
        "geometry",
    ] == list(feed.stops.columns)


def test_load_geo_feed_empty():
    gpd = pytest.importorskip("geopandas")

    feed = ptg.load_geo_feed(fixture("empty"))

    assert isinstance(feed.shapes, gpd.GeoDataFrame)
    assert isinstance(feed.stops, gpd.GeoDataFrame)
    assert feed.shapes.empty
    assert feed.stops.empty


def test_missing_dir():
    with pytest.raises(ValueError, match=r"File or path not found"):
        ptg.load_feed(fixture("missing"))


def test_config_must_be_dag():
    config = ptg.config.default_config()

    assert config.has_edge("routes.txt", "trips.txt")

    # Make a cycle
    config.add_edge("trips.txt", "routes.txt")

    path = fixture("amazon-2017-08-06")
    with pytest.raises(ValueError, match=r"Config must be a DAG"):
        ptg.load_feed(path, config=config)


def test_prune_converted_dtypes():
    config = ptg.config.default_config()
    config.nodes["trips.txt"]["converters"]["route_id"] = np.int64
    config.nodes["routes.txt"]["converters"]["route_id"] = np.int64

    path = fixture("seattle-area-2017-11-16")
    feed = ptg.load_feed(path, config=config)

    # confirm that the dtype conversions were applied
    assert feed.trips.route_id.dtype == np.int64
    assert feed.routes.route_id.dtype == np.int64

    # confirm uniqueness of route_id before further assertions
    assert len(feed.routes.route_id) == len(set(feed.routes.route_id))

    # regression test for issue #62
    assert list(feed.routes.route_id) == [
        100232,
        100235,
        100236,
        100239,
        100240,
        100241,
        100336,
        100337,
        100340,
        100451,
        100479,
        100511,
        102638,
        102640,
    ]


def test_prune_dtype_mismatch():
    config = ptg.config.default_config()
    config.nodes["trips.txt"]["converters"]["route_id"] = np.int64
    config.nodes["routes.txt"]["converters"]["route_id"] = np.unicode

    path = fixture("seattle-area-2017-11-16")
    feed = ptg.load_feed(path, config=config)

    with pytest.raises(ValueError, match=r"configuration error"):
        _ = feed.routes


def test_no_service():
    path = fixture("empty")
    with pytest.raises(AssertionError, match=r"No service"):
        ptg.read_service_ids_by_date(path)


@pytest.mark.parametrize(
    "path", [zip_file("amazon-2017-08-06"), fixture("amazon-2017-08-06")]
)
def test_service_ids_by_date(path):
    service_ids_by_date = ptg.read_service_ids_by_date(path)

    assert service_ids_by_date == {
        datetime.date(2017, 8, 1): frozenset({"1", "0"}),
        datetime.date(2017, 8, 2): frozenset({"1", "0"}),
        datetime.date(2017, 8, 3): frozenset({"1", "0"}),
        datetime.date(2017, 8, 4): frozenset({"1", "0"}),
        datetime.date(2017, 8, 5): frozenset({"1"}),
        datetime.date(2017, 8, 7): frozenset({"1", "0"}),
    }


def test_unused_service_ids():
    # Feed has rows in calendar.txt and calendar_dates.txt
    # with `service_id`s that have no applicable trips
    path = fixture("trimet-vermont-2018-02-06")
    ptg.read_service_ids_by_date(path)


def test_missing_calendar_dates():
    path = fixture("israel-public-transportation-route-2126")
    ptg.read_service_ids_by_date(path)


@pytest.mark.parametrize(
    "path", [zip_file("amazon-2017-08-06"), fixture("amazon-2017-08-06")]
)
def test_dates_by_service_ids(path):
    dates_by_service_ids = ptg.read_dates_by_service_ids(path)

    assert dates_by_service_ids == {
        frozenset({"1"}): {datetime.date(2017, 8, 5)},
        frozenset({"1", "0"}): {
            datetime.date(2017, 8, 1),
            datetime.date(2017, 8, 2),
            datetime.date(2017, 8, 3),
            datetime.date(2017, 8, 4),
            datetime.date(2017, 8, 7),
        },
    }


@pytest.mark.parametrize(
    "path", [zip_file("amazon-2017-08-06"), fixture("amazon-2017-08-06")]
)
def test_trip_counts_by_date(path):
    trip_counts_by_date = ptg.read_trip_counts_by_date(path)

    assert trip_counts_by_date == {
        datetime.date(2017, 8, 1): 442,
        datetime.date(2017, 8, 2): 442,
        datetime.date(2017, 8, 3): 442,
        datetime.date(2017, 8, 4): 442,
        datetime.date(2017, 8, 5): 1,
        datetime.date(2017, 8, 7): 442,
    }


@pytest.mark.parametrize(
    "path", [zip_file("amazon-2017-08-06"), fixture("amazon-2017-08-06")]
)
def test_busiest_date(path):
    date, service_ids = ptg.read_busiest_date(path)
    assert date == datetime.date(2017, 8, 1)
    assert service_ids == frozenset({"0", "1"})


@pytest.mark.parametrize(
    "path", [zip_file("amazon-2017-08-06"), fixture("amazon-2017-08-06")]
)
def test_busiest_week(path):
    service_ids_by_date = ptg.read_busiest_week(path)
    assert service_ids_by_date == {
        datetime.date(2017, 8, 1): frozenset({"0", "1"}),
        datetime.date(2017, 8, 2): frozenset({"0", "1"}),
        datetime.date(2017, 8, 3): frozenset({"0", "1"}),
        datetime.date(2017, 8, 4): frozenset({"0", "1"}),
        datetime.date(2017, 8, 5): frozenset({"1"}),
    }
