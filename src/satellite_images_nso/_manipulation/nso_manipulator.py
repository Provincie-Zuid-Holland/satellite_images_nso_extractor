import rasterio
from rasterio.plot import show
import geopandas as gpd
import pandas as pd
from rasterio.warp import Resampling, transform_geom, calculate_default_transform, reproject
import numpy as np
import satellite_images_nso._nvdi.calculate_nvdi as calculate_nvdi
import satellite_images_nso.__lidar.ahn as ahn
from matplotlib import pyplot as plt
import shutil
import logging
import tqdm

"""
    This is a python class for making various manipulationg such as making crops .tif files, nvdi calculations and exporting to geopandas.

    @author: Michael de Winter.
"""

def __make_the_crop(load_shape, raster_path, raster_path_cropped, plot):
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

    src.close()
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
        src.close()


def add_NDVI(tif_input_file):
    """
    Add a ndvi band to a .tif file.
    
    @param tif_input_file: Path to a .tif file.
    """
    
    inds = rasterio.open(tif_input_file, 'r') 
    meta = inds.meta     
    tile = inds.read() 
    file_to = tif_input_file.replace(".tif","_ndvi.tif")
    meta.update(count = len(tile)+1) 

    ndvi = calculate_nvdi.generate_ndvi_channel(tile)
    inds.close()

    print("Done with calculating NDVI, saving to: "+file_to)
    with rasterio.open(file_to, 'w', **meta) as outds:
                for band in range(0,len(tile)):
                    outds.write_band(band+1,tile[band])        
               
                outds.write_band(len(tile)+1,ndvi)              
                outds.close()

    return file_to 

def add_height(tif_input_file, height_tif_file):
  """

  Adds height(From a lidar data source) and Normalized difference vegetation index (NDVI) as extra bands to a .tif file.

  Exports a new .tif file with _ndvi_height.tif behind it's original file name.

  @param tif_input_file: The tif file where 2 extra bands need to be added.
  @param height_tif_file: The tif file in 2d which shall be added to the tif input file.
  """

  inds = rasterio.open(tif_input_file, 'r') 
  meta = inds.meta
  meta.update(count = 6)   
  tile = inds.read() # TODO is this behaviour similar to inds.read() ? MW: yes
  ndvi = calculate_nvdi.generate_ndvi_channel(tile)
  #normalized_tile = np.array(normalise(tile, channel_normalisation, meta["width"], meta["height"]))  
   
  vegetation_height_data, vegetation_height_transform = get_ahn_data(height_tif_file)
  heightChannel = generate_vegetation_height_channel(vegetation_height_data, vegetation_height_transform, inds.meta["transform"], meta["width"], meta["height"])
 
          
  file_to = tif_input_file.replace(".tif","_ndvi_height.tif")#.split("/")[-1]
  print(file_to)
  
  inds.close()
 
  with rasterio.open(file_to, 'w', **meta) as outds:        
            for band in range(0,len(tile)):
                    outds.write_band(band+1,tile[band]) 
          
            outds.write_band(len(tile)+1,heightChannel)
            outds.close()

  return file_to 



def get_ahn_data(ahn_input_file):

  inds = rasterio.open(ahn_input_file, 'r')        
  vegetation_height_data = inds.read(1)
  vegetation_height_transform = inds.meta["transform"]

  inds.close()
  return vegetation_height_data, vegetation_height_transform

def generate_vegetation_height_channel(vegetation_height_data, vegetation_height_transform, target_transform, target_width, target_height):
        """
        Function to convert a .tif, which was created from a .laz file, into a band which can be used in a raster file with other bands.
        
        @param vegetation_height_data: numpy array from the ahn .tif file.
        @param vegetation_height_transform: transform from the ahn .tif meta data.
        @param target_transform: transform from the satellite .tif meta data.
        @param target_width: The width from the satellite .tif file.
        @param target_height: The height from the satellite .tif file.

        @return a ndvi channel
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

def move_tiff(raster_path_cropped,raster_path_cropped_moved):
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

    src.close()
    return calculate_nvdi.make_ndvi_plot(raster_path_nvdi,raster_path_nvdi,plot)

def run(raster_path, load_shape, output_folder, plot):
    """
        Main run method, combines the cropping of the file based on the shape.

        @param raster_path: path to a raster file.
        @param load_shape: path the file that needs to be cropped.
        @return: the path where the cropped file is stored or where the nvdi is stored.
    """    
    raster_path_cropped_moved = ""
 
    print(f'cropping file {raster_path}')
    logging.info(f'cropping file {raster_path}')
    raster_path_cropped = raster_path.replace(".tif","_"+load_shape.split("/")[len(load_shape.split("/"))-1].split('.')[0]+"_cropped.tif")
    print("New cropped filename: "+raster_path_cropped)
    logging.info("New cropped filename: "+raster_path_cropped)
    __make_the_crop(load_shape,raster_path,raster_path_cropped,plot)
    print(f'finished cropping {raster_path}')
    logging.info(f'Finished cropping file {raster_path}')
    # Path fix and move.
    raster_path_cropped = raster_path_cropped.replace("\\", "/") 
    raster_path_cropped_moved = output_folder+"/"+raster_path_cropped.split("/")[len(raster_path_cropped.split("/"))-1]
    
    move_tiff(raster_path_cropped,raster_path_cropped_moved)

    return raster_path_cropped_moved




