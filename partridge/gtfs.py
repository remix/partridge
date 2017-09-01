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
        config = feed.config

        #
        # Get config for node
        #
        if config.has_node(filename):
            node = config.nodes[filename]
        else:
            node = {}

        #
        # Read CSV into DataFrame, prune it according to the dependency graph
        #
        with ZipFile(feed.path) as zipreader:
            zmap = {os.path.basename(path): path for path in zipreader.namelist()}
            if filename in zmap:
                zfile = zipreader.open(zmap[filename], 'r')
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
                    if any(dependencies):
                        propname = os.path.splitext(depfile)[0]
                        feed_dependencies.append((propname, dependencies))
 
                chunks = []
                for chunk in reader:
                    # Cleanup column names just to be safe
                    chunk.rename(columns=lambda x: x.strip(), inplace=True)

                    #
                    # Prune rows
                    #
                    for propname, dependencies in feed_dependencies:
                        # Read the cached, pruned dependency
                        depdf = getattr(feed, propname)

                        # Prune this chunk
                        for col, depcol in dependencies:
                            if col in chunk.columns and depcol in depdf.columns:
                                chunk = chunk[chunk[col].isin(depdf[depcol])]

                    chunks.append(chunk)

                # Combine chunks into one DataFrame
                df = pd.concat(chunks)
            else:
                # Return an empty DataFrame, specifying expected columns if given.
                columns = node.get('required_columns', [])
                empty = {col: [] for col in columns}
                df = pd.DataFrame(empty, columns=columns, dtype=np.unicode)

        if df.empty:
            # Return early if the DataFrame is empty
            return df

        #
        # Convert types
        #
        converters = node.get('converters', {})

        # Apply conversions, if given
        for col, vfunc in converters.items():
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



# No pruning or type coercion
class raw_feed(feed):
    def __init__(self, path):
        super().__init__(path, config=nx.DiGraph())

