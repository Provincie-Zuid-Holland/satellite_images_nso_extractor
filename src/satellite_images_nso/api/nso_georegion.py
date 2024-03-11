import glob
import json
import logging
import os
import pickle
import shutil
import warnings
from datetime import date
from datetime import datetime
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from cloud_recognition.api import detect_clouds
from rasterio.merge import merge
import re
import shapely
import json
import satellite_images_nso._manipulation.nso_manipulator as nso_manipulator
import satellite_images_nso._nso_data_extraction.nso_api as nso_api


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(funcName)s %(message)s",
    filename="Logging_nso_download.log",
)  # to see log in console remove filename

"""
    This class constructs a nso georegion object.

    WHich can be used for retrieving download links for satellite images for a parameter georegion.
    Or cropping satellite images for the parameter georegion.
   
    Author: Michael de Winter, Pieter Kouyzer
"""


def correct_file_path(path):
    """
    Method to check if all file path slashes are correct.
    Windows file paths can return not correct file paths.
    """
    path = path.replace("\\", "/")
    if path.endswith("/"):
        return path[:-1]
    return path


def merge_tifs(input_files, output_file):
    """
    Merge two different 2 tif files together into one.

    @param input_files: a python array with files paths to .tif files in it.
    @param output_files: The name of the resulting output based on the merged tif files.
    """

    print("Merging: " + input_files[0] + " and " + input_files[1])

    with rasterio.open(input_files[0]) as src1, rasterio.open(input_files[1]) as src2:
        # Check CRS
        assert src1.crs == src2.crs, "CRS mismatch"

    raster_to_mosiac = [rasterio.open(p) for p in input_files]
    mosaic, output = merge(raster_to_mosiac)

    output_meta = raster_to_mosiac[0].profile
    output_meta.update(
        {
            "driver": "GTiff",
            "interleave": "band",
            "tiled": True,
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": output,
        }
    )

    for file in raster_to_mosiac:
        file.close()

    with rasterio.open(output_file, "w", **output_meta) as m:
        m.write(mosaic)


