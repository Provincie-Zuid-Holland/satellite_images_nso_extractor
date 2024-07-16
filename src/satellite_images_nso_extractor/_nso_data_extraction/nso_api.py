import json
import logging
import os
import sys
import zipfile
from datetime import date

import numpy as np
import requests
import shapely
from requests.auth import HTTPBasicAuth

"""
    This class is a python wrapper with added functionality around the NSO api.

    Provides functionality such as:

    - Retrieving download links for satellite images for a georegion.

    - Cloud coverage filtering, note that we use the NSO cloud coverage filter for now, this filter filters the whole satellite images instead of only the cropped image. TODO: Make a filter for the cropped image.

    - Download and unzipping functionality for satellite download links. 

    Author: Michael de Winter, Pieter Kouyzer
"""


def download_file(url, local_filename, user_n, pass_n):
    """
    Method for downloading files in chunks mostly data from the NSO is too large to fit into memory with a normal
    """

    # NOTE the stream=True parameter below
    with requests.get(url, auth=HTTPBasicAuth(user_n, pass_n), stream=True) as r:
        logging.info("Downloading file: " + url)
        print("Downloading file: " + url)
        r.raise_for_status()

        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_filename


def retrieve_download_links(
    georegion,
    user_n,
    pass_n,
    start_date,
    end_date,
    max_meters,
    strict_region,
    max_diff,
    cloud_coverage_whole,
):
    """
    This functions retrieves download links for satellite image corresponding to the region in the geojson.

    @param georegion: a polygon with the georegion.
    @param user_n: NSO username.
    @param pass_n: NSO password.
    @param start_date: From when satelliet date needs to be looked at.
    @param end_date: the end date of the period which needs to be looked at
    @param max_meters: Maximum resolution which needs to be looked at.
    @param strict_region: A filter applied to links to only fully contain the region.
    @param max_diff: The percentage that a satellite image has to have of the selected geojson region.
    @param cloud_coverage_whole: level percentage of clouds to filter out of the whole satellite image, so 30 means the percentage has to be less or equal to 30.
    @return: the found download links.
    """

    # FOR DEBUGGING !!!!!!!This blocks the large print output from the request.
    # save_stdout = sys.stdout
    # sys.stdout = open(os.devnull, 'w')

    geojson_coordinates = georegion

    url = "https://api.satellietdataportaal.nl/v1/search"
    myobj = {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": geojson_coordinates},
        "properties": {
            "fields": {"geometry": "false"},
            "filters": {
                "datefilter": {"startdate": start_date, "enddate": end_date},
                "resolutionfilter": {"maxres": max_meters, "minres": 0},
            },
        },
    }

    headers = {"content-type": "application/json"}
    x = requests.post(
        url, auth=HTTPBasicAuth(user_n, pass_n), data=json.dumps(myobj), headers=headers
    )
    reponse = json.loads(x.text)

    logging.info(f"Got following request: {reponse}")
    if "features" not in reponse.keys():
        print(reponse)
        logging.error("No valid response from NSO message:" + x.text)
        raise Exception("No valid response from NSO message:" + x.text)

    links = []
    for row in reponse["features"]:
        try:
            if row["properties"]["downloads"] is not None:
                print("Cloudcover check:")
                # Check for cloudcoverage. TODO: Use a variable for it.
                if (
                    row["properties"]["cloudcover"] is None
                    or float(row["properties"]["cloudcover"]) < cloud_coverage_whole
                ):
                    # This checks to see if the geojson is in the full region. TODO: Make it optional and propertional
                    print("Passed cloud check")
                    check_region = False
                    print("Going into region check:")
                    try:
                        check_region, percentage_diff, missing_part, overlap_region = (
                            check_if_geojson_in_region(
                                row, geojson_coordinates, max_diff
                            )
                        )
                    except Exception as e:
                        print(str(e) + " This error can be normal!")
                    #   logging.error(str(e)+" This error can be normal!")

                    if check_region == True or strict_region == False:
                        print("Passed region check")
                        for download in row["properties"]["downloads"]:
                            links.append(
                                [
                                    download["href"],
                                    percentage_diff,
                                    missing_part,
                                    overlap_region,
                                ]
                            )

        except Exception as e:
            print(str(e) + " This error can be normal!")
            logging.error(str(e) + " This error can be normal!")

    # sys.stdout = save_stdout
    return links


