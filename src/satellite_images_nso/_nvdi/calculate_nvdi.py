import geopandas as gpd
import numpy as np
import pandas as pd
import earthpy.plot as ep
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
import logging
import tqdm
"""
    This class is used for various NVDI calculations.

    For more information check:
    https://en.wikipedia.org/wiki/Enhanced_vegetation_index

"""
def aggregate_ndvi_habitat(ndvi_geo_df: gpd.geodataframe.GeoDataFrame) -> pd.Series:
    """
    Calculate the aggregated statistics for NDVI 
    @param ndvi_geo_df: geopandas dataframe, with ndvi values for each pixel
    @return pandas series: with 'mean', 'std', 'min', 'max', 'count' in the row axis
    """
    return ndvi_geo_df['ndvi'].agg(['mean', 'std', 'min', 'max', 'count'])

def generate_ndvi_channel(tile):
        """
        Generate ndvi channel from 2 bands.
        
        @param tile: rgbi tile to calculate to the NDVI from.
        @return a NDVI channel.
        """
        print("Generating NDVI channel...")
        red = tile[0]
        nir = tile[3]
        ndvi = []

        # No more numpy way for looping through these array's which lead to not good ndvi calculation.
        # Now we loop through each pixel directly
        for i in tqdm.tqdm(range(len(red))):
            ndvi_x = []
            for x in range(len(red[i])):
                upper_ndvi = (int(nir[i][x])-int(red[i][x]))
                lower_ndvi = (int(nir[i][x])+int(red[i][x]))

                if lower_ndvi == 0:
                    ndvi_x.append(0)
                else:
                    ndvi_cur = upper_ndvi/lower_ndvi
                    ndvi_cur = (ndvi_cur*100)+100
                    ndvi_x.append(int(ndvi_cur))
                    
            ndvi.append(ndvi_x)
        return np.array(ndvi)
    
def normalized_diff(b1: np.array, b2: np.array) -> np.array:
    """Take two n-dimensional numpy arrays and calculate the normalized
    difference.

    Math will be calculated (b1-b2) / (b1 + b2). b1 is NIR, b2 is Red

    Parameters
    ----------
    b1, b2 : numpy arrays
        Two numpy arrays that will be used to calculate the normalized
        difference. Math will be calculated (b1-b2) / (b1+b2).

    Returns
    ----------
    n_diff : numpy array
        The element-wise result of (b1-b2) / (b1+b2) calculation. Inf values
        are set to nan. Array returned as masked if result includes nan values.
    """
    logging.info('Calculating NDVI')
    if not (b1.shape == b2.shape):
        raise ValueError("Both arrays should have the same dimensions")
    
    b1 = b1.astype('f4')
    b2 = b2.astype('f4')
    # Ignore warning for division by zero
    with np.errstate(divide="ignore"):#np.seterr(divide='ignore', invalid='ignore')
        n_diff = (b1 - b2) / (b1 + b2)

    # Set inf values to nan and provide custom warning
    if np.isinf(n_diff).any():
        warnings.warn(
            "Divide by zero produced infinity values that will be replaced "
            "with nan values",
            Warning,
        )
        n_diff[np.isinf(n_diff)] = np.nan

    # Mask invalid values
    if np.isnan(n_diff).any():
        n_diff = np.ma.masked_invalid(n_diff)

    return n_diff
  
def enhanced_vegetation_index(red: np.array, blue: np.array, nir: np.array, L: float=1, c1: float=6, c2: float=7.5, G: float=2.5) -> np.array:
    """
    DEPRECATED MIGHT BE USED IN THE FUTURE!

    
    This function makes groups out of the NVDI values.
    For a nicer plot.
    
    @param red: numpy array color values for red channel
    @param blue: numpy array color values for blue channel
    @param nir: numpy array values for infra-red channel
    @param L: float see Wikipedia
    @param c1: float see Wikipedia
    @param c2: float see Wikipedia
    @param G: float see Wikipedia
    @return numpy array, vegetation index for each pixel
    """
    if not ((red.shape == blue.shape) and (blue.shape == nir.shape)):
        raise ValueError("All arrays should have the same dimensions")
    # Ignore warning for division by zero
    red = red.astype('f4')
    blue = blue.astype('f4')
    nir = nir.astype('f4')
    with np.errstate(divide="ignore"):#np.seterr(divide='ignore', invalid='ignore')
        evi = G * (nir - red) / (nir + c1 * red - c2 * blue + L) 
        
    # Set inf values to nan and provide custom warning
    if np.isinf(evi).any():
        warnings.warn(
            "Divide by zero produced infinity values that will be replaced "
            "with nan values",
            Warning,
        )
        evi[np.isinf(evi)] = np.nan

    # Mask invalid values
    if np.isnan(evi).any():
        evi = np.ma.masked_invalid(evi)
        
    return evi

def make_ndvi_plot(path, title, plot, save_figure =True):
    """ Plot NVDI data 
    
    @path: path to the numpy array with the NVDI data.
    @title: A title on the plot.
    @plot: bool for whether to see the plots in de output or not
    """
    data_ndvi = np.load(path, allow_pickle=True)
    #plot ndvi
    if plot:
        ep.plot_bands(data_ndvi, 
                figsize=(28, 12),
                cmap='RdYlGn',
                scale=False,
                vmin=-1, vmax=1,
                title=title)
        plt.show()
        logging.info('Plotted NDVI image')
    
    # Create classes and apply to NDVI results
    ndvi_class_bins = [-np.inf, 0, 0.1, 0.25, 0.4, np.inf]
    ndvi_class = np.digitize(data_ndvi, ndvi_class_bins)

    # Apply the nodata mask to the newly classified NDVI data
    ndvi_class = np.ma.masked_where(
        np.ma.getmask(data_ndvi), ndvi_class
    )
    np.unique(ndvi_class)

    # Define color map
    nbr_colors = ["gray", "y", "yellowgreen", "g", "darkgreen"]
    nbr_cmap = ListedColormap(nbr_colors)

    # Define class names
    ndvi_cat_names = [
        "No Vegetation",
        "Bare Area",
        "Low Vegetation",
        "Moderate Vegetation",
        "High Vegetation",
    ]
    legend_titles = ndvi_cat_names

    #plot ndvi classes
    fig, ax = plt.subplots(figsize=(28, 12))
    im = ax.imshow(ndvi_class, cmap=nbr_cmap)
    ep.draw_legend(im_ax=im, titles=legend_titles)
    ax.set_title(
        " Normalized Difference Vegetation Index (NDVI) Classes",
        fontsize=14,
    )
    ax.set_axis_off()

    #Auto adjust subplot to fit figure size
    plt.tight_layout()

    #save fig
    path_corr=path.replace("\\","/")+"_classes.png"
    plt.savefig(path_corr)
    logging.info(f'Saved ndvi classes figure {path_corr}')
    print(f'Saved figure {path_corr}')

    #plot figure
    if plot:
        print('Plotting NDVI classes image')
        plt.show()
    else:
        plt.close()

    return path_corr

