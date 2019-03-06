import os
import shutil
import tempfile
from multiprocessing.pool import ThreadPool
from typing import Callable, Collection, Optional

import networkx as nx
import pandas as pd

from .config import default_config
from .gtfs import Feed
from .readers import load_feed
from .types import View
from .utilities import remove_node_attributes


DEFAULT_NODES = frozenset(default_config().nodes())
TMP_COMBINE_COL = "__combine_column__"


def extract_feed(
    inpath: str, outpath: str, view: View, config: nx.DiGraph = None
) -> str:
    """Extract a subset of a GTFS zip into a new file"""
    config = default_config() if config is None else config
    config = remove_node_attributes(config, "converters")
    feed = load_feed(inpath, view, config)
    return write_feed_dangerously(feed, outpath)


def combine_routes_by_column(
    inpath: str, outpath: str, col: str, config: nx.DiGraph = None
):
    return combine_entities_by(
        inpath, outpath, "routes.txt", "route_id", lambda r: r[col]
    )


def combine_entities_by(
    inpath: str,
    outpath: str,
    filename: str,
    column: str,
    transform: Callable,
    config: nx.DiGraph = None,
):
    config = default_config() if config is None else config
    config = remove_node_attributes(config, "converters")
    feed = load_feed(inpath, config=config)

    original_df = feed.get(filename)
    original_df[TMP_COMBINE_COL] = original_df.apply(transform, axis=1)

    mapping = {}
    records = []
    for common, group in original_df.groupby(TMP_COMBINE_COL):
        for original_val in group[column]:
            mapping[original_val] = common

        record = group.iloc[0]
        record[column] = common
        records.append(record)

    for rel_type in (feed.predecessors, feed.successors):
        for _, col, depfile, depcol in rel_type(filename):
            depdf = feed.get(depfile)
            if col == column and depcol in depdf:
                depdf[depcol] = depdf[depcol].apply(lambda x: mapping.get(x, x))

    df = pd.DataFrame.from_records(records, exclude=[TMP_COMBINE_COL])
    feed.set(filename, df)

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
