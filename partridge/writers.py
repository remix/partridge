import os
import shutil
import tempfile
from multiprocessing.pool import ThreadPool
from typing import Collection, Optional

import networkx as nx

from .config import default_config
from .gtfs import Feed
from .readers import load_feed
from .types import View
from .utilities import remove_node_attributes


DEFAULT_NODES = frozenset(default_config().nodes())


def extract_feed(
    inpath: str, outpath: str, view: View, config: nx.DiGraph = None
) -> str:
    """Extract a subset of a GTFS zip into a new file"""
    config = default_config() if config is None else config
    config = remove_node_attributes(config, "converters")
    feed = load_feed(inpath, view, config)
    return write_feed_dangerously(feed, outpath)


def write_feed_dangerously(
    feed: Feed, outpath: str, nodes: Optional[Collection[str]] = None
) -> str:
    """Naively write a feed to a zipfile

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
