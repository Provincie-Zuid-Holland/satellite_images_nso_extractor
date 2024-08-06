import numpy as np
import rasterio
from rasterio.plot import show
from matplotlib import pyplot as plt
import requests
import geopandas as gpd
from rasterio.mask import mask


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
