import logging
import shutil
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import tqdm
from matplotlib import pyplot as plt
from rasterio.plot import show
from rasterio.warp import (
    Resampling,
    calculate_default_transform,
    reproject,
    transform_geom,
)
from shapely.geometry import box, Polygon
from satellite_images_nso._index_channels.calculate_index_channels import (
    generate_ndvi_channel,
    generate_ndwi_channel,
    generate_red_edge_ndvi_channel,
)
from shapely.geometry import mapping
import os

"""
    This is a python class for making various manipulationg such as making crops .tif files, nvdi calculations and exporting to geopandas.

    @author: Michael de Winter, Pieter Kouyzer
"""


def __make_the_crop(
    coordinates, raster_path, raster_path_cropped, buffered_georegion, plot
):
    """
    This crops the satellite image with a chosen shape.

    TODO: Make this accept a object of geopandas or shapely and crs independent.
    @param coordinates: Coordinates of the polygon to make the crop on.
    @param raster_path: path to the raster .tiff file.
    @param raster_path_cropped: path were the cropped raster will be stored.
    @param plot: Plot the results true or false
    """

    # For polygons.
    if not buffered_georegion:
        geometry = [Polygon(coords) for coords in coordinates]

    # For multipolygons.
    elif buffered_georegion:
        print("Cropping multipolygons")
        geometry = []
        for x in range(len(coordinates)):
            geometry.append(Polygon(coordinates[x][0]))

    # Change the crs to rijks driehoek, because all the satelliet images are in rijks driehoek
    agdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326").to_crs(epsg=28992)
    area_to_crop = agdf["geometry"]

    with rasterio.open(raster_path) as src:
        print("raster path opened")

        out_image, out_transform = rasterio.mask.mask(
            src, area_to_crop, crop=True, filled=True
        )
        out_profile = src.profile

        out_profile.update(
            {
                "driver": "GTiff",
                "interleave": "band",
                "tiled": True,
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            }
        )

        # WARNING: we only assume Superview or PNEO satellites here! Change for your specific satellite
        if src.count == 4:
            print("Assuming Superview Satellite columns")
            descriptions = ("r", "g", "b", "i")
        elif src.count == 6:
            print("Assuming PNEO Satellite columns")
            descriptions = ("r", "g", "b", "n", "e", "d")
    print("convert to RD")

    try:
        with rasterio.open(raster_path_cropped, "w", **out_profile) as dest:
            dest.write(out_image)
            dest.descriptions = descriptions
            dest.close()
    except:
        print("Error on making descriptions")
        with rasterio.open(raster_path_cropped, "w", **out_profile) as dest:
            dest.write(out_image)
            dest.close()

    if plot:
        print(
            "Plotting data for:"
            + raster_path_cropped
            + "-----------------------------------------------------"
        )
        src = rasterio.open(raster_path_cropped)
        plot_out_image = (
            np.clip(src.read()[2::-1], 0, 2200) / 2200
        )  # out_image[2::-1] selects the first three items, reversed

        plt.figure(figsize=(10, 10))
        rasterio.plot.show(plot_out_image, transform=src.transform)
        logging.info(f"Plotted cropped image {raster_path_cropped}")
        src.close()


def add_index_channels(tif_input_file: str, channel_types: list):
    """
    Add various index channels to a .tif file.

    @param tif_input_file: Path to a .tif file.
    @param channel_types: Valid channel_types are: ["ndvi", "re_ndvi", "ndwi"]
    """
    if len(channel_types) == 0:
        return tif_input_file

    file_to = tif_input_file
    for channel_type in channel_types:
        if channel_type not in ["ndvi", "re_ndvi", "ndwi"]:
            raise ValueError(f"Unknown channel type: {channel_type}")
        file_to = file_to.replace(".tif", f"_{channel_type}.tif")

    with rasterio.open(tif_input_file, "r") as dataset:
        profile = dataset.profile
        profile.update(count=dataset.count + len(channel_types))
        descriptions = dataset.descriptions + tuple(channel_types)
        index_channels = []

        for channel_type in channel_types:
            if channel_type == "ndvi":
                index_channels += [generate_ndvi_channel(dataset)]
            if channel_type == "re_ndvi":
                index_channels += [generate_red_edge_ndvi_channel(dataset)]
            if channel_type == "ndwi":
                index_channels += [generate_ndwi_channel(dataset)]
            print(f"Done with calculating {channel_type} channel")

    with rasterio.open(file_to, "w", **profile) as output_dataset:
        print(f"Saving to {file_to}")
        with rasterio.open(tif_input_file, "r") as dataset:
            for band in range(1, dataset.count + 1):
                output_dataset.write_band(band, dataset.read(band))
        for i in range(0, len(index_channels)):
            output_dataset.write_band(dataset.count + 1 + i, index_channels[i])
        output_dataset.descriptions = descriptions

    os.remove(tif_input_file)
    return file_to


