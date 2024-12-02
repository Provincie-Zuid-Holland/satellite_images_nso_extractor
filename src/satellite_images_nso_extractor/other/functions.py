import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from matplotlib import pyplot as plt
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.plot import show


def plot_tif(raster_path, save_fig_path=False, title=False):
    """
    Function for plotting a .tif file.
    Might be moved somewhere else.

    @param raster_path: Path to a raster file
    """

    # Open the raster file
    with rasterio.open(raster_path) as src:
        # Stack the bands into a single numpy array
        rgb = np.dstack((np.clip(src.read()[2::-1], 0, 2200) / 2200))

    # Plot the RGB data
    plt.figure(figsize=(10, 10))
    plt.imshow(rgb)
    if title:
        plt.title(title)
    plt.axis("off")  # Turn off the axis

    if save_fig_path:
        # Save the plot as a PNG file
        plt.savefig(save_fig_path, bbox_inches="tight", pad_inches=0)
    plt.show()
    plt.close()


def download_file(url, output_path):
    # Local path where you want to save the downloaded zip file
    local_tiff_path = "/".join(output_path.split("/")[0:-1]) + "/" + url.split("/")[-1]

    # Send a GET request to the URL to download the zip file
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Write the content of the response (the zip file) to a local file
        with open(local_tiff_path, "wb") as file:
            file.write(response.content)

        print(f"file has been downloaded to {local_tiff_path}")
    else:
        print("Failed to download file:", response.status_code)


def crop_tif_with_geojson(tif_path, geojson_path, output_path):
    try:
        # Open the GeoTIFF file
        with rasterio.open(tif_path) as src:
            # Read the GeoJSON file
            with open(geojson_path, "r") as geojson_file:
                geojson_data = gpd.read_file(geojson_file)
                geojson_data = geojson_data.set_crs("EPSG:4326").to_crs("EPSG:28992")

                # Extract the geometry from the GeoJSON
                geom = geojson_data.geometry.values[0]

                # Perform the crop operation
                out_image, out_transform = mask(src, [geom], crop=True)
                out_meta = src.meta.copy()

                # Update the metadata for the cropped image
                out_meta.update(
                    {
                        "driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform,
                    }
                )

                # Write the cropped image to a new GeoTIFF file
                with rasterio.open(output_path, "w", **out_meta) as dest:
                    dest.write(out_image)

                print(f"Cropped GeoTIFF saved to {output_path}")
    except Exception as e:
        print(f"Error cropping GeoTIFF: {e}")


def merge_tif_files(tiff_lst, out_fp):
    """
    Function for merging .tif files into one .tif file.
    Good for first downloading a wider region for different shapes, cropping them for each  shapes and then merging them again with this function.

    @oaram tiff_lst: A python list of .tif files to be merged.
    @param out_fp: The .tif file to write to.
    """
    src_files_to_mosaic = []
    for tiff in tiff_lst:
        src = rasterio.open(tiff)
        src_files_to_mosaic.append(src)
        src.close()

    # Merge
    mosaic, out_trans = merge(src_files_to_mosaic)

    # Copy the metadata
    out_meta = src.meta.copy()

    # Update the metadata
    out_meta.update(
        {
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "crs": "+proj=utm +zone=35 +ellps=GRS80 +units=m +no_defs",
        }
    )

    # Write the mosaic raster to disk
    with rasterio.open(out_fp, "w", **out_meta) as dest:
        dest.write(mosaic)
        dest.close()


def plot_tif_file(path_to_tif_file):
    """
    Plot a .tif file.

    @param path_to_tif_file: path to the tif file.
    """
    src = rasterio.open(path_to_tif_file)
    plot_out_image = (
        np.clip(src.read()[2::-1], 0, 2200) / 2200
    )  # out_image[2::-1] selects the first three items, reversed

    plt.figure(figsize=(10, 10))
    rasterio.plot.show(plot_out_image, transform=src.transform)

    src.close()


def switch_crs(list_coor_x, list_coor_y, crs_from, crs_to):
    """
    This function changes the crs of a given list of coordinates.

    @param list_coor_x: A list of X coordinates.
    @param list_coor_y: A list of Y coordinates.
    @param crs_from: the current crs the coordinates are in.
    @param crs_to: the crs with the coordinates have to be coverted to.
    @return gdf: A geopandas dataframe with the coordinates in them.
    """

    df = pd.DataFrame(
        {"Latitude_orginal": list_coor_x, "Longitude_orginal": list_coor_y}
    )

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.Longitude_orginal, df.Latitude_orginal)
    )
    gdf = gdf.set_crs(crs_from, allow_override=True)
    gdf = gdf.to_crs(epsg=crs_to)

    return gdf


def all_true(arr):
    for val in arr:
        if not val:
            return False
    return True


def all_false(arr):
    for val in arr:
        if val:
            return False
    return True


def download_file(url, output_path):
    # Local path where you want to save the downloaded zip file
    local_tiff_path = output_path + "/" + url.split("/")[-1]

    # Send a GET request to the URL to download the zip file
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Write the content of the response (the zip file) to a local file
        with open(local_tiff_path, "wb") as file:
            file.write(response.content)

        print(f"file has been downloaded to {local_tiff_path}")
    else:
        print("Failed to download file:", response.status_code)
