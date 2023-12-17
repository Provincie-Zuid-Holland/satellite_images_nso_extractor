import os
import satellite_images_nso._nso_data_extraction.nso_api as nso_api
import satellite_images_nso._manipulation.nso_manipulator as nso_manipulator
from datetime import date
import glob
import geopandas as gpd
import json
from satellite_images_nso.__normalisation import normalisation
import shutil
import logging
import numpy as np
import rasterio
import sys

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(funcName)s %(message)s',
                    filename='Logging_nso_download.log'
                    )  # to see log in console remove filename

"""
    This class constructs a nso georegion object.

    WHich can be used for retrieving download links for satellite images for a parameter georegion.
    Or cropping satellite images for the parameter georegion.
   
    Author: Michael de Winter
"""

def correct_file_path(path):
    " File path does not need to end with /"
    path = path.replace("\\","/")
    if path.endswith("/"):
        return path[:-1]
    return path

class nso_georegion:
    """
        A class used to bind the output folder, a chosen a georegion and a NSO account together in one object.
        On this object most of the operations are done.
        
    """

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

        self.georegion = False
        try:
            # georegion is a variable which contains the coordinates in the geojson, which should be WGS!
            self.georegion = self.__getFeatures(self.path_to_geojson)[0]
        except Exception as e:
            print(e)

        if self.georegion == False :
            raise Exception("Geojson not loaded correctly. Weirdly this error is sometimes solved by reloading the session")

        if os.path.isdir(output_folder)  == True:
            self.output_folder = correct_file_path(output_folder)
        else:
            raise ValueError('Output directory does not exists')
       
        self.username = username
        self.password = password


    def  __getFeatures(self,path):
        """
            Function to parse features from GeoDataFrame in such a manner that rasterio wants them
    
            @param path: The path to a geojson.
            @return coordinates which rasterio wants to have.
        """
        json_loaded = json.loads(gpd.read_file(path).to_json())

        if json_loaded['features'][0]['geometry']['type']  == 'MultiPolygon':
            logging.info("Caution multiploygons are not well supported!")
            print("Caution multiploygons are not well supported!")

        return [json_loaded['features'][0]['geometry']['coordinates']]


    def retrieve_download_links(self, start_date = "2014-01-01", end_date =date.today().strftime("%Y-%m-%d"), max_meters=3 , strict_region = True, max_diff = 0.8, cloud_coverage_whole = 30):
        """
            This functions retrieves download links for area chosen in the geojson for the nso.

            @param start_date: From when satelliet date needs to be looked at.
            @param end_date: the end date of the period which needs to be looked at
            @param max_meters: Maximum resolution which needs to be looked at.
            @param strict_region: A filter applied to links which have to fully contain the region in the geojson.
            @param max_diff: The percentage that a satellite image has to have of the selected geojson region.
            @param cloud_coverage_whole: level percentage of clouds to filter out of the whole satellite image, so 30 means the percentage has to be less or equal to 30.
            @return: the found download links.
        """
        return nso_api.retrieve_download_links(self.georegion,self.username, self.password, start_date, end_date, max_meters,strict_region, max_diff, cloud_coverage_whole )


    def crop(self, path, plot):
        """
            Function for the crop and the calculating of the NVDI index.
            Can be used as a standalone if you have already unzipped the file.

            @oaram path: Path to a .tif file.
          
        """       
        true_path = path
        if '.tif' not in true_path:
            for x in glob.glob(path+'/**/*.tif', recursive=True):
                true_path = x
        
        if ".tif" not in true_path:
            logging.error(true_path+" Error:  .tif not found")
            raise Exception(".tif not found")
        else: 
            cropped_path  =  nso_manipulator.run(true_path, self.path_to_geojson, self.output_folder, plot)
            logging.info(f'Cropped file is found at: {cropped_path}')
            
            print("Cropped file is found at: "+str(cropped_path ))
        
            return cropped_path
            
    def delete_extracted(self,extracted_folder):
        """
        Deletes extracted folder

        @param extracted_folder: path to the extracted folder

        """
        try:
            shutil.rmtree(extracted_folder)
            logging.info(f'Deleted extracted folder {extracted_folder}')
        except Exception as e:
            logging.error(f'Failed to delete extracted folder {extracted_folder} '+str(e))
            print("Failed to delete extracted folder: "+str(e))

    def execute_link(self, link, delete_zip_file = False, delete_source_files = True,  plot=True, in_image_cloud_percentage = False,  add_ndvi_band = False, add_height_band = False ): 
        """ 
            Executes the download, crops and the calculates the NVDI for a specific link.
        
            @param link: Link to a file from the NSO.                    
            @param delete_zip_file: whether or not to keep the original .zip file on default it will keep the file.
            @param delete_source_files: whether or not to keep the extracted files on defualt it will delete the source files.
            @param plot: Rather or not to plot the resulting image from cropping.
            @param in_image_cloud_percentage:  TODO: Calculate the cloud percentage in a picture.
            @param add_ndvi_band: Whether or not to add the ndvi as a new band.
            @param add_height_band: Whether or not to height as new bands, input should be a file location to the height file.
           
        """
        cropped_path = ""
        
        try:
            download_archive_name = self.output_folder+"/"+link.split("/")[len(link.split("/"))-1]+"_"+link.split("/")[len(link.split("/"))-2]+'.zip'
           
      
            # Check if file is already cropped
            cropped_path = download_archive_name.replace(".zip","*cropped.tif")           
            found_files = [file for file in glob.glob(cropped_path)]
            skip_cropping = False

            if len(found_files) >0:
                if os.path.isfile(found_files[0].replace("\\","/")):
                        logging.info('File already cropped')
                        print("File is already cropped")
                        skip_cropping = True
                        cropped_path = found_files[0]
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
                        logging.info("Starting download to: "+ download_archive_name)
                        print("Starting download to: "+ download_archive_name)
                        nso_api.download_link(link, download_archive_name, self.username, self.password)
                        logging.info("Downloaded: "+ download_archive_name)
          
                logging.info("Extracting files")
                print("Extracting files")
                extracted_folder = nso_api.unzip_delete(download_archive_name,delete_zip_file)
                logging.info("Extracted folder is: "+extracted_folder)
                print("Extracted folder is: "+extracted_folder)
                    
                logging.info("Cropping")
                cropped_path = self.crop(extracted_folder,plot)
                logging.info("Done with cropping")

                # TODO: Function still needed to calculate clouds in a image.
                if in_image_cloud_percentage is True:

                    with rasterio.open(cropped_path, 'r') as tif_file:        
                            data = tif_file.read()
                            cloud_percentage = self.percentage_cloud(data)
                        
                            if cloud_percentage <= 0.10:
