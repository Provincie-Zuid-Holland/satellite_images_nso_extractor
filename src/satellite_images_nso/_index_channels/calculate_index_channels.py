import logging

import earthpy.plot as ep
import geopandas as gpd
import numpy as np
import pandas as pd
import tqdm
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from rasterio.io import DatasetReader

"""
    This class is used for various NVDI calculations.

    For more information check:
    https://en.wikipedia.org/wiki/Enhanced_vegetation_index

"""


def aggregate_ndvi_habitat(ndvi_geo_df: gpd.geodataframe.GeoDataFrame) -> pd.Series:
    """
    Calculate the aggregated statistics for NDVI
    @param ndvi_geo_df: geopandas dataframe, with ndvi values for each pixel
    @return pandas series: with 'mean', 'std', 'min', 'max', 'count' in the row axis
    """
    return ndvi_geo_df["ndvi"].agg(["mean", "std", "min", "max", "count"])


def generate_ndvi_channel(dataset: DatasetReader) -> np.array:
    """
    Generate ndvi channel from near infra red and red band.

    @param dataset: Rasterio DatasetReader with band 1 corresponding to red and band 4 to near infra red
    @return numpy array in the same shape as dataset with ndvi values
    """
    print("Generating NDVI channel...")
    # Original channels are uint16, so don't allow negative numbers, hence cast to int
    near_infra_red = dataset.read(4).astype(int)
    red = dataset.read(1).astype(int)
    ndvi = (near_infra_red - red) / (near_infra_red + red) * 100 + 100
    ndvi = np.nan_to_num(ndvi, 0)

    return ndvi


def generate_red_edge_ndvi_channel(dataset: DatasetReader) -> np.array:
    """
    Generate re_ndvi channel from red edge and red band.

    @param dataset: Rasterio DatasetReader with band 1 corresponding to red and band 5 to red edge
    @return numpy array in the same shape as dataset with re_ndvi values
    """
    print("Generating RE_NDVI channel...")
    # Original channels are uint16, so don't allow negative numbers, hence cast to int
    red_edge = dataset.read(5).astype(int)
    red = dataset.read(1).astype(int)
    re_ndvi = (red_edge - red) / (red_edge + red) * 100 + 100
    re_ndvi = np.nan_to_num(re_ndvi, 0)

    return re_ndvi


def generate_ndwi_channel(dataset: DatasetReader) -> np.array:
    """
    Generate ndwi channel from near infra red and green band.

    @param dataset: Rasterio DatasetReader with band 2 corresponding to green and band 4 to near infra red
    @return numpy array in the same shape as dataset with ndwi values
    """
    print("Generating NDWI channel...")
    # Original channels are uint16, so don't allow negative numbers, hence cast to int
    near_infra_red = dataset.read(4).astype(int)
    green = dataset.read(2).astype(int)
    ndwi = (green - near_infra_red) / (near_infra_red + green) * 100 + 100
    ndwi = np.nan_to_num(ndwi, 0)

    return ndwi
