import rasterio
from rasterio.plot import show
import geopandas as gpd
import json
import shapely
import pyproj
from rasterio import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_geom
import sys
import os
import time
import re
import os
import zipfile
import numpy as np
import satellite_images_nso._nvdi.calculate_nvdi as calculate_nvdi
from matplotlib import pyplot as plt

"""
    This is a python class for making cuts out of .tif files easier.

    @author: Michael de Winter.
"""

def __getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them
    
        @param gdf: a geopandas data frame
    """
    return [json.loads(gdf.to_json())['features'][0]['geometry']['coordinates']]



def __make_the_cut(load_shape, raster_path, raster_path_cropped):
    """
        This cuts the sattelite image with a chosen shape.

        @param load_schape: path to the shape.
        @param raster_path_wgs: path to the raster wgs.
        @param raster_path_cropped: path were the cropped raster will be stored.
    """

    geo = gpd.read_file(load_shape)
    coords = __getFeatures(geo)
     
    src = rasterio.open(raster_path)
    
    if geo.crs['init'] != 'epsg:28992':
        geo = geo.to_crs(epsg=28992)

   out_image, out_transform = rasterio.mask.mask(src,geo_file['geometry'], crop=True)
   out_meta = src.meta

   out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})
    
    with rasterio.open(raster_path_cropped, "w", **out_meta) as dest:
            dest.write(out_image)
            dest.close()

    print("Plotting data for:"+raster_path_cropped+"-----------------------------------------------------")
    # TODO: Make this optional to plot.
    src = rasterio.open(raster_path_cropped)
    plot_out_image = np.clip(src.read()[2::-1],
                    0,2200)/2200 # out_image[2::-1] selects the first three items, reversed

    plt.figure(figsize=(10,10))
    rasterio.plot.show(plot_out_image,
          transform=src.transform)

def __calculate_nvdi_function(raster_path_cropped,raster_path_nvdi):
    """
        Function which calculates the NVDI index, used in a external package.

        @param raster_path_cropped: Path to the cropped file.
        @param raster_path_nvdi: path where the nvdi will be stored.
    """
    src = rasterio.open(raster_path_cropped)
    data_ndvi = calculate_nvdi.normalized_diff(src.read()[3], src.read()[2]) 
    data_ndvi.dump(raster_path_nvdi)
    
    return calculate_nvdi.make_ndvi_plot(raster_path_nvdi,raster_path_nvdi)


def run(raster_path,load_shape, calculate_nvdi = True):
    """
        Main run method.

        @param raster_path: path to a raster file.
        @param load_shape: path the file that needs to be cropped.
        @param calculate_nvdi: Wether or not to also to calculate the nvdi index.
        @return: the path where the cropped file is stored or where the nvdi is stored.
    """
    raster_path_cropped = raster_path.replace(".tif","_"+load_shape.split("/")[len(load_shape.split("/"))-1].split('.')[0]+"_cropped.tif")
    __make_the_cut(load_shape,raster_path,raster_path_cropped)

    if calculate_nvdi == True:
        raster_path_nvdi = raster_path.replace(".tif","_"+load_shape.split("/")[len(load_shape.split("/"))-1].split('.')[0]+"_cropped_nvdi")
        nvdi_output = __calculate_nvdi_function(raster_path_cropped,raster_path_nvdi)
        return raster_path_cropped, nvdi_output, raster_path_nvdi
    
