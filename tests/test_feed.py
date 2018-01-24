import datetime
import os
import pytest

import partridge as ptg

from .helpers import fixture, zip_file


@pytest.mark.parametrize('path,dates,shapes', [
    (zip_file('empty'), [], {
        'agency.txt': (0, 3),
        'calendar.txt': (0, 10),
        'calendar_dates.txt': (0, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (0, 4),
        'stops.txt': (0, 4),
    }),
    (zip_file('empty'), [datetime.date(2099, 1, 1)], {
        'agency.txt': (0, 3),
        'calendar.txt': (0, 10),
        'calendar_dates.txt': (0, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (0, 4),
        'stops.txt': (0, 4),
    }),
    (zip_file('caltrain-2017-07-24'), [], {
        'agency.txt': (1, 6),
        'calendar.txt': (3, 10),
        'calendar_dates.txt': (642, 3),
        'fare_attributes.txt': (6, 6),
        'fare_rules.txt': (144, 4),
        'routes.txt': (4, 7),
        'shapes.txt': (3008, 5),
        'stops.txt': (64, 12),
    }),
    (zip_file('caltrain-2017-07-24'), [datetime.date(2017, 8, 6)], {
        'agency.txt': (1, 6),
        'calendar.txt': (1, 10),
        'calendar_dates.txt': (6, 3),
        'fare_attributes.txt': (4, 6),
        'fare_rules.txt': (48, 4),
        'routes.txt': (3, 7),
        'shapes.txt': (1094, 5),
        'stops.txt': (50, 12),
    }),
    (zip_file('amazon-2017-08-06'), [], {
        'agency.txt': (1, 7),
        'calendar.txt': (2, 10),
        'calendar_dates.txt': (2, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (50, 9),
        'shapes.txt': (12032, 5),
        'stops.txt': (35, 12),
    }),
    (zip_file('amazon-2017-08-06'), [datetime.date(2017, 8, 5)], {
        'agency.txt': (1, 7),
        'calendar.txt': (1, 10),
        'calendar_dates.txt': (2, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (1, 9),
        'shapes.txt': (3, 5),
        'stops.txt': (2, 12),
    }),
    (fixture('empty'), [], {
        'agency.txt': (0, 3),
        'calendar.txt': (0, 10),
        'calendar_dates.txt': (0, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (0, 4),
        'stops.txt': (0, 4),
    }),
    (fixture('empty'), [datetime.date(2099, 1, 1)], {
        'agency.txt': (0, 3),
        'calendar.txt': (0, 10),
        'calendar_dates.txt': (0, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (0, 4),
        'stops.txt': (0, 4),
    }),
    (fixture('caltrain-2017-07-24'), [], {
        'agency.txt': (1, 6),
        'calendar.txt': (3, 10),
        'calendar_dates.txt': (642, 3),
        'fare_attributes.txt': (6, 6),
        'fare_rules.txt': (144, 4),
        'routes.txt': (4, 7),
        'shapes.txt': (3008, 5),
        'stops.txt': (64, 12),
    }),
    (fixture('caltrain-2017-07-24'), [datetime.date(2017, 8, 6)], {
        'agency.txt': (1, 6),
        'calendar.txt': (1, 10),
        'calendar_dates.txt': (6, 3),
        'fare_attributes.txt': (4, 6),
        'fare_rules.txt': (48, 4),
        'routes.txt': (3, 7),
        'shapes.txt': (1094, 5),
        'stops.txt': (50, 12),
    }),
    (fixture('amazon-2017-08-06'), [], {
        'agency.txt': (1, 7),
        'calendar.txt': (2, 10),
        'calendar_dates.txt': (2, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (50, 9),
        'shapes.txt': (12032, 5),
        'stops.txt': (35, 12),
    }),
    (fixture('amazon-2017-08-06'), [datetime.date(2017, 8, 5)], {
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
    (zip_file('empty'), {
        'agency.txt': (0, 3),
        'calendar.txt': (0, 10),
        'calendar_dates.txt': (0, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (0, 4),
        'stops.txt': (0, 4),
    }),
    (zip_file('caltrain-2017-07-24'), {
        'agency.txt': (1, 6),
        'calendar.txt': (3, 10),
        'calendar_dates.txt': (642, 3),
        'fare_attributes.txt': (6, 6),
        'fare_rules.txt': (144, 4),
        'routes.txt': (4, 7),
        'shapes.txt': (3008, 5),
        'stops.txt': (64, 12),
    }),
    (zip_file('amazon-2017-08-06'), {
        'agency.txt': (1, 7),
        'calendar.txt': (3, 10),
        'calendar_dates.txt': (2, 3),
        'fare_attributes.txt': (0, 0),
        'fare_rules.txt': (0, 0),
        'routes.txt': (50, 9),
        'shapes.txt': (12032, 5),
        'stops.txt': (35, 12),
    }),
    (fixture('empty'), {
        'agency.txt': (0, 3),
        'calendar.txt': (0, 10),
        'calendar_dates.txt': (0, 3),
        'fare_attributes.txt': (0, 5),
        'fare_rules.txt': (0, 1),
        'routes.txt': (0, 4),
        'stops.txt': (0, 4),
    }),
    (fixture('caltrain-2017-07-24'), {
        'agency.txt': (1, 6),
        'calendar.txt': (3, 10),
        'calendar_dates.txt': (642, 3),
        'fare_attributes.txt': (6, 6),
        'fare_rules.txt': (144, 4),
        'routes.txt': (4, 7),
        'shapes.txt': (3008, 5),
        'stops.txt': (64, 12),
    }),
    (fixture('amazon-2017-08-06'), {
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
    except AssertionError as err:
        assert 'File or path not found' in repr(err)


def test_config_must_be_dag():
    config = ptg.config.default_config()

    assert config.has_edge('routes.txt', 'trips.txt')

    # Make a cycle
    config.add_edge('trips.txt', 'routes.txt')

    try:
        path = zip_file('amazon-2017-08-06')
        ptg.feed(path, config=config)
    except AssertionError as err:
        assert 'Config must be a DAG' in repr(err)


@pytest.mark.parametrize('path', [
    zip_file('amazon-2017-08-06'),
    zip_file('caltrain-2017-07-24'),
    fixture('amazon-2017-08-06'),
    fixture('caltrain-2017-07-24'),
])
def test_filtered_columns(path):
    service_ids_by_date = ptg.read_service_ids_by_date(path)
    service_ids = list(service_ids_by_date.values())[0]

    feed_full = ptg.feed(path)
    feed_view = ptg.feed(path,
                         view={'trips.txt': {'service_id': service_ids}})
    feed_null = ptg.feed(path,
                         view={'trips.txt': {'service_id': 'never-match'}})

    assert set(feed_full.trips.columns) == set(feed_view.trips.columns)
    assert set(feed_full.trips.columns) == set(feed_null.trips.columns)
