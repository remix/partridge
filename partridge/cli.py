from collections import defaultdict
from contextlib import contextmanager

import click
from halo import Halo
import numpy as np
import pandas as pd

from .config import default_config
from .gtfs import feed as mkfeed
from .hmm import (
    CandidateCache,
    ObservationCache,
    MeasureCache,
    NoPathError,
    _shape_dist_traveled,
)
from .utilities import remove_node_attributes
from .writers import write_feed_dangerously


ALIGNMENT_COL = '__odometer_idx__'


@click.group()
def cli():
    pass


@cli.command()
@click.argument('infile')
@click.argument('outfile')
def odometer(infile, outfile):
    '''
    A tool for measuring the distance traveled by a vehicle.
    '''
    notes = defaultdict(list)

    def print_notes_table():
        for key, ids in notes.items():
            click.echo('{}: {}'.format(key, len(ids)))

    feed = mkfeed(infile, config=_read_config())
    outfeed = mkfeed(infile, config=_write_config())

    for filename in ('trips.txt', 'stop_times.txt', 'stops.txt', 'shapes.txt'):
        with spinner('Load {}'.format(filename)):
            df = feed.get(filename)
        if df.empty:
            click.echo('Missing {}'.format(filename))
            click.echo('No opportunities to generate shape_dist_traveled.')
            return

    with spinner('Create temp index'):
        feed.stop_times[ALIGNMENT_COL] = feed.stop_times.index
        outfeed.stop_times[ALIGNMENT_COL] = outfeed.stop_times.index

    with spinner('Group shapes'):
        shapes = (feed.shapes
                      .sort_values('shape_pt_sequence')
                      .groupby('shape_id'))

    with spinner('Group trips'):
        trips = (feed.stop_times
                     .merge(feed.trips, sort=False)
                     .merge(feed.stops, sort=False)
                     .sort_values('stop_sequence')
                     .groupby('trip_id'))

    with spinner('Process shapes'):
        candidates = {}
        for shape_id, points in shapes:
            shape_lons = points.shape_pt_lon.values
            shape_lats = points.shape_pt_lat.values
            if shape_lons.shape[0] < 2:
                notes['Less than 2 shape points'].append(shape_id)
                continue
            if pd.isnull(shape_lons).any():
                notes['Null shape_lon'].append(shape_id)
                continue
            if pd.isnull(shape_lats).any():
                notes['Null shape_lat'].append(shape_id)
                continue
            candidates[shape_id] = CandidateCache(shape_lons, shape_lats)

    with spinner('Process trips'):
        observations = {}
        row_alignments = defaultdict(list)
        for trip_id, obs in trips:
            stop_lons = obs.stop_lon.values
            stop_lats = obs.stop_lat.values
            shape_id = obs.iloc[0].shape_id
            stop_ids = tuple(obs.stop_id)
            if obs.shape[0] < 2:
                notes['Less than 2 stop times'].append(trip_id)
                continue
            if shape_id not in candidates:
                notes['No shape'].append(trip_id)
                continue
            if pd.isnull(stop_lons).any():
                notes['Null stop_lon'].append(trip_id)
                continue
            if pd.isnull(stop_lats).any():
                notes['Null stop_lat'].append(trip_id)
                continue
            if stop_ids not in observations:
                observations[stop_ids] = ObservationCache(stop_lons, stop_lats)
            row_alignments[shape_id, stop_ids].append(
                np.array(obs[ALIGNMENT_COL]))

    if not any(row_alignments):
        click.echo('No opportunities to generate shape_dist_traveled.')
        print_notes_table()
        return

    with spinner('Calculate distances'):
        distances = np.full(feed.stop_times.shape[0], np.nan)
        for (shape_id, stop_ids), indexes in row_alignments.items():
            measure = MeasureCache(
                observations[stop_ids], candidates[shape_id])

            try:
                dists = np.around(_shape_dist_traveled(measure))
            except NoPathError:
                dists = np.nan

            for index in indexes:
                distances[index] = dists

    with spinner('Set distance column'):
        outfeed.stop_times.set_index(ALIGNMENT_COL, inplace=True)
        outfeed.stop_times['shape_dist_traveled'] = np.int32(distances)
        outfeed.stop_times.reset_index(inplace=True)
        outfeed.stop_times.drop(ALIGNMENT_COL, axis=1, inplace=True)

    with spinner('Write feed to disk'):
        write_feed_dangerously(outfeed, outfile, nodes=feed.zmap.keys())

    print_notes_table()


@contextmanager
def spinner(message):
    stream = click.get_text_stream('stdout')
    s = Halo(text=message, stream=stream)
    s.start()
    yield
    s.stop_and_persist(symbol='+')


def _read_config():
    # Don't do any pruning - preserve the files as much as possible.
    config = default_config()
    config.remove_edges_from(list(config.edges()))
    return config


def _write_config():
    # Don't apply any conversions to the data so we
    # can safely write it back to a new feed.
    return remove_node_attributes(_read_config(), 'converters')