class nso_georegion:
    """
    A class used to bind the output folder, a chosen a georegion and a NSO account together in one object.
    On this object most of the operations are done.

    """

    def __init__(
        self,
        output_folder: str,
        username: str,
        password: str,
        path_to_geojson: str = None,
        coordinates: str = None,
        previous_link: str = None,
        cloud_detection_model_path: str = None,
    ):
        """
        Init of the class.

        @param output_folder: Path where the resulting .tif file will be saved to.
        @param username: the username of the nso account.
        @param password: the password of the nso account
        @param path_to_geojson: path where the geojson is located with the selected region.
        @param coordinates: instead of geojson also a polygon with coordinates can be given.
        @param previous_link: If we need to fill a region a with new satellite data, we need to know the previous since we have to find the closed link to this one.
        @cloud_detection_model_path: optional location of a .sav of a cloud detection model
        """
        if path_to_geojson:
            self.path_to_geojson = correct_file_path(path_to_geojson)
            # Name needs to be included in the geojson name.
            self.region_name = path_to_geojson.split("/")[
                len(path_to_geojson.split("/")) - 1
            ].split(".")[0]

        if coordinates:
            self.region_name = "fill_region"

        self.georegion = False
        try:
            # georegion is a variable which contains the coordinates in the geojson, which should be WGS84!
            if path_to_geojson is not None:
                self.georegion = self.__getFeatures(self.path_to_geojson)[0]
            elif coordinates is not None:
                self.georegion = coordinates
        except Exception as e:
            print(e)

        if not self.georegion:
            raise Exception(
                "Geojson not loaded correctly. Weirdly this error is sometimes solved by reloading the session"
            )

        if os.path.isdir(output_folder):
            self.output_folder = correct_file_path(output_folder)
        else:
            raise ValueError("Output directory does not exists")

        self.username = username
        self.password = password
        if cloud_detection_model_path:
            self.cloud_detection_model = pickle.load(
                open(cloud_detection_model_path, "rb")
            )

        if previous_link:
            self.previous_link_date = datetime.strptime(
                previous_link.split("/")[-1].split("_")[0], "%Y%m%d"
            )

            # We have to know the resolution because we have to have matching resolutions
            self.resolution = re.search(
                r"(\d{2,3}cm)",
                previous_link,
            )[0]

            # The same thing for bands.
            self.bands = re.search(r"(RGB|RGBI|RGBNED)", previous_link)[0]
            if not self.bands:
                raise ValueError("Only RGB, RGBI or RGBNED values are allowed ")

    def __getFeatures(self, path):
        """
        Function to parse features from GeoDataFrame in such a manner that rasterio wants them

        @param path: The path to a geojson.
        @return coordinates which rasterio wants to have.
        """
        json_loaded = json.loads(gpd.read_file(path).to_json())

        if json_loaded["features"][0]["geometry"]["type"] == "MultiPolygon":
            logging.info("Caution multiploygons are not well supported!")
            print("Caution multiploygons are not well supported!")

        return [json_loaded["features"][0]["geometry"]["coordinates"]]

    def retrieve_download_links(
        self,
        start_date="2014-01-01",
        end_date=date.today().strftime("%Y-%m-%d"),
        max_meters=3,
        strict_region=True,
        max_diff=0.8,
        cloud_coverage_whole=30,
        find_nearest_to_previous_link: bool = False,
    ):
        """
        This functions retrieves download links for area chosen in the geojson for the nso.

        @param start_date: From when satellite date needs to be looked at.
        @param end_date: the end date of the period which needs to be looked at, defaults to the current date.
        @param max_meters: Maximum resolution which needs to be looked at.
        @param strict_region: A filter applied to links which have to fully contain the region in the geojson.
        @param max_diff: The percentage that a satellite image has to have of the selected geojson region.
        @param cloud_coverage_whole: level percentage of clouds to filter out of the whole satellite image, so 30 means the percentage has to be less or equal to 30.
        @param find_nearest_to_previous_link: When this parameters is enabled it tries to find a link which is closed to the previous link in time.
        @return: the found download links.
        """

        links = nso_api.retrieve_download_links(
            self.georegion,
            self.username,
            self.password,
            start_date,
            end_date,
            max_meters,
            strict_region,
            max_diff,
            cloud_coverage_whole,
        )

        if find_nearest_to_previous_link is True:
            print("Finding link closed to the previous link.")
            print("Looking for resolution: " + self.resolution)
            # Find links with the same resolution.
            links = [link for link in links if self.resolution in link[0]]

            print("Looking for bands: " + self.bands)
            # Find the same bands
            links = [link for link in links if self.bands in link[0]]

            if not links:
                raise ValueError("Links are empty, region might be too strict.")

            # Find the link closed to the previous link.
            link_dates = [
                datetime.strptime(link[0].split("/")[-1].split("_")[0], "%Y%m%d")
                for link in links
            ]
            links = [
                links[
                    min(
                        range(len(link_dates)),
                        key=lambda i: abs(link_dates[i] - self.previous_link_date),
                    )
                ]
            ]

        return_links = pd.DataFrame(
            links,
            columns=[
                "link",
                "percentage_geojson",
                "missing_polygon",
                "covered_polygon",
            ],
        )

        return_links["date"] = (
            return_links["link"].str.split("/").str[-1].str.split("_").str[0]
        )
        return_links["satellite"] = (
            return_links["link"].str.split("/").str[-1].str.split("_").str[2]
        )

        return_links["resolution"] = return_links.apply(
            lambda x: (
                re.search(r"(\d{2,3}cm)", str(x["link"]))[0]
                if re.search(r"(\d{2,3}cm)", str(x["link"]))
                else None
            ),
            axis=1,
        )

        return return_links

    def crop(self, path, plot):
        """
        Function for the crop.
        Can be used as a standalone if you have already unzipped the file.

        @oaram path: Path to a .tif file.

        """
        true_path = path
        if ".tif" not in true_path:
            for x in glob.glob(path + "/**/*.tif", recursive=True):
                true_path = x

        if ".tif" not in true_path:
            logging.error(true_path + " Error:  .tif not found")
            raise Exception(".tif not found")
        else:
            cropped_path = nso_manipulator.run(
                true_path, self.georegion, self.region_name, self.output_folder, plot
            )
            logging.info(f"Cropped file is found at: {cropped_path}")

            print("Cropped file is found at: " + str(cropped_path))

            return cropped_path

    def delete_extracted(self, extracted_folder):
        """
        Deletes extracted folder

        @param extracted_folder: path to the extracted folder

        """
        try:
            shutil.rmtree(extracted_folder)
            logging.info(f"Deleted extracted folder {extracted_folder}")
        except Exception as e:
            logging.error(
                f"Failed to delete extracted folder {extracted_folder} " + str(e)
            )
            print("Failed to delete extracted folder: " + str(e))

    def execute_link(
        self,
        link: str,
        delete_zip_file: bool = False,
        delete_source_files: bool = True,
        plot: bool = True,
        in_image_cloud_percentage: bool = False,
        add_ndvi_band: bool = False,
        add_height_band: str = None,
        add_red_edge_ndvi_band: bool = False,
        add_ndwi_band: bool = False,
        cloud_detection_warning: bool = False,
        fill_coordinates: [] = [],
    ):
        """
        Executes the download, crops and the calculates the NVDI for a specific link.

        @param link: Link to a file from the NSO.
        @param delete_zip_file: This determines whether to retain the original .zip file. By default, the .zip file is kept to prevent unnecessary re-downloading.
        @param delete_source_files: This decides whether to keep the extracted files. By default, the source files are deleted after extraction.
        @param plot: Rather or not to plot the resulting image from cropping.
        @param in_image_cloud_percentage: Calculate the cloud percentage in a picture.
        @param add_ndvi_band: Whether or not to add the ndvi as a new band.
        @param add_height_band: Whether or not to height as new bands, input should be a file location to the height file.
        @param add_red_edge_ndvi_band: Whether or not to add the re_ndvi as a new band.
        @param add_ndwi_band: Whether or not to add the ndwi as a new band.
        @param cloud_detection_warning: Whether to give warning when clouds have been detected.
        @param fill_coordinates: If the satellite image is missing a region, this parameters control if it has to filled up with satellite data from the nearest image with coordinates of the missing region to look for.
        """
        cropped_path = ""

        try:
            start_archive_name = link.split("/")[len(link.split("/")) - 1]
            end_archive_name = link.split("/")[len(link.split("/")) - 2]
            download_archive_name = (
                f"{self.output_folder}/{start_archive_name}_{end_archive_name}.zip"
            )

            # Check if file is already cropped

            if hasattr(self, "resolution"):

                # Bands could be on muliple locations and we should sure for multiple glob locations.
                cropped_path_one = os.path.join(
                    self.output_folder,
                    f"{start_archive_name}*"
                    + self.bands
                    + "*"
                    + self.resolution
                    + "*"
                    + self.region_name
                    + "*cropped*.tif",
                )

                cropped_path_two = os.path.join(
                    self.output_folder,
                    f"{start_archive_name}*"
                    + self.resolution
                    + "*"
                    + self.bands
                    + "*"
                    + self.region_name
                    + "*cropped*.tif",
                )
            else:
                cropped_path = os.path.join(
                    self.output_folder,
                    f"{start_archive_name}*" + "*" + self.region_name + "*cropped*.tif",
                )

            print("Searching for: " + str(cropped_path))
            logging.info("Searching for: " + str(cropped_path))
            if hasattr(self, "resolution"):
                found_files = [
                    file
                    for file in glob.glob(cropped_path_one)
                    + glob.glob(cropped_path_two)
                ]
            else:
                found_files = [file for file in glob.glob(cropped_path)]
            skip_cropping = False

            print("Found files: " + str(found_files))
            logging.info("Found files: " + str(found_files))
            if len(found_files) > 0:
                if os.path.isfile(found_files[0].replace("\\", "/")):
                    logging.info("File already cropped")
                    print("File is already cropped")
                    skip_cropping = True
                    cropped_path = found_files[-1]
                # Does not work in notebook mode, input
                # x = input("File is already cropped, continue?")
                # if x == "no":
                #     return "File already cropped"
            if skip_cropping is False:
                # Check if download has already been done.
                if os.path.isfile(download_archive_name):
                    logging.info("Zip file already found, skipping download")
                    print("Zip file found skipping download")
                else:
                    logging.info("Starting download to: " + download_archive_name)
                    print("Starting download to: " + download_archive_name)
                    nso_api.download_link(
                        link, download_archive_name, self.username, self.password
                    )
                    logging.info("Downloaded: " + download_archive_name)

                logging.info("Extracting files")
                print("Extracting files")
                extracted_folder = nso_api.unzip_delete(
                    download_archive_name, delete_zip_file
                )
                logging.info("Extracted folder is: " + extracted_folder)
                print("Extracted folder is: " + extracted_folder)

                logging.info("Cropping")
                cropped_path = self.crop(extracted_folder, plot)
                logging.info("Done with cropping")

                # TODO: Function still needed to calculate clouds in a image.
                if in_image_cloud_percentage:
                    with rasterio.open(cropped_path, "r") as tif_file:
                        data = tif_file.read()
                        cloud_percentage = self.percentage_cloud(data)

                        if cloud_percentage <= 0.10:
                            logging.info("Image contains less than 10% clouds")
                            print("Image contains less than 10% clouds")

                        tif_file.close()

                logging.info("Succesfully cropped .tif file")
                print("Succesfully cropped .tif file")

                if delete_source_files:
                    self.delete_extracted(extracted_folder)

        except Exception as e:
            logging.error("Error in downloading and/or cropping: " + str(e))
            print("Error in downloading and/or cropping: " + str(e))
            raise Exception("Error in downloading and/or cropping: " + str(e))

        print(str(cropped_path) + " is Ready")
        logging.info(str(cropped_path) + " is Ready")

        if cloud_detection_warning:
            clouds = detect_clouds(
                model=self.cloud_detection_model,
                filepath=cropped_path,
            )

            if clouds:
                warnings.warn(
                    f"WARNING: Clouds have been detected in {cropped_path}. Inspect image visually before continuing to segmentation."
                )

        # Add extra channels.
        index_channels_to_add = []
        if add_ndvi_band:
            if "ndvi" in cropped_path:
                print("NDVI is already in it's path")
            else:
                index_channels_to_add += ["ndvi"]

        if add_red_edge_ndvi_band:
            if "re_ndvi" in cropped_path:
                print("Red Edge NDVI is already in it's path")
            else:
                index_channels_to_add += ["re_ndvi"]

        if add_ndwi_band:
            if "ndwi" in cropped_path:
                print("NDWI is already in it's path")
            else:
                index_channels_to_add += ["ndwi"]
        cropped_path = nso_manipulator.add_index_channels(
            cropped_path, channel_types=index_channels_to_add
        )

        # Add height from a source AHN .tif file.
        if add_height_band:
            if "height" in cropped_path:
                print("Height is already in it's path")
            else:
                cropped_path = nso_manipulator.add_height(cropped_path, add_height_band)

        # Fill the image with data from a other satellite image.
        if fill_coordinates != []:
            print(
                "-----Filling satellite image with data from the nearest  other satellite in time----"
            )

            # Create a other georegion based on the coordinates which are missing returned from the NSO api.
            nearest_georegion = nso_georegion(
                coordinates=json.loads(shapely.to_geojson(fill_coordinates))[
                    "coordinates"
                ],
                previous_link=link,
                output_folder=self.output_folder,
                username=self.username,
                password=self.password,
            )

            # Ensure that the region is a whole as possible
            nearest_link = nearest_georegion.retrieve_download_links(
                find_nearest_to_previous_link=True, max_diff=0.95
            )

            print("--------------------")
            print(
                "Found "
                + nearest_link[0:1]["link"].values[0]
                + " as fill satelitte image for the missing parts in the original satellite image"
            )

            cropped_path_fill = nearest_georegion.execute_link(
                nearest_link[0:1]["link"].values[0]
            )
            cropped_path_filled = cropped_path.replace(".tif", "_filled.tif")
            merge_tifs(
                [cropped_path, cropped_path_fill],
                cropped_path_filled,
            )

            cropped_path = cropped_path_filled

        return cropped_path

    def check_already_downloaded_links(self):
        """
        Check which links have already been dowloaded.
        """
        downloaded_files = []

        for file in glob.glob(
            self.output_folder + "/*" + str(self.region_name) + "*.tif"
        ):
            downloaded_files.append(file)

        return downloaded_files

    def get_output_folder(self):
        """
        Get the output folder
        """
        return self.output_folder

    def get_georegion(self):
        """
        Get the coordinates from the geojson.
        """
        return self.georegion

    def get_region_name(self):
        """-
        Get the name of the shape file.
        """
        return self.region_name

    def normalize_min_max(self, kernel):
        """

        Normalize tif file with min max scaler.
        @param kernel: a kernel to normalize

        """

        copy_kernel = np.zeros(shape=kernel.shape)
        for x in range(0, kernel.shape[0]):
            copy_kernel[x] = (
                (kernel[x] - np.min(kernel[x]))
                / (np.max(kernel[x]) - np.min(kernel[x]))
                * 255
            )

        return copy_kernel

    def percentage_cloud(
        self, kernel, initial_threshold=145, initial_mean=29.441733905207673
    ):
        """

        Create mask from tif file on first band.

        @param kernel: a kernel to detect percentage clouds on
        @param initial_threshold: an initial threshold for creating a mask
        @param initial_mean: an initial pixel mean value of the selected band

        """

        kernel = self.normalize_min_max(self.data)
        new_threshold = round(
            (initial_threshold * kernel[0].mean())
            / (initial_threshold * initial_mean)
            * initial_threshold,
            0,
        )
        copy_kernel = kernel[0].copy().copy()
        for x in range(len(kernel[0])):
            for y in range(len(kernel[0][x])):
                if kernel[0][x][y] == 0:
                    copy_kernel[x][y] = 1
                elif kernel[0][x][y] <= new_threshold:
                    if kernel[0][x][y] > 0:
                        copy_kernel[x][y] = 2
                else:
                    copy_kernel[x][y] = 3

        percentage = round((copy_kernel == 3).sum() / (copy_kernel == 2).sum(), 4)

        return percentage
