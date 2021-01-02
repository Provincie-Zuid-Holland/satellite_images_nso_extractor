import rasterio
from rasterio.plot import show
import geopandas as gpd
from pandas import DataFrame
import json
import shapely
import pyproj
from rasterio import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_geom
import sys
import os
import time
import re
import zipfile
import numpy as np
import satellite_images_nso._nvdi.calculate_nvdi as calculate_nvdi
from matplotlib import pyplot as plt
import re

"""
    This is a python class for making various manipulationg such as making cuts out of .tif files, nvdi calculations and exporting to geopandas.

    @author: Michael de Winter.
"""
def __make_the_cut(load_shape, raster_path, raster_path_cropped):
    """
        This cuts the sattelite image with a chosen shape.

        TODO: Make this accept a object of geopandas or shapely and crs independant.
        @param load_schape: path to a geojson shape file.
        @param raster_path_wgs: path to the raster .tiff file.
        @param raster_path_cropped: path were the cropped raster will be stored.
    """
    geo_file = gpd.read_file(load_shape)
    src = rasterio.open(raster_path)

    # Change the crs to rijks driehoek, because all the satelliet images are in rijks driehoek
    if geo_file.crs['init'] != 'epsg:28992':
        geo_file = geo_file.to_crs(epsg=28992)

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


def tranform_vector_to_pixel_df(path_to_vector):
    """
    Maps a rasterio satellite vector object to a geo pandas dataframe per pixel. 
    With the corresponding x and y coordinates and NVDI.


    @param path_to_vector: path to a vector which be read with rasterio.
    @return pandas dataframe: with x and y coordinates in epsg:4326
    """

    satellite_image = rasterio.open(path_to_vector)
    out_image = satellite_image.read()
 
    x_y_np =np.array(
              satellite_image.xy(
                  np.repeat( np.array(range(out_image.shape[1])), out_image.shape[2] ),
                  np.repeat( np.array(range(out_image.shape[2])), out_image.shape[1] )
              )
          ).T

    ndvi = calculate_nvdi.normalized_diff(out_image[3], out_image[2])                                          
    satelliet_df = DataFrame(data=[out_image[i].flatten() for i in range(out_image.shape[0])]).T              
    satelliet_df['ndvi'] = ndvi.flatten()
    satelliet_df['x'] = [row[0] for row in x_y_np]
    satelliet_df['y'] = [row[1] for row in x_y_np]
    satelliet_df.columns = ['blue', 'green', 'red', 'nir', 'ndvi', 'x', 'y']
    satelliet_df['geometry'] = gpd.points_from_xy(x=satelliet_df['x'], y=satelliet_df['y'])

    # The file name should contain the date and the name of the satellite and thus good information to store.
    split_file_name = path_to_vector.split("/")
    satelliet_df['filename'] = split_file_name[len(path_to_vector.split("/"))-1]
    return satelliet_df


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

def run(raster_path, load_shape, calculate_nvdi = True):
    """
        Main run method, combines the cutting of the file based on the shape and calculates the NVDI index.

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
