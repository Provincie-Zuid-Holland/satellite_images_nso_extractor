
import rasterio
from rasterio.merge import merge
import numpy as np
from matplotlib import pyplot as plt

def merge_tif_files(tiff_lst, out_fp):
    """ 
        Function for merging .tif files into one .tif file.
        Good for first downloading a wider region for different shapes, cropping them for each  shapes and then merging them again with this function.

        @oaram tiff_lst: A python list of .tif files to be merged.
        @param out_fp: The .tif file to write to.
    """    
    src_files_to_mosaic = []
    for tiff in tiff_lst:
        src = rasterio.open(tiff)
        src_files_to_mosaic.append(src)

    # Merge
    mosaic, out_trans = merge(src_files_to_mosaic)

    # Copy the metadata
    out_meta = src.meta.copy()
        
    # Update the metadata
    out_meta.update({"driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "crs": "+proj=utm +zone=35 +ellps=GRS80 +units=m +no_defs" })
        
    # Write the mosaic raster to disk
    with rasterio.open(out_fp, "w", **out_meta) as dest:
        dest.write(mosaic)

    
def plot_tif_file(path_to_tif_file):
    """
        Plot a .tif file.

        @param path_to_tif_file: path to the tif file.
    """
    src = rasterio.open(path_to_tif_file)
    plot_out_image = np.clip(src.read()[2::-1],
                    0,2200)/2200 # out_image[2::-1] selects the first three items, reversed

    plt.figure(figsize=(10,10))
    rasterio.plot.show(plot_out_image,
          transform=src.transform)
    
    