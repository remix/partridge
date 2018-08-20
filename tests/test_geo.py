import numpy as np
from partridge.geo import great_circle_vec, pairwise_great_circle_vec


def test_pairwise_great_circle_vec():
    lon1 = -74.034122
    lat1 = 40.717039
    lon2 = -74.035342
    lat2 = 40.716639

    expected = np.array([great_circle_vec(lon1, lat1, lon2, lat2)])

    lons = [lon1, lon2]
    lats = [lat1, lat2]

    actual = pairwise_great_circle_vec(lons, lats)

    assert expected == actual
