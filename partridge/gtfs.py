from collections import defaultdict
import datetime
import io
import networkx as nx
import numpy as np
import os
import pandas as pd
from zipfile import ZipFile


from partridge.config import default_config
from partridge.parsers import vparse_date
from partridge.utilities import cached_property, empty_df, setwrap


DAY_NAMES = (
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
    'saturday', 'sunday')


def read_file(filename):
    def func(feed):
        # Get config for node
        config = feed.config

        if config.has_node(filename):
            node = config.nodes[filename]
        else:
            node = {}

        columns = node.get('required_columns', [])
        converters = node.get('converters', {})

        # If the file isn't in the zip, return an empty DataFrame.
        if filename not in feed.zmap:
            return empty_df(columns)

        # Read CSV into DataFrame, prune it according to the dependency graph
        with ZipFile(feed.path) as zipreader:
            # Prepare a chunked reader for the file
            zfile = zipreader.open(feed.zmap[filename], 'r')
            iowrapper = io.TextIOWrapper(zfile, encoding='utf-8-sig')
            reader = pd.read_csv(iowrapper,
                                 chunksize=10000,
                                 dtype=np.unicode,
                                 index_col=False,
                                 low_memory=False,
                                 skipinitialspace=True,
                                 )

            # Gather the dependencies between this file and others
            file_dependencies = {
                # property name : dependencies
                os.path.splitext(depfile)[0]: data['dependencies'].items()
                for _, depfile, data in config.out_edges(filename, data=True)
                if 'dependencies' in data
            }

            # Gather applicable view filter params
            view_filters = {
                # column name : set of strings
                col: set(map(np.unicode, setwrap(values)))
                for col, values in feed.view.get(filename, {}).items()
            }

            # Process the file in chunks
            chunks = []
            for chunk in reader:
                # Cleanup column names just to be safe
                chunk = chunk.rename(columns=lambda x: x.strip())

                # Apply view filters
                for col, values in view_filters.items():
                    # If applicable, filter this chunk by the
                    # given set of values
                    if col in chunk.columns:
                        chunk = chunk[chunk[col].isin(values)]

                # Prune the chunk
                for propname, dependencies in file_dependencies.items():
                    # Read the filtered, pruned, and cached file dependency
                    depdf = getattr(feed, propname)

                    for col, depcol in dependencies:
                        # If applicable, prune this chunk by the other
                        if col in chunk.columns and depcol in depdf.columns:
                            chunk = chunk[chunk[col].isin(depdf[depcol])]

                # Discard entirely filtered/pruned chunks
                if not chunk.empty:
                    chunks.append(chunk)

            # If all chunks were completely filtered/pruned away,
            # return an empty DataFrame.
            if len(chunks) == 0:
                return empty_df(columns)

        # Concatenate chunks into one DataFrame
        df = pd.concat(chunks)

        # Apply type conversions, strip leading/trailing whitespace
        for col in df.columns:
            if df[col].any():
                df[col] = df[col].str.strip()
                if col in converters:
                    vfunc = converters[col]
                    df[col] = vfunc(df[col])

        return df

    return cached_property(func)


class feed(object):
    def __init__(self, path, config=None, view=None):
        self.path = path
        self.config = default_config() if config is None else config
        self.view = {} if view is None else view
        self.zmap = {}

        assert os.path.isfile(self.path), \
            'File not found: {}'.format(self.path)

        assert nx.is_directed_acyclic_graph(self.config), \
            'Config must be a DAG'

        roots = {n for n, d in self.config.out_degree() if d == 0}
        for filename, param in self.view.items():
            assert filename in roots, \
                'Filter param given for a non-root node ' \
                'of the config graph: {} {}'.format(filename, param)

        with ZipFile(self.path) as zipreader:
            for zpath in zipreader.namelist():
                basename = os.path.basename(zpath)
                if zpath.endswith('.txt'):
                    assert basename not in self.zmap, \
                        'More than one {} in zip'.format(basename)
                self.zmap[basename] = zpath

    agency = read_file('agency.txt')
    calendar = read_file('calendar.txt')
    calendar_dates = read_file('calendar_dates.txt')
    fare_attributes = read_file('fare_attributes.txt')
    fare_rules = read_file('fare_rules.txt')
    feed_info = read_file('feed_info.txt')
    frequencies = read_file('frequencies.txt')
    routes = read_file('routes.txt')
    shapes = read_file('shapes.txt')
    stops = read_file('stops.txt')
    stop_times = read_file('stop_times.txt')
    transfers = read_file('transfers.txt')
    trips = read_file('trips.txt')

    @cached_property
    def service_ids_by_date(self):
        '''Find all service identifiers by date'''
        results = defaultdict(set)
        removals = defaultdict(set)

        calendar = self.calendar
        caldates = self.calendar_dates
        trips = self.trips

        service_ids = set(trips.service_id)

        # Process calendar.txt if it exists
        if not calendar.empty:
            calendar = calendar[calendar.service_id.isin(service_ids)].copy()

            # Ensure dates have been parsed
            calendar.start_date = vparse_date(calendar.start_date)
            calendar.end_date = vparse_date(calendar.end_date)

            # Build up results dict from calendar ranges
            for _, cal in calendar.iterrows():
                start = cal.start_date.toordinal()
                end = cal.end_date.toordinal()

                dow = {i: cal[day] for i, day in enumerate(DAY_NAMES)}
                for ordinal in range(start, end + 1):
                    date = datetime.date.fromordinal(ordinal)
                    if int(dow[date.weekday()]):
                        results[date].add(cal.service_id)

        # Process calendar_dates.txt if it exists
        if not caldates.empty:
            caldates = caldates[caldates.service_id.isin(service_ids)].copy()

            # Ensure dates have been parsed
            caldates.date = vparse_date(caldates.date)

            # Split out additions and removals
            cdadd = caldates[caldates.exception_type.astype(int) == 1]
            cdrem = caldates[caldates.exception_type.astype(int) == 2]

            # Add to results by date
            for _, cd in cdadd.iterrows():
                results[cd.date].add(cd.service_id)

            # Collect removals
            for _, cd in cdrem.iterrows():
                removals[cd.date].add(cd.service_id)

            # Finally, process removals by date
            for date in removals:
                for service_id in removals[date]:
                    if service_id in results[date]:
                        results[date].remove(service_id)

                # Drop the key from results if no service present
                if len(results[date]) == 0:
                    del results[date]

        return {k: frozenset(v) for k, v in results.items()}

    @cached_property
    def dates_by_service_ids(self):
        '''Find dates with identical service'''
        results = defaultdict(set)
        for date, service_ids in self.service_ids_by_date.items():
            results[service_ids].add(date)
        return dict(results)

    @cached_property
    def trip_counts_by_date(self):
        '''A useful proxy for busyness'''
        results = defaultdict(int)
        trips = self.trips
        for service_ids, dates in self.dates_by_service_ids.items():
            trip_count = trips[trips.service_id.isin(service_ids)].shape[0]
            for date in dates:
                results[date] += trip_count
        return dict(results)


# No pruning or type coercion
class raw_feed(feed):
    def __init__(self, path):
        super().__init__(path, config=nx.DiGraph())
