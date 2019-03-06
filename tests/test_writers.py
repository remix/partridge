import os
import shutil
import tempfile

import partridge as ptg
import pytest

from .helpers import fixture, zip_file


def test_combine_routes_by_column():
    inpath = fixture("caltrain-2017-07-24")

    try:
        tmpdir = tempfile.mkdtemp()
        outpath = os.path.join(tmpdir, "out.zip")

        ptg.writers.combine_routes_by_column(inpath, outpath, "route_type")

        outfeed = ptg.load_feed(outpath)

        assert ["2", "3"] == list(outfeed.routes.route_id)

        trip_route_ids = set(outfeed.trips.route_id)
        route_route_ids = set(outfeed.routes.route_id)
        assert trip_route_ids == route_route_ids

        assert {"2", "3"} == set(outfeed.fare_rules.route_id)
    finally:
        shutil.rmtree(tmpdir)


def test_combine_entities_by():
    def first_word_of_route_desc(row):
        return row["route_desc"].split(" ")[0].strip()

    inpath = fixture("seattle-area-2017-11-16")
    infeed = ptg.load_feed(inpath)

    try:
        tmpdir = tempfile.mkdtemp()
        outpath = os.path.join(tmpdir, "out.zip")

        ptg.writers.combine_entities_by(
            inpath, outpath, "routes.txt", "route_id", first_word_of_route_desc
        )

        outfeed = ptg.load_feed(outpath)

        assert list(infeed.routes.columns) == list(outfeed.routes.columns)
        assert list(infeed.trips.columns) == list(outfeed.trips.columns)
        assert infeed.trips.shape == outfeed.trips.shape

        assert [
            "Bellevue",
            "Issaquah",
            "Kirkland",
            "LINK:",
            "Overlake",
            "Redmond",
            "Streetcar:",
            "Water",
            "Woodinville",
        ] == list(outfeed.routes.route_id)

        trip_route_ids = set(outfeed.trips.route_id)
        route_route_ids = set(outfeed.routes.route_id)

        assert trip_route_ids == route_route_ids
    finally:
        shutil.rmtree(tmpdir)


@pytest.mark.parametrize(
    "path", [zip_file("seattle-area-2017-11-16"), fixture("seattle-area-2017-11-16")]
)
def test_extract_agencies(path):
    fd = ptg.load_feed(path)

    agencies = fd.agency
    assert len(agencies) == 3

    routes = fd.routes
    assert len(routes) == 14

    agency_ids = [agencies.iloc[0].agency_id]
    route_ids = set(fd.routes[fd.routes.agency_id.isin(agency_ids)].route_id)
    trip_ids = set(fd.trips[fd.trips.route_id.isin(route_ids)].trip_id)
    stop_ids = set(fd.stop_times[fd.stop_times.trip_id.isin(trip_ids)].stop_id)

    assert len(route_ids)
    assert len(trip_ids)
    assert len(stop_ids)

    try:
        tmpdir = tempfile.mkdtemp()
        outfile = os.path.join(tmpdir, "test.zip")

        result = ptg.extract_feed(
            path, outfile, {"routes.txt": {"agency_id": agency_ids}}
        )
        assert result == outfile

        new_fd = ptg.load_feed(outfile)
        assert list(new_fd.agency.agency_id) == agency_ids
        assert set(new_fd.routes.route_id) == route_ids
        assert set(new_fd.trips.trip_id) == trip_ids
        assert set(new_fd.stop_times.trip_id) == trip_ids
        assert set(new_fd.stops.stop_id) == stop_ids

        nodes = []
        for node in fd._config.nodes():
            df = fd.get(node)
            if not df.empty:
                nodes.append(node)

        assert len(nodes)

        for node in nodes:
            original_df = fd.get(node)
            new_df = new_fd.get(node)
            assert set(original_df.columns) == set(new_df.columns)

    finally:
        shutil.rmtree(tmpdir)


@pytest.mark.parametrize(
    "path", [zip_file("seattle-area-2017-11-16"), fixture("seattle-area-2017-11-16")]
)
def test_extract_routes(path):
    fd = ptg.load_feed(path)

    agencies = fd.agency
    assert len(agencies) == 3

    routes = fd.routes
    assert len(routes) == 14

    route_ids = [routes.iloc[0].route_id]
    agency_ids = set(fd.routes[fd.routes.route_id.isin(route_ids)].agency_id)
    trip_ids = set(fd.trips[fd.trips.route_id.isin(route_ids)].trip_id)
    stop_ids = set(fd.stop_times[fd.stop_times.trip_id.isin(trip_ids)].stop_id)

    assert len(agency_ids)
    assert len(trip_ids)
    assert len(stop_ids)

    try:
        tmpdir = tempfile.mkdtemp()
        outfile = os.path.join(tmpdir, "test.zip")

        result = ptg.extract_feed(path, outfile, {"trips.txt": {"route_id": route_ids}})
        assert result == outfile

        new_fd = ptg.load_feed(outfile)
        assert list(new_fd.routes.route_id) == route_ids
        assert set(new_fd.agency.agency_id) == agency_ids
        assert set(new_fd.trips.trip_id) == trip_ids
        assert set(new_fd.stop_times.trip_id) == trip_ids
        assert set(new_fd.stops.stop_id) == stop_ids

        nodes = []
        for node in fd._config.nodes():
            df = fd.get(node)
            if not df.empty:
                nodes.append(node)

        assert len(nodes)

        for node in nodes:
            original_df = fd.get(node)
            new_df = new_fd.get(node)
            assert set(original_df.columns) == set(new_df.columns)

    finally:
        shutil.rmtree(tmpdir)
