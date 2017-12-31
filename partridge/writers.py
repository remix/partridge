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
    return _extract_feed(
        inpath, outpath,
        extract_agencies_config(),
        {'agency.txt': {'agency_id': agency_ids}},
    )


def extract_routes(inpath, outpath, route_ids):
    return _extract_feed(
        inpath, outpath,
        extract_routes_config(),
        {'trips.txt': {'route_id': route_ids}},
    )


def _extract_feed(inpath, outpath, config, view):
    feed = mkfeed(inpath, config, view)
    nodes = set(config.nodes()) | DEFAULT_NODES

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
