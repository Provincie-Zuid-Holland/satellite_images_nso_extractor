# Run this before deployments, with pytest!
#
# The following functionalities are tested:
# 1. Find download links for certain regions.
# 2. Cropping satellite images.
# 3. Adding new bands: NDVI, re_ndvi, NDWI.
# 4. Cloud detection.


import satellite_images_nso.api.nso_georegion as nso
from settings import nso_username, nso_password, path_geojson, output_path
import os

# Optional
from settings import (
    height_band_filepath,
    cloud_detection_model_path,
    links_must_contain,
)
import rasterio
from rasterio.plot import show
import satellite_images_nso._manipulation.nso_manipulator as nso_manipulator
import matplotlib.pyplot as plt

# the cloud_recognition.api needs to be imported from the natura2000 data science repo
from cloud_recognition.api import detect_clouds
import pickle
import numpy as np


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


def download_zip(url):
    # URL of the zip file you want to download
    zip_url = url

    # Local path where you want to save the downloaded zip file
    local_tiff_path = output_path + "/" + url.split("/")[-1]

    # Send a GET request to the URL to download the zip file
    response = requests.get(zip_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Write the content of the response (the zip file) to a local file
        with open(local_tiff_path, "wb") as file:
            file.write(response.content)

        print(f"zip file has been downloaded to {local_tiff_path}")
    else:
        print("Failed to download zip file:", response.status_code)


georegion = nso.nso_georegion(
    path_to_geojson=path_geojson,
    output_folder=output_path,
    username=nso_username,
    password=nso_password,
)
links = georegion.retrieve_download_links(max_diff=0.5, start_date="2011-01-01")


### Check if test data exists else download the data.

if not os.path.exists(
    output_path + "/20230513_104139_PNEO-03_1_1_30cm_RGBNED_12bit_PNEO.zip"
):
    download_zip(
        "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/Test_regions/20230513_104139_PNEO-03_1_1_30cm_RGBNED_12bit_PNEO.zip"
    )

if not os.path.exists(
    output_path + "/20191202_110523_SV1-04_SV_RD_11bit_RGBI_50cm.zip"
):
    download_zip(
        "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/Test_regions/20230513_104139_PNEO-03_1_1_30cm_RGBNED_12bit_PNEO.zip"
    )


### Link tests.


def test_found_links():

    assert len(links) > 0, "No links found error!"


def test_link_columns():
    # Columns to check for existence
    columns_to_check = [
        "link",
        "percentage_geojson",
        "missing_polygon",
        "covered_polygon",
    ]

    # Check if columns exist
    existing_columns = [col for col in columns_to_check if col in links.columns]

    assert len(existing_columns) == len(
        columns_to_check
    ), "Certain columns are not in the links"


def test_pneo_links():
    # Test if PNEO links are found
    pneo_links = links[links["resolution"] == "30cm"]
    pneo_links = pneo_links[pneo_links["link"].str.contains("RGBNED")]
    pneo_links = pneo_links.sort_values("percentage_geojson")

    assert len(pneo_links) > 0, "No PNEO links found error!"


def test_superview_links():
    # Example filter on resolution and bands
    superview_links = links[links["resolution"] == "50cm"]
    superview_links = superview_links[superview_links["link"].str.contains("RGBI")]
    superview_links = superview_links.sort_values("percentage_geojson")

    assert len(superview_links) > 0, "No  PNEO links found error!"


# Cropping tests


def pneo_polygon_crop():

    georegion = nso.nso_georegion(
        path_to_geojson="C:/repos/satellite-images-nso/input_data/Test_region.geojson",
        output_folder=output_path,
        username=nso_username,
        password=nso_password,
    )

    filepath = georegion.execute_link(
        "https://api.satellietdataportaal.nl/v1/download/30cm_RGBNED_12bit_PNEO/20230513_104139_PNEO-03_1_1",
        plot=False,
    )

    assert filepath, "No file has been downloaded or extracted for a polygon in PNEO!"

    # Remove the file for later tests
    os.remove(filepath)


def pneo_multiploygon_crop():

    georegion = nso.nso_georegion(
        path_to_geojson="C:/repos/satellite-images-nso/input_data/Test_multipolygon_region.geojson",
        output_folder=output_path,
        username=nso_username,
        password=nso_password,
    )

    filepath = georegion.execute_link(
        "https://api.satellietdataportaal.nl/v1/download/30cm_RGBNED_12bit_PNEO/20230513_104139_PNEO-03_1_1"
    )

    assert filepath, "No file has been downloaded or extracted for multiPolygons"

    # Remove the file for later tests
    os.remove(filepath)


# Channel adding tests.


def test_re_ndvi_pneo():
    # Test re_ndvi on PNEO coepelduynen and see if gives the best results.
    path_geojson = "C:/repos/satellite-images-nso/input_data/Test_region.geojson"
    output_path = "E:/data/test"

    georegion = nso.nso_georegion(
        path_to_geojson=path_geojson,
        output_folder=output_path,
        username=nso_username,
        password=nso_password,
    )

    filepath = georegion.execute_link(
        "https://api.satellietdataportaal.nl/v1/download/30cm_RGBNED_12bit_PNEO/20230513_104139_PNEO-03_1_1",
        add_red_edge_ndvi_band=True,
        plot=False,
    )

    # Open the TIFF image and display ndvi
    with rasterio.open(filepath) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert num_bands >= 7, "re_ndvi bands not added correctly"


def test_adding_ndwi_pneo():
    # Add the NDWI Channel
    filepath_ndwi = nso_manipulator.add_index_channels(
        "E:/data/test/20230513_104139_PNEO-03_1_1_30cm_RD_12bit_RGBNED_NoordwijkAanZee_Coepelduynen_cropped_Test_region_cropped_re_ndvi.tif",
        ["ndwi"],
    )

    # Open the TIFF image and display ndvi
    with rasterio.open(filepath_ndwi) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert num_bands >= 8, "ndwi bands not added correctly"

    os.remove(filepath_ndwi)


filepath = ""


def test_adding_ndvi_superview():
    filepath = georegion.execute_link(
        "https://api.satellietdataportaal.nl/v1/download/SV_RD_11bit_RGBI_50cm/20191202_110523_SV1-04",
        add_ndvi_band=True,
        plot=False,
    )

    # Open the TIFF image and display ndvi
    with rasterio.open(filepath) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert num_bands >= 5, "ndvi bands not added correctly"


def test_adding_ndwi_superview():
    # Add the NDWI Channel
    filepath_ndwi = nso_manipulator.add_index_channels(
        "E:/data/test/20191202_110523_SV1-04_50cm_RD_11bit_RGBI_NoordwijkAanZee_Coepelduynen_cropped_Test_region_cropped_ndvi.tif",
        ["ndwi"],
    )

    # Open the TIFF image and display ndvi
    with rasterio.open(filepath_ndwi) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert num_bands >= 6, "re_ndvi bands not added correctly"

    os.remove(filepath_ndwi)


# Test Cloud detection
def test_cloud_detection():

    path_to_model = pickle.load(
        open(
            "C:/repos/satellite-images-nso/models/cloud_detection_logistic_regression_v1.0.sav",
            "rb",
        )
    )
    cloud_pictures = [
        "E:/data/coepelduynen/20220514_114854_SV1-02_SV_RD_11bit_RGBI_50cm_Rijnsburg_natura2000_coepelduynen_cropped.tif",
        "E:/data/coepelduynen/20190302_105829_SV1-01_50cm_RD_11bit_RGBI_KatwijkAanZee_natura2000_coepelduynen_cropped.tif",
        "E:/data/coepelduynen/20191202_110525_SV1-04_50cm_RD_11bit_RGBI_KatwijkAanZee_natura2000_coepelduynen_cropped.tif",
    ]
    non_cloud_pictures = [
        "E:/data/coepelduynen/20230402_105321_PNEO-03_1_49_30cm_RD_12bit_RGBNED_Zoeterwoude_natura2000_coepelduynen_cropped.tif",
        "E:/data/coepelduynen/20230513_104139_PNEO-03_1_1_30cm_RD_12bit_RGBNED_NoordwijkAanZee_natura2000_coepelduynen_cropped.tif",
        "E:/data/coepelduynen/20220515_113347_SV1-02_SV_RD_11bit_RGBI_50cm_KatwijkAanZee_natura2000_coepelduynen_cropped.tif",
    ]

    positive_pictures = [
        detect_clouds(model=path_to_model, filepath=afile) for afile in cloud_pictures
    ]
    false_pictures = [
        detect_clouds(model=path_to_model, filepath=afile)
        for afile in non_cloud_pictures
    ]

    assert all_true(positive_pictures) and all_false(
        false_pictures
    ), "Not all values are True or False"