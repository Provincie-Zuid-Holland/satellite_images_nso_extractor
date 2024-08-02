# Run this before deployments, with pytest!
#
# The following functionalities are tested:
# 1. Find download links for certain regions.
# 2. Cropping satellite images.
# 3. Adding new bands: NDVI, re_ndvi, NDWI.
# 4. Cloud detection.
#
# In order for this test to run make sure to define the settings file with NSO username,NSO password, outputpath for storing .tif files, input data in the form of a test region and a path to a cloud detection model!!!!
#
# If error occur be sure to delete to unzip folder, which could lead to more errors!


import satellite_images_nso_extractor.api.nso_georegion as nso
from settings import (
    nso_username,
    nso_password,
    path_geojson,
    output_path,
    path_test_input_data,
    cloud_detection_model_path,
)
import os
import glob

import rasterio
from rasterio.plot import show
import satellite_images_nso_extractor._manipulation.nso_manipulator as nso_manipulator
import matplotlib.pyplot as plt

# the cloud_recognition.api needs to be imported from the natura2000 data science repo
from cloud_recognition.api import detect_clouds
import pickle
import numpy as np
import requests
import shutil


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


def download_file(url):

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


def remove_directories_in_folder(folder_path):
    try:
        # Iterate over all items in the folder
        for item in os.listdir(folder_path):
            # Join the folder path with the current item
            item_path = os.path.join(folder_path, item)

            # Check if the item is a directory
            if os.path.isdir(item_path):
                # Remove the directory and its contents
                shutil.rmtree(item_path)
                print(f"Directory '{item_path}' removed successfully.")
    except Exception as e:
        print(f"Error: {e}")


georegion = nso.nso_georegion(
    path_to_geojson=path_geojson,
    output_folder=output_path,
    username=nso_username,
    password=nso_password,
)
links = georegion.retrieve_download_links(max_diff=0.5, start_date="2011-01-01")


### Check if test data exists else download the test data.

if not os.path.exists(
    output_path + "/20230513_104139_PNEO-03_1_1_30cm_RGBNED_12bit_PNEO.zip"
):
    download_file(
        "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/Test_regions/20230513_104139_PNEO-03_1_1_30cm_RGBNED_12bit_PNEO.zip"
    )

if not os.path.exists(
    output_path + "/20191202_110523_SV1-04_SV_RD_11bit_RGBI_50cm.zip"
):
    download_file(
        "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/Test_regions/20230513_104139_PNEO-03_1_1_30cm_RGBNED_12bit_PNEO.zip"
    )


### Link tests.


def test_retrieve_download_links():

    assert len(links) > 0, "No links found error!"


def test_retrieve_download_links_columns():
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


def test_retrieve_download_links_pneo_links():
    # Test if PNEO links are found
    pneo_links = links[links["resolution"] == "30cm"]
    pneo_links = pneo_links[pneo_links["link"].str.contains("RGBNED")]
    pneo_links = pneo_links.sort_values("percentage_geojson")

    assert len(pneo_links) > 0, "No PNEO links found error!"


def test_retrieve_download_links_superview_links():
    # Example filter on resolution and bands
    superview_links = links[links["resolution"] == "50cm"]
    superview_links = superview_links[superview_links["link"].str.contains("RGBI")]
    superview_links = superview_links.sort_values("percentage_geojson")

    assert len(superview_links) > 0, "No  PNEO links found error!"


# Cropping tests


def pneo_polygon_crop():

    georegion = nso.nso_georegion(
        path_to_geojson=path_test_input_data + "Test_region.geojson",
        output_folder=output_path,
        username=nso_username,
        password=nso_password,
    )

    filepath = georegion.execute_link(
        "https://api.satellietdataportaal.nl/v1/download/30cm_RGBNED_12bit_PNEO/20230513_104139_PNEO-03_1_1",
        plot=False,
    )

    assert filepath, "No file has been downloaded or extracted for a polygon in PNEO!"


def pneo_multiploygon_crop():

    georegion = nso.nso_georegion(
        path_to_geojson=path_test_input_data + "Test_multipolygon_region.geojson",
        output_folder=output_path,
        username=nso_username,
        password=nso_password,
    )

    filepath = georegion.execute_link(
        "https://api.satellietdataportaal.nl/v1/download/30cm_RGBNED_12bit_PNEO/20230513_104139_PNEO-03_1_1"
    )

    assert filepath, "No file has been downloaded or extracted for multiPolygons"


# Clean up from crop tests.

[os.remove(file) for file in glob.glob(output_path + "/*.tif")]

remove_directories_in_folder(output_path)

# Channel adding tests.


def test_re_ndvi_pneo():
    # Test re_ndvi on PNEO coepelduynen and see if gives the best results.
    path_geojson = path_test_input_data + "Test_region.geojson"
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

        assert "re_ndvi" in src.descriptions, "re_ndvi bands not added correctly"


def test_adding_additional_ndwi_pneo():

    # Test re_ndvi on PNEO coepelduynen and see if gives the best results.
    path_geojson = path_test_input_data + "Test_region.geojson"
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

    # Add the NDWI Channel
    filepath_ndwi = nso_manipulator.add_index_channels(
        filepath,
        ["ndwi"],
    )

    # Open the TIFF image and display ndvi
    with rasterio.open(filepath_ndwi) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert "ndwi" in src.descriptions, "re_ndwi bands not added correctly"


