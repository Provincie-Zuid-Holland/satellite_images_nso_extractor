import requests
from requests.auth import HTTPBasicAuth 
import objectpath
import os
from datetime import date
import zipfile 
import shapely
import numpy as np
import json
from satellite_images_nso.__logger import logger_nso
import sys

"""
    This class is a python wrapper with added functionality around the NSO api.

    Provides functionality such as:

    - Retrieving download links for satellite images for a georegion.

    - Cloud coverage filtering, note that we use the NSO cloud coverage filter for now, this filter filters the whole satellite images instead of only the cropped image. TODO: Make a filter for the cropped image.

    - Download and unzipping functionality for satellite download links. 

    Author: Michael de Winter.
"""
logger = logger_nso.init_logger()


def download_file(url, local_filename, user_n, pass_n):
    """
        Method for downloading files in chunk
    """
    
    # NOTE the stream=True parameter below
    with requests.get(url, auth = HTTPBasicAuth(user_n, pass_n), stream=True) as r:
        logger.info("Downloading file: "+url)
        print("Downloading file: "+url)
        r.raise_for_status()
     
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
    return local_filename



def retrieve_download_links(georegion, user_n, pass_n, start_date = "2014-01-01", end_date =date.today().strftime("%Y-%m-%d"),max_meters=3,):
    """
        This functions retrieves download links for satellite image corresponding to the region in the geojson.

        @param georegion: a polygon with the georegion.
        @param start_date: From when satelliet date needs to be looked at.
        @param end_date: the end date of the period which needs to be looked at
        @param max_meters: Maximum resolution which needs to be looked at.
        @return: the found download links.
    """
    save_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    geojson_coordinates = georegion
    
    url = 'https://api.satellietdataportaal.nl/v1/search'
    myobj = { "type": "Feature","geometry":
    {"type": "Polygon", "coordinates": geojson_coordinates },"properties": {"fields":{"geometry":"false"},"filters" :
    { "datefilter":{ "startdate": start_date,"enddate" : end_date }, "resolutionfilter":{ "maxres" :max_meters, "minres" : 0 }} } }

    headers = {'content-type': 'application/json'}
    x = requests.post(url, auth = HTTPBasicAuth(user_n, pass_n), data = json.dumps(myobj) ,  headers=headers )  
    reponse = json.loads(x.text)

    # Check if valid reponse
    if reponse == "":
        raise Exception("No valid response from NSO! message:"+x.text)       
    links = []

    for row in reponse['features']:
        try:  
            if row['properties']['downloads'] is not None:

                # Check for cloudcoverage. TODO: Use a variable for it.
                if row['properties']['cloudcover'] is None or float(row['properties']['cloudcover']) < 30.0 :
                    # This checks to see if the geojson is in the full region. TODO: Make it optional and propertional
                    if check_if_geojson_in_region(row,geojson_coordinates ) == True:                
                        for download in row['properties']['downloads']:
                            links.append(download['href'] )
                
        except Exception as e: 
            logger.info(str(e)+" This error can be normal!")

    sys.stdout = save_stdout
    return links


def download_link(link, absolute_path, user_n, pass_n, file_exists_check: bool = False):
    """
        Method for downloading satelliet data from a link.

        @param link: a link where the satelliet data is stored.
        @param absolute_path: the filename and path where the file will get downloaded.
    """

    try:
        # Check if file is already downloaded.
        if os.path.isfile(absolute_path) is True:
            logger.info(absolute_path+" is already downloaded in \n" )
            print("File already downloaded: \n"+absolute_path)
        else:    
            
            #r = requests.get(link,auth = HTTPBasicAuth(user_n, pass_n))
            download_file(link, absolute_path, user_n, pass_n)
            
            #logger.info("Status code from the request: "+r.status_code)
            #print("Status code from the request: "+r.status_code)
            #logger.info("This is the text: "+r.text)
            #print("This is the text: "+r.text)

            #Retrieving data from the URL using get method
            #with open(absolute_path, 'wb') as f:
                #giving a name and saving it in any required format
                #opening the file in write mode
            #    f.write(r.content)
            #f.close()
            #r.close()
    except Exception as e:
        logger.info("Error downloading file: "+str(e))
        print("Error downloading file: "+str(e))  # This is the correct syntax
        raise SystemExit(e)

def unzip_delete(path,delete = True): 
    """
        Unzip a zip file and delete the .zip file.
    """
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(path.replace(".zip",""))
    
    if delete == True:
        os.remove(path)

    return path.replace(".zip","")


def check_if_geojson_in_region(row,projected_shape):
    """
        This method checks if the geojson is fully in the TCI raster.

        TODO: For now it's only fully in the georegion on which the cloud coverage is calculated.      
        @param src_TCI_raster_dataset: The rasterio opened TCI raster.
        @param projected_shape: The geojson warped to the src of the copernicus crs.
    """
    
    return_statement = False 
    
    row_shape = shapely.geometry.Polygon([[coordx[0],coordx[1]] for coordx in row['geometry']['coordinates'][0]])
    geojson_shape = shapely.geometry.Polygon([[coordx[0],coordx[1]] for coordx in projected_shape[0]])
    geojson_shape_xy = geojson_shape.boundary.xy

    xy_intersection = geojson_shape.intersection(row_shape).boundary.xy
    
    try:
        difference_array = np.array(geojson_shape_xy) -  np.array(xy_intersection)
       
        if max(difference_array.min(), difference_array.max(), key=abs) < 10000:
            return_statement = True
    except Exception as e: 
            print(e)
            print(row)
            logger.info(e+" "+row)

    return return_statement


    

