import satellite_images_nso.api.nso_georegion as nso
from satellite_images_nso._nso_data_extraction import nso_api
import rasterio
import numpy as np
from matplotlib import pyplot as plt
from rasterio.plot import show
import glob
import settings
import logging
from azure.storage.blob import ContainerClient

""" 

Schedule NSO satellite images for SV 50 cm RGBI Coepelduynen.


@author: Michael de Winter


"""

logging.basicConfig(level=logging.DEBUG)



logger = logging.getLogger('schedule_nso_tif')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('schedule_nso_tif.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

container = ContainerClient.from_connection_string(conn_str=settings.BLOB_CONNECTION_STRING,\
                                                   container_name=settings.BLOB_CONTAINER) 

def upload_file_rm_blob(path_to_file, name, overwrite=True):

        with open(path_to_file, "rb") as data:      
            container.upload_blob(name,data,overwrite=overwrite)


def init():
  """ 
    Set a nso georegion and retrieve links.
  """
  # This method fetches all the download links to all the satelliet images which contain region in the geojson
  georegion = nso.nso_georegion(settings.path_geojson_coepelduynen,settings.output_path_coepelduynen,\
                                settings.nso_username,\
                              settings.nso_password)


  links = georegion.retrieve_download_links( max_diff = 0.9)
  return links, georegion


def check_downloaded_tif_files(output_path):
  """
  Check .tif files which are already downloaded.
  Depends on being the files being stored locally instead of in a blob storage.
  

  @param output_path: Path where the .tif files are stored.
  @return done_files: files which are already done.
  """
  done_files = []

  # Filter out already done links.
  for file in glob.glob(output_path+"/*.tif"):
      print(file.split("\\")[1].split("-")[0])
      done_files.append(file.split("\\")[1].split("-")[0])
    
  return done_files

def filter_links(links, done_files):
  """
  Filter links based on the found files.

  @param links: the download links for the georegions found.
  @param done_files: .tif files already downloaded.
  @return filter_links: links which are not already downloaded.
  """
  SV_links = []
  for link in links:
      if 'SV' in link and '50cm' in link and "RGBI" in link:
          check_list = [link.find(file) for file in done_files]
          if sum(1 for number in check_list if number > 0) == 0:
              print(link)
              SV_links.append(link)
  return SV_links

if __name__ == '__main__':

  links,georegion = init()

  done_files = check_downloaded_tif_files(settings.output_path_coepelduynen)

  SV_links = filter_links(links, done_files)

  if len(SV_links) >0:
    logger.info("Found new links")
    for link in SV_links:
      logger.info(link)
      cropped_location, no, no2 = georegion.execute_link(link, calculate_nvdi = False)
      logger.info("Uploading")
      upload_file_rm_blob(cropped_location, cropped_location.split("/")[-1])
  else:
      logger.info("No new links")
