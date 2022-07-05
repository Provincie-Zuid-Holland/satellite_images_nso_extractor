import rasterio
from rasterio.plot import show
import geopandas as gpd
import pandas as pd
from rasterio.warp import Resampling, transform_geom, calculate_default_transform, reproject
import numpy as np
import satellite_images_nso._nvdi.calculate_nvdi as calculate_nvdi
from matplotlib import pyplot as plt
import shutil
import logging

"""
    This is a python class for making various manipulationg such as making crops .tif files, nvdi calculations and exporting to geopandas.

    @author: Michael de Winter.
"""

def __make_the_crop(load_shape, raster_path, raster_path_cropped,plot):
    """
        This crops the sattelite image with a chosen shape.

        TODO: Make this accept a object of geopandas or shapely and crs independant.
        @param load_schape: path to a geojson shape file.
        @param raster_path_wgs: path to the raster .tiff file.
        @param raster_path_cropped: path were the cropped raster will be stored.
    """
    geo_file = gpd.read_file(load_shape)
    src = rasterio.open(raster_path)
    print('raster path opened')
    # Change the crs to rijks driehoek, because all the satelliet images are in rijks driehoek
    if geo_file.crs != 'epsg:28992':
        geo_file = geo_file.to_crs(epsg=28992)

    out_image, out_transform = rasterio.mask.mask(src,geo_file['geometry'], crop=True, filled=True)
    out_meta = src.meta

    out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})
    print('convert to RD')
    with rasterio.open(raster_path_cropped, "w", **out_meta) as dest:
            dest.write(out_image)
            dest.close()

    if plot:
        print("Plotting data for:"+raster_path_cropped+"-----------------------------------------------------")
        # TODO: Make this optional to plot.
        src = rasterio.open(raster_path_cropped)
        plot_out_image = np.clip(src.read()[2::-1],
                        0,2200)/2200 # out_image[2::-1] selects the first three items, reversed

        plt.figure(figsize=(10,10))
        rasterio.plot.show(plot_out_image,
            transform=src.transform)
        logging.info(f'Plotted cropped image {raster_path_cropped}')


def transform_vector_to_pixel_df(path_to_vector, add_ndvi_column = False):
    """
    Maps a rasterio satellite vector object to a geo pandas dataframe per pixel. 
    With the corresponding x and y coordinates and NVDI.


    @param path_to_vector: path to a vector which be read with rasterio.
    @param add_ndvi_column: WWether or not to add a ndvi column to the pandas dataframe.
    @return pandas dataframe: with x and y coordinates in epsg:4326
    """

    gpf = ""
    
    src =  rasterio.open(path_to_vector)
    crs = src.crs

    # create 1D coordinate arrays (coordinates of the pixel center)
    xmin, ymax = np.around(src.xy(0.00, 0.00), 9)  # src.xy(0, 0)
    xmax, ymin = np.around(src.xy(src.height-1, src.width-1), 9)  # src.xy(src.width-1, src.height-1)
    x = np.linspace(xmin, xmax, src.width)
    y = np.linspace(ymax, ymin, src.height)  # max -> min so coords are top -> bottom

    # create 2D arrays
    xs, ys = np.meshgrid(x, y)
    blue = src.read(1)
    green = src.read(2)
    red = src.read(3)
    nir = src.read(4)
                
    # Apply NoData mask
    mask = src.read_masks(1) > 0
    xs, ys, blue, green, red, nir = xs[mask], ys[mask], blue[mask], green[mask], red[mask], nir[mask]

    data = {"X": pd.Series(xs.ravel()),
            "Y": pd.Series(ys.ravel()),
            "blue": pd.Series(blue.ravel()),
            "green": pd.Series(green.ravel()),
            "red": pd.Series(red.ravel()),
            "nir": pd.Series(nir.ravel())
            }

    df = pd.DataFrame(data=data)
    geometry = gpd.points_from_xy(df.X, df.Y)

    if add_ndvi_column == True:
       df['ndvi'] = calculate_nvdi.normalized_diff(src.read()[3][mask], src.read()[2][mask])
       df = df[['blue','green','red','nir','ndvi',"X","Y"]]
    else:
        df = df[['blue','green','red','nir',"X","Y"]]

    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    src.close()
    
    return gdf