def download_link(link, absolute_path, user_n, pass_n):
    """
    Method for downloading satelliet data from a link.

    @param link: a link where the satelliet data is stored.
    @param absolute_path: the filename and path where the file will get downloaded.
    """

    try:
        # Check if file is already downloaded.
        if os.path.isfile(absolute_path) is True:
            logging.info(f"{absolute_path} is already downloaded")
            print("File already downloaded: " + absolute_path)
        else:
            # r = requests.get(link,auth = HTTPBasicAuth(user_n, pass_n))
            download_file(link, absolute_path, user_n, pass_n)

            # logging.info("Status code from the request: "+r.status_code)
            # print("Status code from the request: "+r.status_code)
            # logging.info("This is the text: "+r.text)
            # print("This is the text: "+r.text)

            # Retrieving data from the URL using get method
            # with open(absolute_path, 'wb') as f:
            # giving a name and saving it in any required format
            # opening the file in write mode
            #    f.write(r.content)
            # f.close()
            # r.close()
    except Exception as e:
        logging.error("Error downloading file: " + str(e))
        print("Error downloading file: " + str(e))  # This is the correct syntax
        raise SystemExit(e)


def unzip_delete(path, delete):
    """
    Unzip a zip file and delete the .zip file.
    """
    try:
        with zipfile.ZipFile(path, "r") as zip_ref:
            zip_ref.extractall(path.replace(".zip", ""))
        zip_ref.close()
    except:
        logging.error(f"Could not extract {path}")

    if delete:
        try:
            os.remove(path)
            logging.info("Deleted zip file")
        except:
            logging.error("Unable to delete zip")

    return path.replace(".zip", "")


def check_if_geojson_in_region(row, geojson, max_diff):
    """
    This method checks if the geojson is fully in the TCI raster.

    TODO: For now it's only fully in the georegion on which the cloud coverage is calculated.
    TODO: The geojson region might be split in 2 different photo's, this is for further work now.

    @param row: the row of found satellite images which contain the geojson.
    @param geojson: The selected region in the geojson.
    @parak max_diff: The cutoff of max pixel distance between the regions.
    """

    return_statement = False

    print("Max_diff in method " + str(max_diff))
    row_shape = shapely.geometry.Polygon(
        [[coordx[0], coordx[1]] for coordx in row["geometry"]["coordinates"][0]]
    )
    geojson_shape = shapely.geometry.Polygon(
        [[coordx[0], coordx[1]] for coordx in geojson[0]]
    )
    geojson_shape_xy = geojson_shape.boundary.xy

    xy_intersection = geojson_shape.intersection(row_shape).boundary.xy

    geojson_shape_xy = np.array(geojson_shape_xy)
    xy_intersection = np.array(xy_intersection)

    missing_region = geojson_shape.difference(row_shape)

    try:
        print(geojson_shape_xy)
        # This checks if pixels values are the same for both of the shapes.
        # If this isn't the case there should be min or max fluctations based on pixels which is filter with a threshold value.
        difference_array = np.intersect1d(geojson_shape_xy, xy_intersection)

        diff_geojson_sat = (
            difference_array.shape[0] / geojson_shape_xy.flatten().shape[0]
        )

        # Check if the difference is under a certain percentage.
        if diff_geojson_sat >= max_diff:
            return_statement = True

    except Exception as e:
        print(e)
        print(row)
        logging.error(e + " " + row)

    return (
        return_statement,
        diff_geojson_sat,
        missing_region,
        geojson_shape.intersection(row_shape),
    )
