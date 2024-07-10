import numpy as np
import rasterio
from rasterio.plot import show
from matplotlib import pyplot as plt
import requests


def plot_tif(raster_path):
    """
    Function for plotting a .tif file.
    Might be moved somewhere else.

    @param raster_path: Path to a raster file
    """
    src = rasterio.open(raster_path)
    plot_out_image = (
        np.clip(src.read()[2::-1], 0, 2200) / 2200
    )  # out_image[2::-1] selects the first three items, reversed

    plt.figure(figsize=(10, 10))
    rasterio.plot.show(plot_out_image, transform=src.transform)

    src.close()


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
