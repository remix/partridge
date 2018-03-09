import os
import shutil
import tempfile

from partridge.config import default_config
from partridge.readers import get_filtered_feed
from partridge.utilities import remove_node_attributes


DEFAULT_NODES = frozenset(default_config().nodes())


def extract_agencies(inpath, outpath, agency_ids):
    filters = {'routes.txt': {'agency_id': agency_ids}}
    return extract_feed(inpath, outpath, filters)


def extract_routes(inpath, outpath, route_ids):
    filters = {'trips.txt': {'route_id': route_ids}}
    return extract_feed(inpath, outpath, filters)


def extract_feed(inpath, outpath, filters, config=None):
    config = default_config() if config is None else config
    config = remove_node_attributes(config, 'converters')
    feed = get_filtered_feed(inpath, filters, config)
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