def move_tiff (raster_path_cropped,raster_path_cropped_moved):
    """
    Moves cropped tiff file to the main folder.

    @param raster_path_cropped: path to the cropped tiff file
    @param raster_path_cropped_moved: path to be moved to

    """
    try:
        shutil.move(raster_path_cropped,raster_path_cropped_moved)
        logging.info(f'Moving tiff file to {raster_path_cropped_moved}')
    except:
        logging.error(f'Failed to move tiff to {raster_path_cropped_moved}')

def __calculate_nvdi_function(raster_path_cropped,raster_path_nvdi,plot):
    """
        Function which calculates the NVDI index, used in a external package.

        @param raster_path_cropped: Path to the cropped file.
        @param raster_path_nvdi: path where the nvdi will be stored.
    """
    src = rasterio.open(raster_path_cropped)
    data_ndvi = calculate_nvdi.normalized_diff(src.read()[3], src.read()[2])
    data_ndvi.dump(raster_path_nvdi)

    return calculate_nvdi.make_ndvi_plot(raster_path_nvdi,raster_path_nvdi,plot)

def run(raster_path, load_shape, output_folder, calculate_nvdi,plot):
    """
        Main run method, combines the cropping of the file based on the shape and calculates the NVDI index.

        @param raster_path: path to a raster file.
        @param load_shape: path the file that needs to be cropped.
        @param calculate_nvdi: Wether or not to also to calculate the nvdi index.
        @return: the path where the cropped file is stored or where the nvdi is stored.
    """    
    raster_path_cropped_moved = ""
    raster_path_nvdi_path  = ""
    nvdi_output_classes_png_output_path = ""
    print(f'cropping file {raster_path}')
    logging.info(f'cropping file {raster_path}')
    raster_path_cropped = raster_path.replace(".tif","_"+load_shape.split("/")[len(load_shape.split("/"))-1].split('.')[0]+"_cropped.tif")
    __make_the_crop(load_shape,raster_path,raster_path_cropped,plot)
    print(f'finished cropping {raster_path}')
    logging.info(f'Finished cropping file {raster_path}')
    # Path fix and move.
    raster_path_cropped = raster_path_cropped.replace("\\", "/") 
    raster_path_cropped_moved = output_folder+"/"+raster_path_cropped.split("/")[len(raster_path_cropped.split("/"))-1]
    

    if calculate_nvdi == True:
        raster_path_nvdi = raster_path.replace(".tif","_"+load_shape.split("/")[len(load_shape.split("/"))-1].split('.')[0]+"_cropped_nvdi")
        nvdi_output_classes_png_output = __calculate_nvdi_function(raster_path_cropped,raster_path_nvdi,plot)

        raster_path_nvdi = raster_path_nvdi.replace("\\", "/")
        raster_path_nvdi_path = output_folder+"/"+raster_path_nvdi.split("/")[len(raster_path_nvdi.split("/"))-1]

        nvdi_output_classes_png_output = nvdi_output_classes_png_output.replace("\\","/")
        nvdi_output_classes_png_output_path = output_folder+"/"+nvdi_output_classes_png_output.split("/")[len(nvdi_output_classes_png_output.split("/"))-1]

        try:
            shutil.move(raster_path_nvdi,raster_path_nvdi_path)
            logging.info("Moving file to this ndvi array path: "+raster_path_nvdi_path)
        except:
            logging.error(f'Failed to move file to {raster_path_nvdi_path}')
            
        try:
            shutil.move(nvdi_output_classes_png_output,nvdi_output_classes_png_output_path)
            logging.info("Moving file to this file classes path: "+nvdi_output_classes_png_output_path)
        except:
            logging.error(f'Failed to move file to {nvdi_output_classes_png_output_path}')

    move_tiff(raster_path_cropped,raster_path_cropped_moved)

    return raster_path_cropped_moved, raster_path_nvdi_path, nvdi_output_classes_png_output_path




