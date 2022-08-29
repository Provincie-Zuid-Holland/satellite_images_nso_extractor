import numpy as np
import tqdm
import rasterio


def get_ahn_data(ahn_input_file):

  inds = rasterio.open(ahn_input_file, 'r')        
  vegetation_height_data = inds.read(1)
  vegetation_height_transform = inds.meta["transform"]

  inds.close()
  return vegetation_height_data, vegetation_height_transform