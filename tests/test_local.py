import os
import zipfile

import rasterio

# the cloud_recognition.api needs to be imported from the natura2000 data science repo
from rasterio.plot import show
from settings_local import output_path, path_geojson

import satellite_images_nso_extractor._manipulation.nso_manipulator as nso_manipulator
import satellite_images_nso_extractor._nso_data_extraction.nso_api as nso_api
import satellite_images_nso_extractor.api.nso_georegion as nso

output_path = "./test_output_data/"


def zip_tif_file(tif_file_path, zip_file_path):
    """
    Zips a .tif file into a .zip archive.

    :param tif_file_path: Path to the .tif file to be zipped
    :param zip_file_path: Path to the resulting .zip file
    """
    if not os.path.exists(tif_file_path):
        raise FileNotFoundError(f"The file '{tif_file_path}' does not exist.")

    # Ensure the file is a .tif file
    if not tif_file_path.endswith(".tif"):
        raise ValueError(f"The file '{tif_file_path}' is not a .tif file.")

    # Create a zip archive and add the .tif file
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        zipf.write(tif_file_path, os.path.basename(tif_file_path))

    print(f"File '{tif_file_path}' has been zipped into '{zip_file_path}'.")


def test_links():
    """
    These tests test the API handling of NSO download link data.
    """
    georegion = nso.nso_georegion(
        path_to_geojson=path_geojson,
        output_folder=output_path,
        username=nso_username,
        password=nso_password,
    )

    links = georegion.retrieve_download_links(max_diff=0.5, start_date="2011-01-01")

    assert len(links) > 0, "No links found error!"

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

    pneo_links = links[links["resolution"] == "30cm"]
    pneo_links = pneo_links[pneo_links["link"].str.contains("RGBNED")]
    pneo_links = pneo_links.sort_values("percentage_geojson")

    assert len(pneo_links) > 0, "No PNEO links found error!"

    superview_links = links[links["resolution"] == "50cm"]
    superview_links = superview_links[superview_links["link"].str.contains("RGBI")]
    superview_links = superview_links.sort_values("percentage_geojson")

    assert len(superview_links) > 0, "No  PNEO links found error!"


def test_channels_pneo():
    """

    Test if the channels are added correctly to PNEO data.

    """

    test_file_path_org = "./test_data/20240921_104947_PNEO-04_2_1_30cm_RD_12bit_RGBNED_NieuwVennep_test_small_region_cropped.tif"

    test_file_path = nso_manipulator.add_index_channels(
        test_file_path_org, ["re_ndvi"], remove_input_file=False
    )
    # Open the TIFF image and display ndvi
    with rasterio.open(test_file_path) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert "re_ndvi" in src.descriptions, "re_ndvi bands not added correctly"

    os.remove(test_file_path)

    test_file_path = nso_manipulator.add_index_channels(
        test_file_path_org, ["ndwi"], remove_input_file=False
    )
    # Open the TIFF image and display ndvi
    with rasterio.open(test_file_path) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert "ndwi" in src.descriptions, "re_ndvi bands not added correctly"

    os.remove(test_file_path)


def test_channels_superview():
    """

    Test if added channels were correct with superview data.

    """

    test_file_path_org = "./test_data/20220922_110546_SV2-01_SV_RD_11bit_RGBI_50cm_Voorhout_test_small_region_cropped.tif"

    test_file_path = nso_manipulator.add_index_channels(
        test_file_path_org, ["ndvi"], remove_input_file=False
    )
    # Open the TIFF image and display ndvi
    with rasterio.open(test_file_path) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert "ndvi" in src.descriptions, "re_ndvi bands not added correctly"

    os.remove(test_file_path)

    test_file_path = nso_manipulator.add_index_channels(
        test_file_path_org, ["ndwi"], remove_input_file=False
    )
    # Open the TIFF image and display ndvi
    with rasterio.open(test_file_path) as src:
        # Get the number of bands
        num_bands = src.count
        print("Number of bands:", num_bands)

        assert "ndwi" in src.descriptions, "re_ndvi bands not added correctly"

    os.remove(test_file_path)


def test_crop():
    try:
        georegion = nso.nso_georegion(
            path_to_geojson="./test_data/test_small_region_crop.geojson",
            output_folder=output_path,
            username="test",
            password="test",
        )

        cropped_file = georegion.crop(
            "./test_data/20240921_104947_PNEO-04_2_1_30cm_RD_12bit_RGBNED_NieuwVennep_test_small_region_cropped.tif",
            False,
        )

        assert os.path.exists(
            cropped_file
        ), f"Cropped file not found, cropped might not have worked: {cropped_file}"
    finally:
        os.remove(cropped_file)


def test_unzip():
    try:
        zip_name = "./test_output_data/20220922_110546_SV2-01_SV_RD_11bit_RGBI_50cm_Voorhout_test_small_region_cropped_tif.zip"

        zip_tif_file(
            "./test_data/20220922_110546_SV2-01_SV_RD_11bit_RGBI_50cm_Voorhout_test_small_region_cropped.tif",
            zip_name,
        )
        extracted_folder = nso_api.unzip_delete(zip_name, True)
        assert os.path.exists(
            extracted_folder
        ), f"Unzipped file not found, unzipping might not have worked: {extracted_folder}"
    finally:
        if os.path.exists(zip_name):
            os.remove(zip_name)
        if os.path.exists(zip_name):
            os.remove(extracted_folder)
