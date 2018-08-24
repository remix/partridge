import numpy as np
from shapely.geometry import Point
import utm

from partridge.utilities import pairwise

EARTH_RADIUS_METERS = 6371009


class InsufficientCoordinateLength(Exception):
    pass

class UnequalCoordinateLengths(Exception):
    pass

def bbox_from_point(lon, lat, meters):
    easting, northing, zn, zl = utm.from_latlon(lat, lon)
    point = Point(easting, northing)
    bounds = point.buffer(meters).bounds
    minx, miny, maxx, maxy = bounds
    result = []
    for e, n in ((minx, miny), (maxx, maxy)):
        lat, lon = utm.to_latlon(e, n, zn, zl)
        result.append(lon)
        result.append(lat)
    return tuple(result)


def pairwise_great_circle_vec(lons, lats, earth_radius=EARTH_RADIUS_METERS):
    for l in [lats, lons]:
        if len(l) <= 1:
            raise InsufficientCoordinateLength(
                'Not enough coordinates to perform pairwise operation.')
    if not len(lats) == len(lons):
        raise UnequalCoordinateLengths(
            'Different counts of latitudes and longitudes')
    return great_circle_vec(
        lons[:-1], lats[:-1], lons[1:], lats[1:], earth_radius)


def great_circle_vec(lon1, lat1, lon2, lat2, earth_radius=EARTH_RADIUS_METERS):
    """
    Credit to Geoff Boeing and the OSMNX package: https://git.io/fNgVj.

    Vectorized function to calculate the great-circle distance between two
    points or between vectors of points, using haversine.
    Parameters
    ----------
    lon1 : float or array of float
    lat1 : float or array of float
    lon2 : float or array of float
    lat2 : float or array of float
    earth_radius : numeric
        radius of earth in units in which distance will be returned (default is
        meters)
    Returns
    -------
    distance : float or vector of floats
        distance or vector of distances from (lon1, lat1) to (lon2, lat2) in
        units of earth_radius
    """

    phi1 = np.deg2rad(lat1)
    phi2 = np.deg2rad(lat2)
    d_phi = phi2 - phi1

    theta1 = np.deg2rad(lon1)
    theta2 = np.deg2rad(lon2)
    d_theta = theta2 - theta1

    h = np.sin(d_phi / 2) ** 2 + \
        np.cos(phi1) * np.cos(phi2) * np.sin(d_theta / 2) ** 2
    h = np.minimum(1.0, h)  # protect against floating point errors

    arc = 2 * np.arcsin(np.sqrt(h))

    # return distance in units of earth_radius
    distance = arc * earth_radius
    return distance
