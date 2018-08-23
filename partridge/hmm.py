import numpy as np
from rtree.index import Index
from shapely.geometry import LineString, Point

from partridge.geo import (
    bbox_from_point,
    great_circle_vec,
    pairwise_great_circle_vec,
)
from partridge.utilities import (
    cached_property,
    ddict,
    ddict2dict,
    dict_argmax,
    lru_cache,
    pairwise,
)


SQRT2PI = np.sqrt(2.0 * np.pi)

# Meticulously hand-tuned parameters!
SIGMA = 2.25
BETA = 18.797498


class NoPathError(RuntimeError):
    pass


def shape_dist_traveled(stop_lons, stop_lats, shape_lons, shape_lats,
                        threshold=200, sigma=SIGMA, beta=BETA):
    observations = ObservationCache(stop_lons, stop_lats)
    candidates = CandidateCache(shape_lons, shape_lats)
    measures = MeasureCache(observations, candidates)
    return _shape_dist_traveled(measures, threshold, sigma, beta)


def _shape_dist_traveled(measures, threshold=200, sigma=SIGMA, beta=BETA):
    init_probs, emiss_probs, trans_probs = \
        calculate_probabilities(measures, threshold, sigma, beta)
    path = sparse_viterbi(measures.N, init_probs, emiss_probs, trans_probs)
    return np.array([
        measures.shape_dist_traveled(stop_idx, seg_idx)
        for stop_idx, seg_idx in path
    ])


def calculate_probabilities(measures, threshold, sigma, beta):
    init_probs = ddict()
    emiss_probs = ddict()
    trans_probs = ddict()  # [to][from]

    #
    # Emission probabilities
    #
    for stop_idx in range(measures.N):
        for seg_idx, meters in measures.search(stop_idx, threshold):
            eprob = log_normal_distribution(meters, sigma)
            emiss_probs[stop_idx][seg_idx] = eprob

    #
    # Initial probabilities
    #
    for seg_idx in emiss_probs[0]:
        init_probs[0][seg_idx] = emiss_probs[0][seg_idx]

    #
    # Transition probabilities
    #
    for astop_idx, bstop_idx in pairwise(range(measures.N)):
        for aseg_idx in emiss_probs[astop_idx]:
            for bseg_idx in emiss_probs[bstop_idx]:
                if bseg_idx < aseg_idx:
                    continue

                from_dist = measures.shape_dist_traveled(astop_idx, aseg_idx)
                to_dist = measures.shape_dist_traveled(bstop_idx, bseg_idx)
                if not to_dist > from_dist:
                    # Skip if the projected points are out of order
                    continue

                shape_spacing = to_dist - from_dist
                stop_spacing = measures.stop_spacing[astop_idx]
                spacing_diff = np.abs(shape_spacing - stop_spacing)
                tprob = log_exponential_distribution(spacing_diff, beta)

                trans_probs[bstop_idx][bseg_idx][astop_idx][aseg_idx] = tprob

    init_probs = ddict2dict(init_probs)
    emiss_probs = ddict2dict(emiss_probs)
    trans_probs = ddict2dict(trans_probs)

    return init_probs, emiss_probs, trans_probs


