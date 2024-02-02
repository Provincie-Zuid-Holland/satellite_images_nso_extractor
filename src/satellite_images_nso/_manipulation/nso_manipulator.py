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
from shapely.geometry import box

import satellite_images_nso.__lidar.ahn as ahn
from satellite_images_nso._index_channels.calculate_index_channels import (
    generate_ndvi_channel,
    generate_ndwi_channel,
    generate_red_edge_ndvi_channel,
)

"""
    This is a python class for making various manipulationg such as making crops .tif files, nvdi calculations and exporting to geopandas.

    @author: Michael de Winter.
"""


def __make_the_crop(load_shape, raster_path, raster_path_cropped, plot):
    """
    This crops the sattelite image with a chosen shape.

    TODO: Make this accept a object of geopandas or shapely and crs independant.
    @param load_schape: path to a geojson shape file.
    @param raster_path_wgs: path to the raster .tiff file.
    @param raster_path_cropped: path were the cropped raster will be stored.
    """
    geo_file = gpd.read_file(load_shape)
    src = rasterio.open(raster_path)
    print("raster path opened")
    # Change the crs to rijks driehoek, because all the satelliet images are in rijks driehoek
    if geo_file.crs != "epsg:28992":
        geo_file = geo_file.to_crs(epsg=28992)

    out_image, out_transform = rasterio.mask.mask(
        src, geo_file["geometry"], crop=True, filled=True
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
    print("convert to RD")

    src.close()
    with rasterio.open(raster_path_cropped, "w", **out_profile) as dest:
        dest.write(out_image)
        dest.close()

    if plot:
        print(
            "Plotting data for:"
            + raster_path_cropped
            + "-----------------------------------------------------"
        )
        # TODO: Make this optional to plot.
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
    return output_file_path


def get_ahn_data(ahn_input_file):
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


def transform_vector_to_pixel_df(path_to_vector, add_ndvi_column=False):
    """
    Maps a rasterio satellite vector object to a geo pandas dataframe per pixel.
    With the corresponding x and y coordinates and NVDI.


    @param path_to_vector: path to a vector which be read with rasterio.
    @param add_ndvi_column: WWether or not to add a ndvi column to the pandas dataframe.
    @return pandas dataframe: with x and y coordinates in epsg:4326
    """

    gpf = ""

    src = rasterio.open(path_to_vector)
    crs = src.crs

    # create 1D coordinate arrays (coordinates of the pixel center)
    xmin, ymax = np.around(src.xy(0.00, 0.00), 9)  # src.xy(0, 0)
    xmax, ymin = np.around(
        src.xy(src.height - 1, src.width - 1), 9
    )  # src.xy(src.width-1, src.height-1)
    x = np.linspace(xmin, xmax, src.width)
    y = np.linspace(ymax, ymin, src.height)  # max -> min so coords are top -> bottom

    # create 2D arrays
    xs, ys = np.meshgrid(x, y)
    blue = src.read(1)
    green = src.read(2)
    red = src.read(3)
    nir = src.read(4)

    # Apply NoData mask
    mask = src.read_masks(1) > 0
    xs, ys, blue, green, red, nir = (
        xs[mask],
        ys[mask],
        blue[mask],
        green[mask],
        red[mask],
        nir[mask],
    )

    data = {
        "X": pd.Series(xs.ravel()),
        "Y": pd.Series(ys.ravel()),
        "blue": pd.Series(blue.ravel()),
        "green": pd.Series(green.ravel()),
        "red": pd.Series(red.ravel()),
        "nir": pd.Series(nir.ravel()),
    }

    df = pd.DataFrame(data=data)
    geometry = gpd.points_from_xy(df.X, df.Y)

    if add_ndvi_column == True:
        df["ndvi"] = calculate_nvdi.normalized_diff(
            src.read()[3][mask], src.read()[2][mask]
        )
        df = df[["blue", "green", "red", "nir", "ndvi", "X", "Y"]]
    else:
        df = df[["blue", "green", "red", "nir", "X", "Y"]]

    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    src.close()

    return gdf


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


def __calculate_nvdi_function(raster_path_cropped, raster_path_nvdi, plot):
    """
    Function which calculates the NVDI index, used in a external package.

    @param raster_path_cropped: Path to the cropped file.
    @param raster_path_nvdi: path where the nvdi will be stored.
    """
    src = rasterio.open(raster_path_cropped)
    data_ndvi = calculate_nvdi.normalized_diff(src.read()[3], src.read()[2])
    data_ndvi.dump(raster_path_nvdi)

    src.close()
    return calculate_nvdi.make_ndvi_plot(raster_path_nvdi, raster_path_nvdi, plot)


def run(raster_path, load_shape, output_folder, plot):
    """
    Main run method, combines the cropping of the file based on the shape.

    @param raster_path: path to a raster file.
    @param load_shape: path the file that needs to be cropped.
    @return: the path where the cropped file is stored or where the nvdi is stored.
    """
    raster_path_cropped_moved = ""

    print(f"cropping file {raster_path}")
    logging.info(f"cropping file {raster_path}")
    raster_path_cropped = raster_path.replace(
        ".tif",
        "_"
        + load_shape.split("/")[len(load_shape.split("/")) - 1].split(".")[0]
        + "_cropped.tif",
    )
    print("New cropped filename: " + raster_path_cropped)
    logging.info("New cropped filename: " + raster_path_cropped)
    __make_the_crop(load_shape, raster_path, raster_path_cropped, plot)
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