def test_adding_ndvi_superview():

    # Test re_ndvi on PNEO coepelduynen and see if gives the best results.
    path_geojson = path_test_input_data + "Test_region.geojson"
    output_path = "E:/data/test"

    georegion = nso.nso_georegion(
        path_to_geojson=path_geojson,
        output_folder=output_path,
        username=nso_username,
        password=nso_password,
    )

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

        assert "ndvi" in src.descriptions, "ndvi bands not added correctly"


def test_adding_additional_ndwi_superview():

    # Test re_ndvi on PNEO coepelduynen and see if gives the best results.
    path_geojson = path_test_input_data + "Test_region.geojson"
    output_path = "E:/data/test"

    georegion = nso.nso_georegion(
        path_to_geojson=path_geojson,
        output_folder=output_path,
        username=nso_username,
        password=nso_password,
    )

    filepath = georegion.execute_link(
        "https://api.satellietdataportaal.nl/v1/download/SV_RD_11bit_RGBI_50cm/20191202_110523_SV1-04",
        add_ndvi_band=True,
        plot=False,
    )

    # Add the NDWI Channel
    filepath_ndwi = nso_manipulator.add_index_channels(
        filepath,
        ["ndwi"],
    )

    # Open the TIFF image and display ndvi
    with rasterio.open(filepath_ndwi) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert "ndwi" in src.descriptions, "ndwi band  not added correctly"


# Clean up from adding channels

[os.remove(file) for file in glob.glob(output_path + "/*.tif")]

remove_directories_in_folder(output_path)


# Test Cloud detection
def test_cloud_detection():

    path_to_model = pickle.load(
        open(
            cloud_detection_model_path,
            "rb",
        )
    )

    # TODO: Make smaller files for cloud detection.

    # Cloud pictures
    if not os.path.exists(
        output_path
        + "/20220514_114854_SV1-02_SV_RD_11bit_RGBI_50cm_Rijnsburg_natura2000_coepelduynen_cropped.tif"
    ):
        download_file(
            "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/coepelduynen/20220514_114854_SV1-02_SV_RD_11bit_RGBI_50cm_Rijnsburg_natura2000_coepelduynen_cropped.tif"
        )

    if not os.path.exists(
        output_path
        + "/20190302_105829_SV1-01_50cm_RD_11bit_RGBI_KatwijkAanZee_natura2000_coepelduynen_cropped.tif"
    ):
        download_file(
            "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/coepelduynen/20190302_105829_SV1-01_50cm_RD_11bit_RGBI_KatwijkAanZee_natura2000_coepelduynen_cropped.tif"
        )

    if not os.path.exists(
        output_path
        + "/20191202_110525_SV1-04_50cm_RD_11bit_RGBI_KatwijkAanZee_natura2000_coepelduynen_cropped.tif"
    ):
        download_file(
            "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/coepelduynen/20191202_110525_SV1-04_50cm_RD_11bit_RGBI_KatwijkAanZee_natura2000_coepelduynen_cropped.tif"
        )

    # Not cloud pictures
    if not os.path.exists(
        output_path
        + "/20230402_105321_PNEO-03_1_49_30cm_RD_12bit_RGBNED_Zoeterwoude_natura2000_coepelduynen_cropped_ndvi_asphalt_crop.tif"
    ):
        download_file(
            "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/coepelduynen/20230402_105321_PNEO-03_1_49_30cm_RD_12bit_RGBNED_Zoeterwoude_natura2000_coepelduynen_cropped_ndvi_asphalt_crop.tif"
        )

    if not os.path.exists(
        output_path
        + "/20230513_104139_PNEO-03_1_1_30cm_RD_12bit_RGBNED_NoordwijkAanZee_natura2000_coepelduynen_cropped_ndvi_re_ndvi_asphalt_crop.tif"
    ):
        download_file(
            "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/coepelduynen/20230513_104139_PNEO-03_1_1_30cm_RD_12bit_RGBNED_NoordwijkAanZee_natura2000_coepelduynen_cropped_ndvi_re_ndvi_asphalt_crop.tif"
        )

    if not os.path.exists(
        output_path
        + "/20220515_113347_SV1-02_SV_RD_11bit_RGBI_50cm_KatwijkAanZee_natura2000_coepelduynen_cropped.tif"
    ):
        download_file(
            "https://e34a505986aa74678a5a0e0f.blob.core.windows.net/satellite-images-nso/coepelduynen/20220515_113347_SV1-02_SV_RD_11bit_RGBI_50cm_KatwijkAanZee_natura2000_coepelduynen_cropped.tif"
        )

    cloud_pictures = [
        output_path
        + "/20220514_114854_SV1-02_SV_RD_11bit_RGBI_50cm_Rijnsburg_natura2000_coepelduynen_cropped.tif",
        output_path
        + "/20190302_105829_SV1-01_50cm_RD_11bit_RGBI_KatwijkAanZee_natura2000_coepelduynen_cropped.tif",
        output_path
        + "/20191202_110525_SV1-04_50cm_RD_11bit_RGBI_KatwijkAanZee_natura2000_coepelduynen_cropped.tif",
    ]
    non_cloud_pictures = [
        output_path
        + "/20230402_105321_PNEO-03_1_49_30cm_RD_12bit_RGBNED_Zoeterwoude_natura2000_coepelduynen_cropped_ndvi_asphalt_crop.tif",
        output_path
        + "/20230513_104139_PNEO-03_1_1_30cm_RD_12bit_RGBNED_NoordwijkAanZee_natura2000_coepelduynen_cropped_ndvi_re_ndvi_asphalt_crop.tif",
        output_path
        + "/20220515_113347_SV1-02_SV_RD_11bit_RGBI_50cm_KatwijkAanZee_natura2000_coepelduynen_cropped.tif",
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
