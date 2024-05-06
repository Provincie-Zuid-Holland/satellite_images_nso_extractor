import numpy as np
import rasterio
from rasterio.plot import show
from matplotlib import pyplot as plt




def plot_tif(raster_path):
    """
    Function for plotting a .tif file.
    Might be moved somewhere else.

    @param raster_path: Path to a raster file 
    """
        src = rasterio.open(raster_path)
        plot_out_image = np.clip(src.read()[2::-1],
                        0,2200)/2200 # out_image[2::-1] selects the first three items, reversed

        plt.figure(figsize=(10,10))
        rasterio.plot.show(plot_out_image,
            transform=src.transform)
        
        src.close()