from collections import defaultdict

import click
import numpy as np
import pandas as pd
from tqdm import tqdm

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
    feed = mkfeed(infile, config=_read_config())
    outfeed = mkfeed(infile, config=_write_config())

    click.echo('Read trips.txt')
    feed.trips

    click.echo('Read stop_times.txt')
    feed.stop_times

    click.echo('Read stops.txt')
    feed.stops

    click.echo('Read shapes')
    feed.shapes

    click.echo('Prepare row alignments for writing')
    feed.stop_times[ALIGNMENT_COL] = feed.stop_times.index
    outfeed.stop_times[ALIGNMENT_COL] = outfeed.stop_times.index

    click.echo('Sort and group shapes')
    shapes = (feed.shapes
                  .sort_values('shape_pt_sequence')
                  .groupby('shape_id'))

    click.echo('Merge, sort, and group observations')
    trips = (feed.stop_times
                 .merge(feed.trips, sort=False)
                 .merge(feed.stops, sort=False)
                 .sort_values('stop_sequence')
                 .groupby('trip_id'))

    candidates = {}
    for shape_id, points in tqdm(shapes, desc='Prune and cache HMM states'):
        shape_lons = points.shape_pt_lon.values
        shape_lats = points.shape_pt_lat.values
        if shape_lons.shape[0] < 2:
            continue
        if pd.isnull(shape_lons).any() or pd.isnull(shape_lats).any():
            continue
        candidates[shape_id] = CandidateCache(shape_lons, shape_lats)

    observations = {}
    row_alignments = defaultdict(list)
    for trip_id, obs in tqdm(trips, desc='Prune and cache HMM observations'):
        stop_lons = obs.stop_lon.values
        stop_lats = obs.stop_lat.values
        shape_id = obs.iloc[0].shape_id
        stop_ids = tuple(obs.stop_id)
        if obs.shape[0] < 2:
            continue
        if shape_id not in candidates:
            continue
        if pd.isnull(stop_lons).any() or pd.isnull(stop_lats).any():
            continue
        if stop_ids not in observations:
            observations[stop_ids] = ObservationCache(stop_lons, stop_lats)
        row_alignments[shape_id, stop_ids].append(np.array(obs[ALIGNMENT_COL]))

    if not any(row_alignments):
        click.echo('No opportunities to generate shape_dist_traveled.')
        return

    distances = np.full(feed.stop_times.shape[0], np.nan)
    for (shape_id, stop_ids), indexes in tqdm(row_alignments.items(),
                                              total=len(row_alignments),
                                              desc='Calculating distances'):
        measure = MeasureCache(observations[stop_ids], candidates[shape_id])

        try:
            dists = np.around(_shape_dist_traveled(measure))
        except NoPathError:
            dists = np.nan

        for index in indexes:
            distances[index] = dists

    click.echo('Update shape_dist_traveled values')
    outfeed.stop_times.set_index(ALIGNMENT_COL, inplace=True)
    outfeed.stop_times['shape_dist_traveled'] = np.int32(distances)
    outfeed.stop_times.reset_index(inplace=True)
    outfeed.stop_times.drop(ALIGNMENT_COL, axis=1, inplace=True)

    click.echo('Write feed to disk')
    write_feed_dangerously(outfeed, outfile, nodes=feed.zmap.keys())

    click.echo('Done!')


def _read_config():
    # Don't do any pruning - preserve the files as much as possible.
    config = default_config()
    config.remove_edges_from(list(config.edges()))
    return config


def _write_config():
    # Don't apply any conversions to the data so we
    # can safely write it back to a new feed.
    return remove_node_attributes(_read_config(), 'converters')