def sparse_viterbi(N, init_probs, emiss_probs, trans_probs):
    '''
    Based on the implementation found here: https://git.io/fNQ6S
    ------------------------------------------------------------

    p = log probability
    i = stop index
    j = seg index

    init_probs[i][j] = p
    trans_probs[i1][j1][i0][j0] = p
    emiss_probs[i][j] = p
    '''
    P = [{} for _ in range(N)]
    preds = {}

    for seg_idx, eprob in emiss_probs[0].items():
        if seg_idx in init_probs[0]:
            iprob = init_probs[0][seg_idx]
            P[0][seg_idx] = iprob + eprob

    for bstop_idx in range(1, N):
        if bstop_idx not in emiss_probs:
            raise NoPathError('HMM break at observation {}'.format(bstop_idx))

        for bseg_idx, eprob in emiss_probs[bstop_idx].items():
            if (
                bstop_idx not in trans_probs or
                bseg_idx not in trans_probs[bstop_idx]
            ):
                continue

            for astop_idx, tprobs in trans_probs[bstop_idx][bseg_idx].items():
                for aseg_idx, tprob in tprobs.items():
                    if aseg_idx not in P[astop_idx]:
                        continue

                    curr_prob = P[astop_idx][aseg_idx]
                    prob = curr_prob + eprob + tprob

                    if (
                        bseg_idx not in P[bstop_idx] or
                        prob > P[bstop_idx][bseg_idx]
                    ):
                        P[bstop_idx][bseg_idx] = prob
                        preds[bstop_idx, bseg_idx] = (astop_idx, aseg_idx)

    last_stop_idx = N - 1

    # Find the most probable end state
    last_seg_idx = dict_argmax(P[-1])

    path = [(last_stop_idx, last_seg_idx)]

    # Reconstruct the most probable path the end state
    for i in range(last_stop_idx):
        if path[-1] not in preds:
            raise NoPathError('HMM break at observation {}'.format(N - i))
        path.append(preds[path[-1]])

    path.reverse()

    return path


class CandidateCache(object):
    def __init__(self, shape_lons, shape_lats):
        assert shape_lons.shape[0] > 1
        assert shape_lons.shape == shape_lats.shape
        self.shape_lons = shape_lons
        self.shape_lats = shape_lats

    @cached_property
    def spatial_index(self):
        return Index((i, s.bounds, None) for i, s in enumerate(self.segments))

    @cached_property
    def cumulative_dists(self):
        return np.cumsum(self.segment_dists)

    @cached_property
    def segment_dists(self):
        return pairwise_great_circle_vec(self.shape_lons, self.shape_lats)

    @cached_property
    def segments(self):
        return list(map(LineString, pairwise(zip(
            self.shape_lons, self.shape_lats))))


class ObservationCache(object):
    def __init__(self, stop_lons, stop_lats):
        assert stop_lons.shape[0] > 1
        assert stop_lons.shape == stop_lats.shape
        self.N = len(stop_lons)
        self.stop_lons = stop_lons
        self.stop_lats = stop_lats

    @cached_property
    def stops(self):
        return list(map(Point, zip(self.stop_lons, self.stop_lats)))

    @cached_property
    def stop_spacing(self):
        return pairwise_great_circle_vec(self.stop_lons, self.stop_lats)


class MeasureCache(object):
    def __init__(self, observations, candidates):
        self.N = observations.N

        self.stop_lons = observations.stop_lons
        self.stop_lats = observations.stop_lats
        self.shape_lons = candidates.shape_lons
        self.shape_lats = candidates.shape_lats

        self.stops = observations.stops
        self.segments = candidates.segments
        self.spatial_index = candidates.spatial_index

        self.stop_spacing = observations.stop_spacing
        self.cumulative_dists = candidates.cumulative_dists

    @lru_cache(maxsize=None)
    def search(self, stop_idx, threshold):
        point = self.stops[stop_idx]
        bounds = bbox_from_point(point.x, point.y, threshold)

        results = []
        for i in self.spatial_index.intersection(bounds):
            segment = self.segments[i]
            prjdist = segment.project(point, normalized=True)
            prjpoint = segment.interpolate(prjdist, normalized=True)
            dist_meters = great_circle_vec(
                point.x, point.y,
                prjpoint.x, prjpoint.y)

            if dist_meters <= threshold:
                results.append((i, dist_meters))

        return results

    @lru_cache(maxsize=None)
    def shape_dist_traveled(self, stop_idx, seg_idx):
        curr_dist = self.cumulative_dists[seg_idx]
        segment = self.segments[seg_idx]
        stop = self.stops[stop_idx]
        prjdist = segment.project(stop, normalized=True)
        prjpoint = segment.interpolate(prjdist, normalized=True)
        dist = great_circle_vec(stop.x, stop.y, prjpoint.x, prjpoint.y)
        return curr_dist + dist


def log_normal_distribution(x, sigma):
    return np.log(1.0 / (SQRT2PI * sigma)) + \
           (-0.5 * np.power(x / sigma, 2))


def log_exponential_distribution(x, beta):
    return np.log(1.0 / beta) - (x / beta)
