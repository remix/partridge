import datetime

import partridge as ptg
import pytest

from .helpers import fixture, zip_file


@pytest.mark.parametrize('path', [
    zip_file('caltrain-2017-07-24'),
    fixture('caltrain-2017-07-24'),
])
def test_get_representative_feed(path):
    trip_counts_by_date = ptg.read_trip_counts_by_date(path)
    service_ids_by_date = ptg.read_service_ids_by_date(path)
    date, _ = max(trip_counts_by_date.items(), key=lambda p: p[1])
    service_ids = service_ids_by_date[date]

    feed = ptg.get_representative_feed(path)
    assert isinstance(feed, ptg.feed)
    assert feed.view == {'trips.txt': {'service_id': service_ids}}

@pytest.mark.parametrize('path', [
    zip_file('amazon-2017-08-06'),
    fixture('amazon-2017-08-06'),
])
def test_service_ids_by_date(path):
    service_ids_by_date = ptg.read_service_ids_by_date(path)

    assert service_ids_by_date == {
        datetime.date(2017, 8, 1): frozenset({'1', '0'}),
        datetime.date(2017, 8, 2): frozenset({'1', '0'}),
        datetime.date(2017, 8, 3): frozenset({'1', '0'}),
        datetime.date(2017, 8, 4): frozenset({'1', '0'}),
        datetime.date(2017, 8, 5): frozenset({'1'}),
        datetime.date(2017, 8, 7): frozenset({'1', '0'})
    }

@pytest.mark.parametrize('path', [
    zip_file('amazon-2017-08-06'),
    fixture('amazon-2017-08-06'),
])
def test_dates_by_service_ids(path):
    dates_by_service_ids = ptg.read_dates_by_service_ids(path)

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

@pytest.mark.parametrize('path', [
    zip_file('amazon-2017-08-06'),
    fixture('amazon-2017-08-06'),
])
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
