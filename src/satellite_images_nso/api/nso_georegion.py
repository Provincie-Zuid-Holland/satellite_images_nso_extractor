import os
import satellite_images_nso._nso_data_extraction.nso_api as nso_api
import satellite_images_nso._manipulation.nso_manipulator as nso_manipulator
from datetime import date
import glob
import geopandas as gpd
import json
from satellite_images_nso.__logger import logger_nso
from satellite_images_nso.__normalisation import normalisation
import shutil


"""
    This class constructs a nso georegion object.

    WHich can be used for retrieving download links for satellite images for a parameter georegion.
    Or cropping satellite images for the parameter georegion.
   
    Author: Michael de Winter
"""

logger = logger_nso.init_logger()

def correct_file_path(path):
    " File path does not need to end with /"
    path = path.replace("\\","/")
    if path.endswith("/"):
        return path[:-1]
    return path


class nso_georegion:

    def __init__(self, path_to_geojson: str, output_folder: str, username: str, password: str):
        """
            Init of the class.

            @param path_to_geojson: Path where the geojson is located.
            @param output_folder: Folder where the cropped and nvdi files will be stored.
            @param username: the username of the nso account.
            @param password: the password of the nso account
        """
        
        self.path_to_geojson = correct_file_path(path_to_geojson)
        # Name needs to be included in the geojson name.
        self.region_name = path_to_geojson.split("/")[len(path_to_geojson.split("/"))-1].split('.')[0]
        # georegion is a variable which contains the coordinates in the geojson, which should be WGS!
        self.georegion = self.__getFeatures(self.path_to_geojson)[0]
        if len(self.georegion) == 0 :
            raise Exception("Geojson not loaded correctly. Weirdly this error is sometimes solved by reloading the session")

        self.output_folder = correct_file_path(output_folder)
       
        self.username = username
        self.password = password


    def  __getFeatures(self,path):
        """
            Function to parse features from GeoDataFrame in such a manner that rasterio wants them
    
            @param path: The path to a geojson.
            @return coordinates which rasterio wants to have.
        """
        return [json.loads(gpd.read_file(path).to_json())['features'][0]['geometry']['coordinates']]


    def retrieve_download_links(self,start_date = "2014-01-01", end_date =date.today().strftime("%Y-%m-%d"),max_meters=3):
        """
            This functions retrieves download links for area chosen in the geojson for the nso.

            @param georegion: Polygon with the stored georegion.
            @param start_date: From when satelliet date needs to be looked at.
            @param end_date: the end date of the period which needs to be looked at
            @param max_meters: Maximum resolution which needs to be looked at.

            @return: the found download links.
        """
        return nso_api.retrieve_download_links(self.georegion,self.username, self.password, start_date = "2014-01-01", end_date =date.today().strftime("%Y-%m-%d"),max_meters=3)

    def crop_and_calculate_nvdi(self,path, calculate_nvdi):
        """
            Function for the crop and the calculating of the NVDI index.
            Can be used as a standalone if you have already unzipped the file.

            @oaram path: Path to a .tif file.
            @param calculate_nvdi: Wether or not to also calculate the NVDI index.
        """       
        true_path = path
        if '.tif' not in true_path:
            for x in glob.glob(path+'/*.tif', recursive=True):
                true_path = x
        
        if ".tif" not in true_path:
            logger.info(true_path+" Error:  .tif not found") 
            raise Exception(".tif not found")
        else: 

            cropped_path, nvdi_path, nvdi_matrix =  nso_manipulator.run(true_path, self.path_to_geojson, self.output_folder, calculate_nvdi )
            logger.info("Cropped file is found at: "+cropped_path)
            logger.info("The NDVI picture is found at: "+nvdi_path)
            logger.info("NDVI numpy arrat i found at: "+nvdi_matrix)

            print("Cropped file is found at: "+str(cropped_path ))
            print("The NDVI picture is found at: "+nvdi_path)
            print("NDVI numpy arrat i found at: "+nvdi_matrix)
            return cropped_path, nvdi_path, nvdi_matrix
            
                      
    def execute_link(self, link, calculate_nvdi = True,  delete_zip_file = True, delete_source_files = True, check_if_file_exists = True, relative_75th_normalize = False):
        """ 
            Executes the download, croppend 67and the calculating of the NVDI for a specific link.
        
            @param link: Link to a file from the NSO.
            @param geojson_path: Path to a geojson with the selected region.
            @param calculate_nvdi: Wether or not to also calculate the NDVI for the cropped region.
            @param delete_zip_file: whether or not to keep the original .zip file.
            @param delete_source_files: whether or not to keep the extracted files.
            @param check_if_file_exists: check wether the file is already downloaded or stored somewhere.
        """

        cropped_path = ""
        nvdi_path = ""
        nvdi_matrix = ""

        try:
            download_archive_name = self.output_folder+"/"+link.split("/")[len(link.split("/"))-1]+"_"+link.split("/")[len(link.split("/"))-2]+'.zip'

            logger.info("Starting download to: "+download_archive_name)
            print("Starting download to: "+download_archive_name)
            nso_api.download_link(link,download_archive_name, self.username, self.password)

            logger.info("Extracting files")
            print("Extracting files")
            extracted_folder = nso_api.unzip_delete(download_archive_name,delete_zip_file)

            logger.info("Extracted folder is: "+extracted_folder)
            print("Extracted folder is: "+extracted_folder)
            cropped_path, nvdi_path, nvdi_matrix = self.crop_and_calculate_nvdi(extracted_folder,calculate_nvdi)
            
            # Multi date normalize the file.
            if relative_75th_normalize == True:
                normalisation.multidate_normalisation_75th_percentile(cropped_path)
            
            logger.info("Succesfully cropped .tif file")
            print("Succesfully cropped .tif file")
        except Exception as e: 
            logger.info("Error in downloading and or cropping: "+str(e))
            print("Error in downloading and or cropping: "+str(e))
            
        if delete_source_files == True:
            try:
                shutil.rmtree(extracted_folder)
            except Exception as e: 
                print("Failed to delete source files: "+str(e))

<<<<<<< HEAD
        logger.info("Succesfully cropped .tif file")

=======
>>>>>>> 0445b71112c9f95c1ec723a6fc406e07b42a2d2d
        return cropped_path, nvdi_path, nvdi_matrix


    def check_already_downloaded_links(self):
        """
            Check which links have already been dowloaded.
        """
        downloaded_files = []

        for file in glob.glob(self.output_folder+'/*'+str(self.region_name)+'*.tif'):
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

  








    





