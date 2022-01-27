import satellite_images_nso.api.nso_georegion as nso
from satellite_images_nso._nso_data_extraction import nso_api
import rasterio
import numpy as np
from matplotlib import pyplot as plt
from rasterio.plot import show
import glob
import settings

""" 

Schedule NSO satellite images for Coepelduynen.


@author: Michael de Winter


"""



def init():
  """ 
    Set a nso georegion and retrieve links.
  """
  # This method fetches all the download links to all the satelliet images which contain region in the geojson
  georegion = nso.nso_georegion(settings.path_geojson_coepelduynen,settings.output_path_coepelduynen,\
***REMOVED***  settings.nso_username,\
***REMOVED***settings.nso_password)


  links = georegion.retrieve_download_links( max_diff = 0.9)
  return links


def check_downloaded_tif_files(output_path):
  """
  Check .tif files which are already downloaded.
  
  """
  done_files = []

  # Filter out already done links.
  for file in glob.glob(output_path+"/*.tif"):
      print(file.split("\\")[1].split("-")[0])
      done_files.append(file.split("\\")[1].split("-")[0])
    
  return done_files

def filter_links(links):

  SV_links = []
  for link in links:
      if 'SV' in link and '50cm' in link and "RGBI" in link:
          check_list = [link.find(file) for file in done_files]
          if sum(1 for number in check_list if number > 0) == 0:
              print(link)
              SV_links.append(link)
  return SV_links

if __name__ == '__main__':

  links = init()

  check_downloaded_tif_files(settings.output_path_coepelduynen)

  filter_links(