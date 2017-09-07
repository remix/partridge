import io
import networkx as nx
import numpy as np
import os
import pandas as pd
from zipfile import ZipFile


from partridge.config import default_config

from partridge.utilities import \
    cached_property, \
    empty_df, \
    setwrap

from partridge.readers import \
    read_service_ids_by_date, \
    read_dates_by_service_ids, \
    read_trip_counts_by_date


def cached_node_getter(filename):
    def func(feed):
        # Get config for node
        config = feed.config
        if config.has_node(filename):
            node = config.nodes[filename]
        else:
            node = {}

        columns = node.get('required_columns', [])
        converters = node.get('converters', {})

        if filename not in feed.zmap:
            # File isn't in the zip, return an empty DataFrame.
            return empty_df(columns)

        # Read CSV into DataFrame, prune it according to the dependency graph
        with ZipFile(feed.path) as zipreader:
            zfile = zipreader.open(feed.zmap[filename], 'r')
            iowrapper = io.TextIOWrapper(zfile, encoding='utf-8-sig')
            reader = pd.read_csv(iowrapper, dtype=np.unicode,
                                            chunksize=10000,
                                            index_col=False,
                                            low_memory=False)

            # Gather the dependencies between this file and others
            feed_dependencies = []
            for _, depfile in config.out_edges(filename):
                edge = config.edges[filename, depfile]
                dependencies = edge.get('dependencies', {}).items()
                if dependencies:
                    propname = os.path.splitext(depfile)[0]
                    feed_dependencies.append((propname, dependencies))

            # Gather applicable view filter params
            view_filter = [
                (col, map(np.unicode, setwrap(value)))
                for col, value in feed.view.get(filename, {}).items()
            ]

            chunks = []
            for chunk in reader:
                # Cleanup column names just to be safe
                chunk.rename(columns=lambda x: x.strip(), inplace=True)

                # Apply filter view
                for col, value in view_filter:
                    if col in chunk.columns:
                        # Filter the chunk by the unicode values set
                        chunk = chunk[chunk[col].isin(value)]

                # Prune rows
                for propname, dependencies in feed_dependencies:
                    # Read the cached, pruned, filtered dependency
                    depdf = getattr(feed, propname)
                    # Prune this chunk
                    for col, depcol in dependencies:
                        if col in chunk.columns and depcol in depdf.columns:
                            chunk = chunk[chunk[col].isin(depdf[depcol])]

                if not chunk.empty:
                    chunks.append(chunk)

            if len(chunks) == 0:
                # Rows were completely pruned away, return an empty DataFrame.
                return empty_df(columns)

        # Concatenate chunks into one DataFrame
        df = pd.concat(chunks)

        # Renumber the index
        df = df.reset_index()

        # Apply conversions, if given
        for col, vfunc in converters.items():
            if col in df.columns and df[col].any():
                df[col] = vfunc(df[col])

        return df

    return cached_property(func)


class feed(object):
    def __init__(self, path, config=None, view=None):
        self.path = path
        self.config = default_config() if config is None else config
        self.view = {} if view is None else view
        self.zmap = {}

        assert os.path.isfile(self.path), 'File not found: {}'.format(self.path)
        assert os.path.getsize(self.path), 'File is empty: {}'.format(self.path)
        assert nx.is_directed_acyclic_graph(self.config), 'Config must be a DAG'

        roots = {n for n, d in self.config.out_degree() if d == 0}
        for filename, param in self.view.items():
            assert filename in roots, \
                'Filter param given for a non-root node ' \
                'of the config graph: {} {}'.format(filename, param)

        with ZipFile(self.path) as zipreader:
            for zpath in zipreader.namelist():
                basename = os.path.basename(zpath)
                assert basename not in self.zmap, \
                    'More than one {} found in {}'.format(basename, self.path)
                self.zmap[basename] = zpath

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



# No pruning or type coercion
class raw_feed(feed):
    def __init__(self, path):
        super().__init__(path, config=nx.DiGraph())

