import os
import satellite_images_nso._nso_data_extraction.nso_api as nso_api
import satellite_images_nso._manipulation.nso_manipulator as nso_manipulator
from datetime import date
import glob
import shutil
import geopandas as gpd
import json

"""
    This class constructs a nso georegion object.

    WHich can be used for retrieving download links for satellite images for a parameter georegion.
    Or cropping satellite images for the parameter georegion.
   
    Author: Michael de Winter
"""
class nso_georegion:

    def __init__(self, path_to_geojson: str, output_folder: str, username: str, password: str):
        """
            Init of the class.

            @param path_to_geojson: Path where the geojson is located.
            @param output_folder: Folder where the cropped and nvdi files will be stored.
            @param username: the username of the nso account.
            @param password: the password of the nso account
        """
        
        self.path_to_geojson = path_to_geojson
        # georegion is a variable which contains the coordinates in the geojson.
        self.georegion = self.__getFeatures(path_to_geojson)[0]
        self.output_folder = output_folder 
       
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

    def crop_and_calculate_nvdi(self,path, calculate_nvdi = True):
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
            return ".Tif not found"
        else: 
            cropped_path, nvdi_path, nvdi_matrix =  nso_manipulator.run(true_path, self.path_to_geojson, calculate_nvdi )
            cropped_path = cropped_path.replace("\\", "/") 
            nvdi_path = nvdi_path.replace("\\", "/")
            nvdi_matrix = nvdi_matrix.replace("\\","/")
            shutil.move(cropped_path,self.output_folder+cropped_path.split("/")[len(cropped_path.split("/"))-1])
            shutil.move(nvdi_path,self.output_folder+nvdi_path.split("/")[len(nvdi_path.split("/"))-1])
            shutil.move(nvdi_matrix,self.output_folder+nvdi_matrix.split("/")[len(nvdi_matrix.split("/"))-1])

            
    def execute_link(self, link, delete_zip_file = False, delete_source_files = True, check_if_file_exists = True):
        """ 
            Executes the download, croppend and the calculating of the NVDI for a specific link.
        
            @param link: Link to a file from the NSO.
            @param geojson_path: Path to a geojson with the selected region.
            @param delete_zip_file: whether or not to keep the original .zip file.
            @param delete_source_files: whether or not to keep the extracted files.
            @param check_if_file_exists: check wether the file is already downloaded or stored somewhere.
        """
        download_archive_name = self.output_folder+"/"+link.split("/")[len(link.split("/"))-1]+"_"+link.split("/")[len(link.split("/"))-2]+'.zip'

        nso_api.download_link(link,download_archive_name, self.username, self.password)
        extracted_folder = nso_api.unzip_delete(download_archive_name,False)

        self.crop_and_calculate_nvdi(extracted_folder)
    
        if delete_zip_file == True:
            os.remove(download_archive_name)

        if delete_source_files == True:
            shutil.rmtree(extracted_folder)

        return "Succesfully cropped .tif file"

    def get_georegion(self):
        """
            Get the coordinates from the geojson.
        """
        return self.georegion 








    





