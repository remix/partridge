from typing import Dict, List

import pandas as pd

try:
    import geopandas as gpd
    from shapely.geometry import LineString, Point
except ImportError as impexc:
    print(impexc)
    print("You must install GeoPandas to use this module.")
    raise


DEFAULT_CRS = "EPSG:4326"


def build_shapes(df: pd.DataFrame) -> gpd.GeoDataFrame:
    if df.empty:
        return gpd.GeoDataFrame({"shape_id": [], "geometry": []}, crs=DEFAULT_CRS)

    data: Dict[str, List] = {"shape_id": [], "geometry": []}
    for shape_id, shape in df.sort_values("shape_pt_sequence").groupby("shape_id"):
        data["shape_id"].append(shape_id)
        data["geometry"].append(
            LineString(list(zip(shape.shape_pt_lon, shape.shape_pt_lat)))
        )

    return gpd.GeoDataFrame(data, crs=DEFAULT_CRS)


def build_stops(df: pd.DataFrame) -> gpd.GeoDataFrame:
    if df.empty:
        return gpd.GeoDataFrame(df, geometry=[], crs=DEFAULT_CRS)

    df = gpd.GeoDataFrame(df, crs=DEFAULT_CRS, geometry=gpd.points_from_xy(df.stop_lon,df.stop_lat))
    df.drop(["stop_lon", "stop_lat"], axis=1, inplace=True)

    return df
