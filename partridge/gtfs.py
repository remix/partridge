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
        path = self._pathmap.get(filename)
        config = self._config

        # Get config for node
        node = config.nodes.get(filename, {})
        columns = node.get("required_columns", [])
        converters = node.get("converters", {})

        # If the file isn't in the zip, return an empty DataFrame.
        if path is None:
            return empty_df(columns)

        # Gather the dependencies between this file and others
        file_dependencies = {
            depfile: data.get("dependencies", [])
            for _, depfile, data in config.out_edges(filename, data=True)
        }

        # Gather applicable view filter params
        view_filters = {
            # column name : set of strings
            col: setwrap(values)
            for col, values in self._view.get(filename, {}).items()
        }

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

        # Strip leading/trailing whitespace
        if not df.empty:
            for col in df.columns:
                df[col] = df[col].str.strip()

        # Apply view filters
        for col, values in view_filters.items():
            # If applicable, filter this dataframe by the
            # given set of values
            if col in df.columns:
                df = df[df[col].isin(values)]

        # Prune the dataframe
        for depfile, deplist in file_dependencies.items():
            # Read the filtered, pruned, and cached file dependency
            depdf = self.get(depfile)

            for deps in deplist:
                col = deps[filename]
                depcol = deps[depfile]

                # If applicable, prune this dataframe by the other
                if col in df.columns and depcol in depdf.columns:
                    df = df[df[col].isin(depdf[depcol])]

        if df.empty:
            return df

        # Apply type conversions
        for col in df.columns:
            if col in converters:
                vfunc = converters[col]
                df[col] = vfunc(df[col])

        return df

    def _prepare(self):
        """
        Verify that the folder does not contain multiple files
        of the same name. Load file paths into internal dictionary.
        Initialize a reentrant lock for synchronizing reads of each file.
        """
        for root, _subdirs, files in os.walk(self._path):
            for fname in files:
                basename = os.path.basename(fname)
                assert (
                    basename not in self._pathmap
                ), "More than one {} in folder".format(basename)
                self._pathmap[basename] = os.path.join(root, fname)
                self._locks[basename] = RLock()
