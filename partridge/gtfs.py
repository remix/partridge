from contextlib import contextmanager
import io
import os
from zipfile import ZipFile

import networkx as nx
import numpy as np
import pandas as pd

from partridge.config import default_config, empty_config
from partridge.utilities import empty_df, detect_encoding, lru_cache, setwrap


def read_file(filename):
    return property(lambda feed: feed.get(filename))


class feed(object):
    def __init__(self, path, config=None, view=None):
        self.path = path
        self.is_dir = os.path.isdir(self.path)
        self.config = default_config() if config is None else config
        self.view = {} if view is None else view
        self.zmap = {}

        assert os.path.isfile(self.path) or self.is_dir, \
            'File or path not found: {}'.format(self.path)

        assert nx.is_directed_acyclic_graph(self.config), \
            'Config must be a DAG'

        roots = {n for n, d in self.config.out_degree() if d == 0}
        for filename, param in self.view.items():
            assert filename in roots, \
                'Filter param given for a non-root node ' \
                'of the config graph: {} {}'.format(filename, param)

        if self.is_dir:
            self._verify_folder_contents()
        else:
            self._verify_zip_contents()

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

    @lru_cache(maxsize=None)
    def get(self, filename):
        config = self.config

        # Get config for node
        node = config.nodes.get(filename, {})
        columns = node.get('required_columns', [])
        converters = node.get('converters', {})

        # If the file isn't in the zip, return an empty DataFrame.
        if filename not in self.zmap:
            return empty_df(columns)

        # Gather the dependencies between this file and others
        file_dependencies = {
            depfile: data.get('dependencies', [])
            for _, depfile, data in config.out_edges(filename, data=True)
        }

        # Gather applicable view filter params
        view_filters = {
            # column name : set of strings
            col: setwrap(values)
            for col, values in self.view.get(filename, {}).items()
        }

        # Read CSV in chunks, prune it according to the dependency graph
        chunks = []
        with self.read_file_chunks(filename) as reader:
            # Process the file in chunks
            for i, chunk in enumerate(reader):
                # Cleanup column names just to be safe
                chunk = chunk.rename(columns=lambda x: x.strip())

                if i == 0:
                    # Track the actual columns in the file if present
                    columns = list(chunk.columns)

                # Apply view filters
                for col, values in view_filters.items():
                    # If applicable, filter this chunk by the
                    # given set of values
                    if col in chunk.columns:
                        chunk = chunk[chunk[col].isin(values)]

                # Prune the chunk
                for depfile, deplist in file_dependencies.items():
                    # Read the filtered, pruned, and cached file dependency
                    depdf = self.get(depfile)

                    for deps in deplist:
                        col = deps[filename]
                        depcol = deps[depfile]

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

    @contextmanager
    def read_file_chunks(self, filename):
        """
        Yield a pandas DataFrame iterator for the given file.
        """
        with self._io_adapter(self.zmap[filename]) as result:
            iowrapper, encoding = result
            try:
                yield pd.read_csv(
                    iowrapper, chunksize=10000,
                    dtype=np.unicode, encoding=encoding, index_col=False,
                    low_memory=False, skipinitialspace=True)
            except pd.errors.EmptyDataError:
                yield iter([])

    @contextmanager
    def _io_adapter(self, fpath):
        """
        Yield an IO object and its encoding for the given file path.
        Reads from a zip file or folder.
        """
        if self.is_dir:
            with open(fpath, 'rb') as iowrapper:
                encoding = detect_encoding(iowrapper)
                iowrapper.seek(0)  # Rewind to the beginning of the file
                yield iowrapper, encoding
        else:
            with ZipFile(self.path) as zipreader:
                with zipreader.open(fpath, 'r') as zfile:
                    encoding = detect_encoding(zfile)
                with zipreader.open(fpath, 'r') as zfile:
                    with io.TextIOWrapper(zfile, encoding) as iowrapper:
                        yield iowrapper, encoding

    def _verify_zip_contents(self):
        """
        Verify that the folder does not contain multiple files
        of the same name. Load file paths into internal dictionary.
        """
        with ZipFile(self.path) as zipreader:
            for entry in zipreader.filelist:
                # ZipInfo.is_dir was added in Python 3.6
                # http://harp.pythonanywhere.com/python_doc/whatsnew/3.6.html
                # https://hg.python.org/cpython/rev/7fea2cebc604#l4.58
                if entry.filename[-1] == '/':
                    continue

                basename = os.path.basename(entry.filename)
                assert basename not in self.zmap, \
                    'More than one {} in zip'.format(basename)
                self.zmap[basename] = entry.filename

    def _verify_folder_contents(self):
        """
        Verify that the folder does not contain multiple files
        of the same name. Load file paths into internal dictionary.
        """
        for root, _subdirs, files in os.walk(self.path):
            for fname in files:
                basename = os.path.basename(fname)
                assert basename not in self.zmap, \
                    'More than one {} in folder'.format(basename)
                self.zmap[basename] = os.path.join(root, fname)


# No pruning or type coercion
class raw_feed(feed):
    def __init__(self, path):
        super(raw_feed, self).__init__(path, config=empty_config())