***REMOVED***  logging.info(f"Image contains less than 10% clouds")
***REMOVED***  print(f"Image contains less than 10% clouds")
                            
                            
                            tif_file.close()
                    
                logging.info(f'Succesfully cropped .tif file')
                print("Succesfully cropped .tif file")
                
                if delete_source_files:
                    self.delete_extracted(extracted_folder)

        except Exception as e: 
            
            logging.error("Error in downloading and/or cropping: "+str(e))
            print("Error in downloading and/or cropping: "+str(e))
            raise Exception("Error in downloading and/or cropping: "+str(e) )
                   
        print('Ready')
        logging.info('Ready')

        # Add extra channels.
        if add_ndvi_band != False:
            if "ndvi" in cropped_path:
                print("NDVI is already in it's path")
            else:
                cropped_path = nso_manipulator.add_NDVI(cropped_path)

        # Add height from a source AHN .tif file.
        if add_height_band != False:
            if "height" in cropped_path:
                print("Height is already in it's path")
            else:
                cropped_path = nso_manipulator.add_height(cropped_path, add_height_band)
        
        return cropped_path
        
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

    def normalize_min_max(self, kernel):
        """
        
            Normalize tif file with min max scaler.
            @param kernel: a kernel to normalize 

        """

        copy_kernel = np.zeros(shape=kernel.shape)
        for x in range(0, kernel.shape[0]):
            copy_kernel[x] = (kernel[x] - np.min(kernel[x])) / (np.max(kernel[x]) - np.min(kernel[x]))*255
        
        return copy_kernel

    def percentage_cloud(self, kernel, initial_threshold=145, initial_mean=29.441733905207673):

        """

            Create mask from tif file on first band.

            @param kernel: a kernel to detect percentage clouds on
            @param initial_threshold: an initial threshold for creating a mask  
            @param initial_mean: an initial pixel mean value of the selected band
        
        """
        
        kernel = self.normalize_min_max(self.data)
        new_threshold = round((initial_threshold*kernel[0].mean())/(initial_threshold*initial_mean) * initial_threshold,0)
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
        
        percentage = round((copy_kernel == 3).sum() / (copy_kernel == 2).sum(),4)

        return percentage








    





