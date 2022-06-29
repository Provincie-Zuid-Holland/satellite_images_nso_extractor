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
import tqdm

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

# Add extra channels.

def generate_ndvi_channel(tile):
        """
        Generate ndvi channel from 2 bands.
        
        @param tile: rgbi tile to calculate to the NDVI from.
        @return a NDVI channel.
        """
        print("Generating NDVI channel...")
        red = tile[2]
        nir = tile[3]
        ndvi = []
        for i in tqdm.tqdm(range(len(red))):
            ndvi.append((nir[i]-red[i])/(nir[i]+red[i]+1e-10)*255)
        return np.array(ndvi, dtype=np.uint8)

def generate_vegetation_height_channel(vegetation_height_data, vegetation_height_transform, target_transform, target_width, target_height):
        """
        Function to convert a .tif, which was created from a .laz file, into a band which can be used in a raster file with other bands.
        
        @param vegetation_height_data: numpy array from the ahn .tif file.
        @param vegetation_height_transform: transform from the ahn .tif meta data.
        @param target_transform: transform from the satellite .tif meta data.
        @param target_width: The width from the satellite .tif file.
        @param target_height: The height from the satellite .tif file.
        """
        print("Generating vegetation height channel...")
        channel = np.array([[0] * target_width] * target_height, dtype=np.uint8)
        src_height, src_width = vegetation_height_data.shape[0], vegetation_height_data.shape[1]
        for y in tqdm.tqdm(range(target_height)):
            for x in range(target_width):
                rd_x, rd_y = rasterio.transform.xy(target_transform, y, x)
                vh_y, vh_x = rasterio.transform.rowcol(vegetation_height_transform, rd_x, rd_y)
                if vh_x < 0 or vh_x >= src_width or \
                    vh_y < 0 or vh_y >= src_height:
                    continue
                # print(rd_x, rd_y, x, y, vh_x, vh_y)
                channel[y][x] = vegetation_height_data[vh_y][vh_x]
        return channel

def get_ahn_data(ahn_input_file):

  inds = rasterio.open(ahn_input_file, 'r')        
  vegetation_height_data = inds.read(1)
  vegetation_height_transform = inds.meta["transform"]

  return vegetation_height_data, vegetation_height_transform


def add_height_NDVI(tif_input_file):

  inds = rasterio.open(tif_input_file, 'r') 
  meta = inds.meta
  meta.update(count = 6)   
  tile = inds.read() # TODO is this behaviour similar to inds.read() ? MW: yes
  ndvi = generate_ndvi_channel(tile)
  #normalized_tile = np.array(normalise(tile, channel_normalisation, meta["width"], meta["height"]))  
   
  vegetation_height_data, vegetation_height_transform = get_ahn_data(settings.input_ahn_file)
  heightChannel = generate_vegetation_height_channel(vegetation_height_data, vegetation_height_transform, inds.meta["transform"], meta["width"], meta["height"])
  tile = np.append(tile, [heightChannel], axis=0)
  tile = np.append(tile, [ndvi], axis=0)
          
  file_to = tif_input_file.replace(".tif","_ndvi_height.tif")#.split("/")[-1]
  print(file_to)
  
 
  with rasterio.open(file_to, 'w', **meta) as outds:        
                outds.write_band(1,tile[0])
                outds.write_band(2,tile[1])
                outds.write_band(3,tile[2])
                outds.write_band(4,tile[3])
                outds.write_band(5,ndvi)
                outds.write_band(6,heightChannel)

  return file_to      
  

if __name__ == '__main__':

  links,georegion = init()

  done_files = check_downloaded_tif_files(settings.output_path_coepelduynen)

  SV_links = filter_links(links, done_files)

  if len(SV_links) >0:
    logger.info("Found new links")
    for link in SV_links:
      logger.info(link)
      cropped_location, no, no2 = georegion.execute_link(link, calculate_nvdi = False)
      logger.info('Adding new channels')
      file_all_channels = add_height_NDVI(cropped_location)
      logger.info("Uploading")
      upload_file_rm_blob(file_all_channels, file_all_channels.split("/")[-1])
  else:
      logger.info("No new links")