def add_height(tif_input_file, height_tif_file):
    """

    Adds height(From a lidar data source) and Normalized difference vegetation index (NDVI) as extra bands to a .tif file.

    Exports a new .tif file with _ndvi_height.tif behind it's original file name.

    @param tif_input_file: The tif file where 2 extra bands need to be added.
    @param height_tif_file: The tif file in 2d which shall be added to the tif input file.
    """
    print("Adding height to tif file")
    output_file_path = tif_input_file.replace(".tif", "_height.tif")

    with rasterio.open(tif_input_file, "r") as input_src:
        input_res_x = input_src.res[0]
        crop_window = box(*input_src.bounds)
        profile = input_src.profile
        profile.update(count=profile["count"] + 1)
        descriptions = input_src.descriptions + ("height",)

    with rasterio.open(height_tif_file, "r") as height_src:
        height_res_x = height_src.res[0]

        scale = height_res_x / input_res_x

        scaled_transform = rasterio.Affine(
            height_src.transform.a / scale,
            height_src.transform.b,
            height_src.transform.c,
            height_src.transform.d,
            height_src.transform.e / scale,
            height_src.transform.f,
        )
        scaled_profile = height_src.profile
        scaled_profile.update(
            transform=scaled_transform,
            driver="GTiff",
            height=height_src.height * scale,
            width=height_src.width * scale,
            crs=height_src.crs,
        )
        scaled_data = height_src.read(
            out_shape=(
                int(height_src.count),
                int(height_src.width * scale),
                int(height_src.height * scale),
            ),
            resampling=Resampling.nearest,
        )

    with rasterio.open(output_file_path, "w", **scaled_profile) as destination:
        destination.write(scaled_data)

    with rasterio.open(output_file_path, "r") as destination:
        masked_height, _ = rasterio.mask.mask(destination, [crop_window], crop=True)

    with rasterio.open(output_file_path, "w", **profile) as destination:
        with rasterio.open(tif_input_file, "r") as input_src:
            for i in range(1, profile["count"]):
                destination.write_band(i, input_src.read(i))
        destination.write_band(profile["count"], masked_height.squeeze())
        destination.descriptions = descriptions
    return output_file_path


def get_ahn_data(ahn_input_file):
    """
    This function returns height data from a ahn file.

    @param ahn_input_file
    """
    inds = rasterio.open(ahn_input_file, "r")
    vegetation_height_data = inds.read(1)
    vegetation_height_transform = inds.meta["transform"]

    inds.close()
    return vegetation_height_data, vegetation_height_transform


def generate_vegetation_height_channel(
    vegetation_height_data,
    vegetation_height_transform,
    target_transform,
    target_width,
    target_height,
):
    """
    Function to convert a .tif, which was created from a .laz file, into a band which can be used in a raster file with other bands.

    @param vegetation_height_data: numpy array from the ahn .tif file.
    @param vegetation_height_transform: transform from the ahn .tif meta data.
    @param target_transform: transform from the satellite .tif meta data.
    @param target_width: The width from the satellite .tif file.
    @param target_height: The height from the satellite .tif file.

    @return a ndvi channel
    """
    print("Generating vegetation height channel...")
    channel = np.array([[0] * target_width] * target_height, dtype=np.uint8)
    src_height, src_width = (
        vegetation_height_data.shape[0],
        vegetation_height_data.shape[1],
    )
    for y in tqdm.tqdm(range(target_height)):
        for x in range(target_width):
            rd_x, rd_y = rasterio.transform.xy(target_transform, y, x)
            vh_y, vh_x = rasterio.transform.rowcol(
                vegetation_height_transform, rd_x, rd_y
            )
            if vh_x < 0 or vh_x >= src_width or vh_y < 0 or vh_y >= src_height:
                continue
            # print(rd_x, rd_y, x, y, vh_x, vh_y)
            channel[y][x] = vegetation_height_data[vh_y][vh_x]
    return channel


def move_tiff(raster_path_cropped, raster_path_cropped_moved):
    """
    Moves cropped tiff file to the main folder.

    @param raster_path_cropped: path to the cropped tiff file
    @param raster_path_cropped_moved: path to be moved to

    """
    try:
        shutil.move(raster_path_cropped, raster_path_cropped_moved)
        logging.info(f"Moving tiff file to {raster_path_cropped_moved}")
    except:
        logging.error(f"Failed to move tiff to {raster_path_cropped_moved}")


def run(raster_path, coordinates, region_name, output_folder, buffered_georegion, plot):
    """
    Main run method, combines the cropping of the file based on the shape.

    @param raster_path: path to a raster file.
    @param coordinates: coordinates from a polygon to crop on.
    @param region_name: the region name of the cropped area to be saved in the file name.
    @param output_folder: Which output folder to store the .tif file.
    @param plot: Whether or not to plot the cropped image.
    @return: the path where the cropped file is stored or where the nvdi is stored.
    """
    raster_path_cropped_moved = ""

    print(f"cropping file {raster_path}")
    logging.info(f"cropping file {raster_path}")
    raster_path_cropped = raster_path.replace(
        ".tif",
        "_" + region_name + "_cropped.tif",
    )
    print("New cropped filename: " + raster_path_cropped)
    logging.info("New cropped filename: " + raster_path_cropped)
    __make_the_crop(
        coordinates, raster_path, raster_path_cropped, buffered_georegion, plot
    )
    print(f"finished cropping {raster_path}")
    logging.info(f"Finished cropping file {raster_path}")
    # Path fix and move.
    raster_path_cropped = raster_path_cropped.replace("\\", "/")
    raster_path_cropped_moved = (
        output_folder
        + "/"
        + raster_path_cropped.split("/")[len(raster_path_cropped.split("/")) - 1]
    )

    move_tiff(raster_path_cropped, raster_path_cropped_moved)

    return raster_path_cropped_moved
