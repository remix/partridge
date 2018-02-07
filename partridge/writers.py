import os
import shutil
import tempfile

from partridge.config import (
    default_config,
    extract_agencies_config,
    extract_routes_config,
)
from partridge.gtfs import feed as mkfeed


DEFAULT_NODES = frozenset(default_config().nodes())


def extract_agencies(inpath, outpath, agency_ids):
    config = extract_agencies_config()
    view = {'agency.txt': {'agency_id': agency_ids}}
    feed = mkfeed(inpath, config, view)
    return write_feed_dangerously(feed, outpath)


def extract_routes(inpath, outpath, route_ids):
    config = extract_routes_config()
    view = {'trips.txt': {'route_id': route_ids}}
    feed = mkfeed(inpath, config, view)
    return write_feed_dangerously(feed, outpath)


def write_feed_dangerously(feed, outpath, nodes=None):
    """
    Naively write a feed to a zipfile

    This function provides no sanity checks. Use it at
    your own risk.
    """
    nodes = DEFAULT_NODES if nodes is None else nodes
    try:
        tmpdir = tempfile.mkdtemp()

        for node in nodes:
            df = feed.get(node)
            if not df.empty:
                path = os.path.join(tmpdir, node)
                df.to_csv(path, index=False)

        if outpath.endswith('.zip'):
            outpath, _ = os.path.splitext(outpath)

        outpath = shutil.make_archive(outpath, 'zip', tmpdir)
    finally:
        shutil.rmtree(tmpdir)

    return outpath
