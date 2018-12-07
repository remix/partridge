import os
from threading import RLock

import numpy as np
import pandas as pd

from .config import default_config
from .utilities import detect_encoding, setwrap


def read_file(filename):
    return property(lambda feed: feed.get(filename))


class Feed(object):
    def __init__(self, path, view=None, config=None):
        self._path = path
        self._config = default_config() if config is None else config
        self._view = {} if view is None else view
        self._cache = {}
        self._pathmap = {}
        self._delete_after_reading = False
        self._shared_lock = RLock()
        self._locks = {}

        # Walk recursively through the directory
        for root, _subdirs, files in os.walk(self._path):
            for fname in files:
                basename = os.path.basename(fname)
                if basename in self._pathmap:
                    # Verify that the folder does not contain multiple files of the same name.
                    raise ValueError("More than one {} in folder".format(basename))
                # Index paths by their basename.
                self._pathmap[basename] = os.path.join(root, fname)
                # Build a lock for each file to synchronize reads.
                self._locks[basename] = RLock()

    agency = read_file("agency.txt")
    calendar = read_file("calendar.txt")
    calendar_dates = read_file("calendar_dates.txt")
    fare_attributes = read_file("fare_attributes.txt")
    fare_rules = read_file("fare_rules.txt")
    feed_info = read_file("feed_info.txt")
    frequencies = read_file("frequencies.txt")
    routes = read_file("routes.txt")
    shapes = read_file("shapes.txt")
    stops = read_file("stops.txt")
    stop_times = read_file("stop_times.txt")
    transfers = read_file("transfers.txt")
    trips = read_file("trips.txt")

    def get(self, filename):
        lock = self._locks.get(filename, self._shared_lock)
        with lock:
            df = self._cache.get(filename)
            if df is None:
                path = self.path(filename)
                view = self.view(filename)
                columns = self.required_columns(filename)
                dependencies = self.dependencies(filename)
                converters = self.converters(filename)
                df = read(path, view, columns)
                df = prune(self, filename, df, dependencies)
                convert_types(df, converters)
                self._cache[filename] = df.reset_index(drop=True)
            return self._cache[filename]

    def required_columns(self, filename):
        return self._config.nodes.get(filename, {}).get("required_columns", [])

    def converters(self, filename):
        return self._config.nodes.get(filename, {}).get("converters", {})

    def dependencies(self, filename):
        results = []
        for _, depf, data in self._config.out_edges(filename, data=True):
            deps = data.get("dependencies")
            if deps is None:
                msg = f"Edge missing `dependencies` attribute: {filename}->{depf}"
                raise ValueError(msg)
            results.append((depf, deps))
        return results

    def path(self, filename):
        return self._pathmap.get(filename)

    def view(self, filename):
        return self._view.get(filename, {})


def read(path, view, columns):
    if path is None or os.path.getsize(path) == 0:
        # The file is missing or empty. Return an empty
        # DataFrame containing any required columns.
        return empty_df(columns)

    df = read_csv(path)
    if df.empty:
        # The file has no rows. Return the DataFrame as-is.
        return df

    df = apply_view(df, view)
    if df.empty:
        # No rows are visible with this view. Return the DataFrame as-is.
        return df

    return df


def prune(feed, filename, df, dependencies):
    """
    Depth-first search through the dependency graph
    and prune dependent DataFrames along the way.
    """
    if not dependencies:
        return df

    keep = df.index
    for depfile, column_pairs in dependencies:
        # Read the filtered, cached file dependency
        depdf = feed.get(depfile)
        for deps in column_pairs:
            col = deps[filename]
            depcol = deps[depfile]
            # If applicable, prune this dataframe by the other
            if col in df.columns and depcol in depdf.columns:
                mask = df[col].isin(depdf[depcol])
                keep = keep.intersection(df[mask].index)

    drop = df.index.difference(keep)
    return df.drop(drop)


def convert_types(df, converters):
    """
    Apply type conversions
    """
    if df.empty:
        return

    for col, converter in converters.items():
        if col in df.columns:
            df[col] = converter(df[col])


def apply_view(df, view):
    """
    Apply view filters
    """
    if not view:
        return df

    keep = df.index
    for col, values in view.items():
        # If applicable, filter this dataframe by the given set of values
        if col in df.columns:
            mask = df[col].isin(setwrap(values))
            keep = keep.intersection(df[mask].index)

    drop = df.index.difference(keep)
    return df.drop(drop)


def read_csv(path):
    """
    Read CSV into a DataFrame
    """

    # If the file isn't in the zip, return an empty DataFrame.
    with open(path, "rb") as f:
        encoding = detect_encoding(f)

    df = pd.read_csv(path, dtype=np.unicode, encoding=encoding, index_col=False)

    # Strip leading/trailing whitespace from column names
    df.rename(columns=lambda x: x.strip(), inplace=True)

    if not df.empty:
        # Strip leading/trailing whitespace from column values
        for col in df.columns:
            df[col] = df[col].str.strip()

    return df


def empty_df(columns=None):
    columns = [] if columns is None else columns
    empty = {col: [] for col in columns}
    return pd.DataFrame(empty, columns=columns, dtype=np.unicode)
