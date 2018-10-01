import os
import shutil
import tempfile
from multiprocessing.pool import ThreadPool

from .config import default_config
from .readers import load_feed
from .utilities import remove_node_attributes


DEFAULT_NODES = frozenset(default_config().nodes())


def extract_feed(inpath, outpath, filters, config=None):
    config = default_config() if config is None else config
    config = remove_node_attributes(config, "converters")
    feed = load_feed(inpath, filters, config)
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

        def write_node(node):
            df = feed.get(node)
            if not df.empty:
                path = os.path.join(tmpdir, node)
                df.to_csv(path, index=False)

        pool = ThreadPool(len(nodes))
        try:
            pool.map(write_node, nodes)
        finally:
            pool.terminate()

        if outpath.endswith(".zip"):
            outpath, _ = os.path.splitext(outpath)

        outpath = shutil.make_archive(outpath, "zip", tmpdir)
    finally:
        shutil.rmtree(tmpdir)

    return outpath
