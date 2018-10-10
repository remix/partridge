from contextlib import contextmanager
import io
import os
from threading import RLock
from zipfile import ZipFile

import networkx as nx
import numpy as np
import pandas as pd

from .config import default_config, empty_config
from .utilities import empty_df, detect_encoding, setwrap


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
        self._prepare()

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
                df = self._get(filename)
                self._cache[filename] = df
            return df

    def _get(self, filename):
        df = self._read_file(filename)
        self._apply_view(df, filename)
        self._apply_dependency_filters(df, filename)
        self._convert_types(df, filename)
        return df.reset_index(drop=True)

    def _read_file(self, filename):
        """
        Read CSV into a DataFrame
        """
        path = self._pathmap.get(filename)
        node = self._config.nodes.get(filename, {})
        columns = node.get("required_columns", [])

        # If the file isn't in the zip, return an empty DataFrame.
        if path is None:
            return empty_df(columns)

        with open(path, "rb") as f:
            encoding = detect_encoding(f)

        try:
            df = pd.read_csv(
                path,
                dtype=np.unicode,
                encoding=encoding,
                index_col=False,
                low_memory=False,
            )
        except pd.errors.EmptyDataError:
            return empty_df(columns)
        finally:
            if self._delete_after_reading:
                os.unlink(path)

        # Strip leading/trailing whitespace from column names
        df.rename(columns=lambda x: x.strip(), inplace=True)

        if not df.empty:
            # Strip leading/trailing whitespace from column values
            for col in df.columns:
                df[col] = df[col].str.strip()

        return df

    def _apply_view(self, df, filename):
        """
        Apply view filters
        """
        view = self._view.get(filename)
        if view is None or df.empty:
            return

        keep = df.index
        for col, values in view.items():
            # If applicable, filter this dataframe by the given set of values
            if col in df.columns:
                mask = df[col].isin(setwrap(values))
                keep = keep.intersection(df[mask].index)

        drop = df.index.difference(keep)
        df.drop(drop, inplace=True)

    def _apply_dependency_filters(self, df, filename):
        """
        Depth-first search through the dependency graph
        and prune dependent DataFrames along the way.
        """
        out_edges = self._config.out_edges(filename, data=True)
        if not out_edges or df.empty:
            return

        keep = df.index
        for _, depfile, data in out_edges:
            # Read the filtered, cached file dependency
            depdf = self.get(depfile)
            for deps in data.get("dependencies", []):
                col = deps[filename]
                depcol = deps[depfile]
                # If applicable, prune this dataframe by the other
                if col in df.columns and depcol in depdf.columns:
                    mask = df[col].isin(depdf[depcol])
                    keep = keep.intersection(df[mask].index)

        drop = df.index.difference(keep)
        df.drop(drop, inplace=True)

    def _convert_types(self, df, filename):
        """
        Apply type conversions
        """
        converters = self._config.nodes.get(filename, {}).get("converters")
        if converters is None or df.empty:
            return

        for col in df.columns:
            if col in converters:
                vfunc = converters[col]
                df[col] = vfunc(df[col])

    def _prepare(self):
        """
        Verify that the folder does not contain multiple files
        of the same name. Load file paths into internal dictionary.
        Initialize a reentrant lock for synchronizing reads of each file.
        """
        for root, _subdirs, files in os.walk(self._path):
            for fname in files:
                basename = os.path.basename(fname)
                if basename in self._pathmap:
                    raise ValueError("More than one {} in folder".format(basename))
                self._pathmap[basename] = os.path.join(root, fname)
                self._locks[basename] = RLock()
