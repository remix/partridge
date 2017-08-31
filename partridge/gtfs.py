import io
import networkx as nx
import numpy as np
import os
import pandas as pd
from zipfile import ZipFile


from partridge.utilities import cached_property
from partridge.config import default_config
from partridge.readers import \
    read_service_ids_by_date, \
    read_dates_by_service_ids, \
    read_trip_counts_by_date


def cached_node_getter(filename):
    def func(feed):
        #
        # Get config for node
        #

        if feed.config.has_node(filename):
            node = feed.config.nodes[filename]
        else:
            node = {}

        #
        # Read CSV into DataFrame
        #

        with ZipFile(feed.path) as zipreader:
            zmap = {os.path.basename(path): path for path in zipreader.namelist()}
            if filename in zmap:
                zfile = zipreader.open(zmap[filename], 'r')
                iowrapper = io.TextIOWrapper(zfile, encoding='utf-8-sig')
                df = pd.read_csv(iowrapper, dtype=np.unicode, index_col=False, low_memory=False)

                # Cleanup
                df.rename(columns=lambda x: x.strip(), inplace=True)
            else:
                default_columns = node.get('required_columns', [])
                empty = {col: [] for col in default_columns}
                df = pd.DataFrame(empty, columns=default_columns, dtype=np.unicode)

        if df.empty:
            # Return early if the DataFrame is empty
            return df

        #
        # Prune rows
        #

        for depfile in dict(feed.config.out_edges(filename)).values():
            edge = feed.config.edges[filename, depfile]
            prop, _ext = os.path.splitext(depfile)
            depdf = getattr(feed, prop)
            for col, depcol in edge['dependencies'].items():
                if col in df.columns and depcol in depdf.columns:
                    df = df[df[col].isin(depdf[depcol])]

        if df.empty:
            # Return early if the DataFrame is empty
            return df

        #
        # Convert types
        #

        converters = node.get('converters', {}).items()

        # Return early if there are no converters for the node
        if not any(converters):
            return df

        # Apply given conversions
        for col, vfunc in converters:
            if col in df.columns and df[col].any():
                df[col] = vfunc(df[col])

        return df

    return cached_property(func)



class feed(object):
    def __init__(self, path, config=None):
        self.path = path
        self.config = default_config() if config is None else config

        assert os.path.isfile(self.path), 'File not found: {}'.format(self.path)
        assert os.path.getsize(self.path), 'File is empty: {}'.format(self.path)
        assert nx.is_directed_acyclic_graph(self.config), 'Config must be a DAG'

    agency = cached_node_getter('agency.txt')
    calendar = cached_node_getter('calendar.txt')
    calendar_dates = cached_node_getter('calendar_dates.txt')
    fare_attributes = cached_node_getter('fare_attributes.txt')
    fare_rules = cached_node_getter('fare_rules.txt')
    feed_info = cached_node_getter('feed_info.txt')
    frequencies = cached_node_getter('frequencies.txt')
    routes = cached_node_getter('routes.txt')
    shapes = cached_node_getter('shapes.txt')
    stops = cached_node_getter('stops.txt')
    stop_times = cached_node_getter('stop_times.txt')
    transfers = cached_node_getter('transfers.txt')
    trips = cached_node_getter('trips.txt')

    service_ids_by_date = cached_property(read_service_ids_by_date)
    dates_by_service_ids = cached_property(read_dates_by_service_ids)
    trip_counts_by_date = cached_property(read_trip_counts_by_date)
