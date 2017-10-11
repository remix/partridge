import pytest

import datetime
import os

import partridge as ptg


def fixture(filename):
    return os.path.join(os.path.dirname(__file__), 'fixtures', filename)


@pytest.mark.parametrize('path,dates,shapes', [
    (fixture('empty.zip'), [], {
        'agency.txt': (0, 3),
        'calendar.txt': (0, 10),
        'calendar_dates.txt': (0, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (0, 4),
        'stops.txt': (0, 4),
    }),
    (fixture('empty.zip'), [datetime.date(2099, 1, 1)], {
        'agency.txt': (0, 3),
        'calendar.txt': (0, 10),
        'calendar_dates.txt': (0, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (0, 4),
        'stops.txt': (0, 4),
    }),
    (fixture('caltrain-2017-07-24.zip'), [], {
        'agency.txt': (1, 6),
        'calendar.txt': (3, 10),
        'calendar_dates.txt': (642, 3),
        'fare_attributes.txt': (6, 6),
        'fare_rules.txt': (144, 4),
        'routes.txt': (4, 7),
        'shapes.txt': (3008, 5),
        'stops.txt': (64, 12),
    }),
    (fixture('caltrain-2017-07-24.zip'), [datetime.date(2017, 8, 6)], {
        'agency.txt': (1, 6),
        'calendar.txt': (1, 10),
        'calendar_dates.txt': (6, 3),
        'fare_attributes.txt': (4, 6),
        'fare_rules.txt': (48, 4),
        'routes.txt': (3, 7),
        'shapes.txt': (1094, 5),
        'stops.txt': (50, 12),
    }),
    (fixture('amazon-2017-08-06.zip'), [], {
        'agency.txt': (1, 7),
        'calendar.txt': (2, 10),
        'calendar_dates.txt': (2, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (50, 9),
        'shapes.txt': (12032, 5),
        'stops.txt': (35, 12),
    }),
    (fixture('amazon-2017-08-06.zip'), [datetime.date(2017, 8, 5)], {
        'agency.txt': (1, 7),
        'calendar.txt': (1, 10),
        'calendar_dates.txt': (2, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (1, 9),
        'shapes.txt': (3, 5),
        'stops.txt': (2, 12),
    }),
])
def test_read_file(path, dates, shapes):
    service_ids_by_date = ptg.read_service_ids_by_date(path)

    service_ids = {
        service_id
        for date in dates if date in service_ids_by_date
        for service_id in service_ids_by_date[date]
    }

    if service_ids:
        feed = ptg.feed(path, view={'trips.txt': {'service_id': service_ids}})
    else:
        feed = ptg.feed(path)

    for filename, shape in shapes.items():
        attrname, _ = os.path.splitext(filename)
        assert getattr(feed, attrname).shape == shape, \
            '{}/{} dataframe shape was incorrect'.format(path, filename)


@pytest.mark.parametrize('path,shapes', [
    (fixture('empty.zip'), {
        'agency.txt': (0, 0),
        'calendar.txt': (0, 0),
        'calendar_dates.txt': (0, 0),
        'fare_attributes.txt': (0, 0),
        'fare_rules.txt': (0, 0),
        'routes.txt': (0, 0),
        'stops.txt': (0, 0),
    }),
    (fixture('caltrain-2017-07-24.zip'), {
        'agency.txt': (1, 6),
        'calendar.txt': (3, 10),
        'calendar_dates.txt': (642, 3),
        'fare_attributes.txt': (6, 6),
        'fare_rules.txt': (144, 4),
        'routes.txt': (4, 7),
        'shapes.txt': (3008, 5),
        'stops.txt': (64, 12),
    }),
    (fixture('amazon-2017-08-06.zip'), {
        'agency.txt': (1, 7),
        'calendar.txt': (3, 10),
        'calendar_dates.txt': (2, 3),
        'fare_attributes.txt': (0, 0),
        'fare_rules.txt': (0, 0),
        'routes.txt': (50, 9),
        'shapes.txt': (12032, 5),
        'stops.txt': (35, 12),
    }),
])
def test_raw_feed(path, shapes):
    feed = ptg.raw_feed(path)

    for filename, shape in shapes.items():
        attrname, _ = os.path.splitext(filename)
        assert getattr(feed, attrname).shape == shape, \
            '{}/{} dataframe shape was incorrect'.format(path, filename)


def test_missing_zip():
    try:
        ptg.feed(fixture('missing.zip'))
        assert False
    except AssertionError as e:
        assert 'File not found' in repr(e)


def test_config_must_be_dag():
    config = ptg.config.default_config()

    assert config.has_edge('routes.txt', 'trips.txt')

    # Make a cycle
    config.add_edge('trips.txt', 'routes.txt')

    try:
        path = fixture('amazon-2017-08-06.zip')
        ptg.feed(path, config=config)
    except AssertionError as e:
        assert 'Config must be a DAG' in repr(e)


def test_service_ids_by_date():
    path = fixture('amazon-2017-08-06.zip')

    service_ids_by_date = ptg.read_service_ids_by_date(path)
    feed = ptg.feed(path)
    raw_feed = ptg.raw_feed(path)

    assert service_ids_by_date == feed.service_ids_by_date
    assert service_ids_by_date == raw_feed.service_ids_by_date

    assert service_ids_by_date == {
        datetime.date(2017, 8, 1): frozenset({'1', '0'}),
        datetime.date(2017, 8, 2): frozenset({'1', '0'}),
        datetime.date(2017, 8, 3): frozenset({'1', '0'}),
        datetime.date(2017, 8, 4): frozenset({'1', '0'}),
        datetime.date(2017, 8, 5): frozenset({'1'}),
        datetime.date(2017, 8, 7): frozenset({'1', '0'})
    }


def test_dates_by_service_ids():
    path = fixture('amazon-2017-08-06.zip')

    dates_by_service_ids = ptg.read_dates_by_service_ids(path)
    feed = ptg.feed(path)
    raw_feed = ptg.raw_feed(path)

    assert dates_by_service_ids == feed.dates_by_service_ids
    assert dates_by_service_ids == raw_feed.dates_by_service_ids

    assert dates_by_service_ids == {
        frozenset({'1'}): {
            datetime.date(2017, 8, 5),
        },
        frozenset({'1', '0'}): {
            datetime.date(2017, 8, 1),
            datetime.date(2017, 8, 2),
            datetime.date(2017, 8, 3),
            datetime.date(2017, 8, 4),
            datetime.date(2017, 8, 7),
        }
    }


def test_trip_counts_by_date():
    path = fixture('amazon-2017-08-06.zip')

    trip_counts_by_date = ptg.read_trip_counts_by_date(path)
    feed = ptg.feed(path)
    raw_feed = ptg.raw_feed(path)

    assert trip_counts_by_date == feed.trip_counts_by_date
    assert trip_counts_by_date == raw_feed.trip_counts_by_date

    assert trip_counts_by_date == {
        datetime.date(2017, 8, 1): 442,
        datetime.date(2017, 8, 2): 442,
        datetime.date(2017, 8, 3): 442,
        datetime.date(2017, 8, 4): 442,
        datetime.date(2017, 8, 5): 1,
        datetime.date(2017, 8, 7): 442,
    }


@pytest.mark.parametrize('path', [
    fixture('empty.zip'),
    fixture('amazon-2017-08-06.zip'),
    fixture('caltrain-2017-07-24.zip'),
])
def test_structure(path):
    feed = ptg.feed(path)
    for date, service_ids in feed.service_ids_by_date.items():
        member_dates = feed.dates_by_service_ids[service_ids]
        for member in member_dates:
            assert feed.service_ids_by_date[member] == service_ids
            assert feed.trip_counts_by_date[member] > 0
