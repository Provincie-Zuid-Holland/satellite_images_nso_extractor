"""
This is for normalisation of satellite images.
Which is import because of atmospheric corretion.

Based on the following literature:
https://esajournals.onlinelibrary.wiley.com/doi/full/10.1002/ecy.1730

"The second approach uses pseudo invariant features
(PIF; generally consisting of one or more pixels) or pseudo
invariant targets (PIT; generally a single pixel), where nonchanging features or targets in the overlapping area are
used to bring the images to a common scale (Schott et al.
1988). These pseudo invariant features/targets can be
selected manually or automatically through statistical
algorithms (Du et al. 2002, Bao et al. 2012). Comparisons
have shown that performing a relative correction might
provide more accurate results than an absolute atmospheric correction, especially when comparability is more
important than the pixel value (Schroeder et al. 2006).
Furthermore, some studies have performed relative correction of atmospherically corrected imagery to account
for residual differences between images arising from
imperfect preprocessing when surface reflectance is desired
(Li et al. 2014). We suggest this approach only if both comparability between images and surface reflectance units are
needed for a particular application. If the objective is to
obtain images that are spatially or temporally consistent
(and that is the only goal of the relative correction), then
relative correction from a more basic preprocessing level,
such as DN or TOA, would be the most appropriate
option, as correcting to surface reflectance serves no
purpose and injects a potential source of error."

So here we use relative multi date normalisation. 
We here have our custom coefficients, make your own coefficients for your own images.

@author: Michael de Winter.
"""
from satellite_images_nso._manipulation import nso_manipulator
from satellite_images_nso.__logger import logger_nso
import pandas as pd
from matplotlib import pyplot
import rasterio
import numpy as np 
from numpy import median
import glob 
import os
import io
import requests
import platform
import time


"""
    Helper functions.
"""

logger = logger_nso.init_logger()


def __get_season_for_month(month):
    """
        This method get the season for a specific month for a number of a month.

        @param month: A month in number
        @return the season in string format, and the season in string format.
    """
    
    season = int(month)%12 // 3 + 1
    season_str = ""
    if season == 1:
        season_str = "Winter"
    if season == 2:
        season_str = "Spring"
    if season == 3:
        season_str = "Summer"
    if season == 4 :
        season_str = "Fall"
    return season_str, season

def __creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime  

def __is_file_older_than_x_days(file, days=1): 
    """
    
    Comparison check to see if a file is older than a  couple of days.

    @param file: Path to a file to check if it's older than specific date.
    @param days: The days which are older to check.
    """
    file_time = __creation_date(file) 
    # Check against 24 hours 
    return ((time.time() - file_time) / 3600 > 24*days) 

"""
     End helper functions.
""" 


def extract_multi_date_normalisation_coefficients(path_to_tif_files):
    """ 
        This method generates coefficients for a folder of .tif files.

        @param path_to_tif_files: Path to a folder where all the .tif files are located.
        @return: A pandas dataframe with the median 75th quantiles.
    """

    multidate_coefficents = pd.DataFrame([],columns=["Season","Blue_median_75", "Green_median_75", "Red_median_75", "Nir_median_75"])
    for season_cur in ["Winter","Summer","Spring","Fall"]:
      
        blue_count = []
        green_count = []
        red_count = []
        nir_count = []
        count = 0
        for file in glob.glob(path_to_tif_files+"*"):
            if ".csv" not in file:
                season = __get_season_for_month(file.split("/")[-1][4:6])[0]

                if season == season_cur:
                    df = nso_manipulator.tranform_vector_to_pixel_df(file)
                    #print("-----file: "+str(file)+"--------")
                    #print(df['green'].min())
                    #print(df['blue'].min())
                    #print(df['red'].min())
                    #print(df['nir'].min())
                    #print(df[['blue','green','red','nir']].min())
                    #print(df[['blue','green','red','nir']].max())
                    #print(df[['blue','green','red','nir']].quantile(0.75))
                    #src = rasterio.open(file).read()
                    #plot_out_image = np.clip(src[2::-1],
                    #            0,2200)/2200
                    blue_mean_add, green_mean_add, red_mean_add, nir_mean_add =  df[['blue','green','red','nir']].quantile(0.75)
                    blue_count.append(blue_mean_add)
                    green_count.append(green_mean_add)
                    red_count.append(red_mean_add)
                    nir_count.append(nir_mean_add)

                    #rasterio.plot.show(plot_out_image)
                    #pyplot.show()
               
        print("----------- Season Medians 75 percentile----:"+season_cur)
        blue_count_median = median(blue_count)
        green_count_median = median(green_count)
        red_count_median = median(red_count)
        nir_count_median = median(nir_count)
    
        print("--Blue_median:"+str(blue_count_median))
        print("--Green_median:"+str(green_count_median))
        print("--Red_median:"+str(red_count_median))
        print("--NIR_median:"+str(nir_count_median))

        multidate_coefficents.loc[len(multidate_coefficents)] =  [season_cur, blue_count_median, green_count_median, red_count_median, nir_count_median]
        
    return multidate_coefficents

    


def multidate_normalisation_75th_percentile(path_to_tif):
    """
        Normalisa a .tif file based on 75th percentile point.

        @param path_to_tif: Path to a .tif file.
        @return: returns a .tif file with 75th percentile normalisation.
    """


    script_dir = os.path.dirname(__file__)
    coefficients = script_dir+"/coefficients/Multi-date-index-coefficients_pd.csv"
    multidate_coefficents = ""

    if __is_file_older_than_x_days(coefficients,1) == True:
      
        # Check the PZH blob storage for the most recent multi data coefficients.
        url="https://a804bee12d94d498fbfe55e2.blob.core.windows.net/satellite-images-nso/coefficients/Multi-date-index-coefficients_pd.csv"
        s=requests.get(url).content

        if s is not None and s != '':
            print("Downloading most recent coefficients")
            logger.info("Downloading most recent coefficients")
            multidate_coefficents = pd.read_csv(io.StringIO(s.decode('utf-8')))
    if multidate_coefficents == "":
        print("Using local coefficients")
        logger.info("Using local coefficients")
        multidate_coefficents = pd.read_csv(script_dir+"/coefficients/Multi-date-index-coefficients_pd.csv")

    season = __get_season_for_month(path_to_tif.split("/")[-1][4:6])[0]
    multidate_coefficents = multidate_coefficents[multidate_coefficents['Season'] == season]
 
    print("-------- Multi-date Relative Normalisation for file: \n"+path_to_tif)

    df = nso_manipulator.tranform_vector_to_pixel_df(path_to_tif)
    blue_mean_current, green_mean_current, red_mean_current, nir_mean_current =  df[['blue','green','red','nir']].quantile(0.75)
    
    blue_diff_add = multidate_coefficents['Blue_median_75'].values[0]-blue_mean_current
    green_diff_add = multidate_coefficents['Green_median_75'].values[0]-green_mean_current
    red_diff_add = multidate_coefficents['Red_median_75'].values[0]-red_mean_current
    nir_diff_add = multidate_coefficents['Nir_median_75'].values[0]-nir_mean_current
      
    src = rasterio.open(path_to_tif).read(masked=True)
    meta = rasterio.open(path_to_tif).meta.copy()
      
    fig, (axrgb, axhist) = pyplot.subplots(1, 2, figsize=(14,7))
    plot_out_image = np.clip(src[2::-1],
                    0,2200)/2200

    rasterio.plot.show(plot_out_image, ax=axrgb, title="Original")
      
    src[0] = src[0]+blue_diff_add
    src[1] = src[1]+green_diff_add 
    src[2] = src[2]+red_diff_add 
    src[3] = src[3]+nir_diff_add 
      
    ahn_outpath = path_to_tif.split(".")[0]+"_"+str(season)+"_normalised.tif"

      
    print("Saving file to:")
    print(ahn_outpath)
     
    plot_out_image_2 = np.clip(src[2::-1],
                    0,2200)/2200
    
    rasterio.plot.show(plot_out_image_2, ax=axhist, title="Multi-date Relative Normalisation")
    pyplot.show()
      
    with rasterio.open(ahn_outpath, 'w', **meta) as outds:        
        outds.write(src)


def multi_date_dark_spot_normalisation(path_to_tif, satellite_image_name = False, X_specific_point = False, Y_specific_point =False, ):
    """
        Black point normalisation based on the most darkest point in the landsat image.
        Save a new .tif file with the normalisation.

        The coefficients are again pre calculated, if you wish to use your own replace the black point coefficients .csv file.
    
        @param path_to_tif: Path to the .tif to be used.
        @param X_specific_point: X coordinates of a specific point in the .tif file on which you want to normalize. In RD coordinates!
        @param Y_specific_point: Y coordinates of a specific point in the .tif file on which you want to normalize. In RD coordinates!
    """

    script_dir = os.path.dirname(__file__)
    coefficients = script_dir+"/coefficients/dark-spot-coefficients_pd.csv"
   
    dark_spot_coefficents = pd.DataFrame()

    if __is_file_older_than_x_days(coefficients,1) == True:
      
        # Check the PZH blob storage for the most recent multi data coefficients.
        url="https://a804bee12d94d498fbfe55e2.blob.core.windows.net/satellite-images-nso/coefficients/dark-spot-coefficients_pd.csv"
        s=requests.get(url).content
        if s is not None and s != '':
            print("Downloading most recent coefficients")
            logger.info("Downloading most recent coefficients")
            dark_spot_coefficents = pd.read_csv(io.StringIO(s.decode('utf-8')))

    if dark_spot_coefficents.empty:
        print("Using local coefficients")
        logger.info("Using local coefficients")
        script_dir = os.path.dirname(__file__)
        dark_spot_coefficents = pd.read_csv(script_dir+"/coefficients/dark-spot-coefficients_pd.csv")
    
    print("-------- Dark Spot Normalisation for file: \n"+path_to_tif)
    df = nso_manipulator.tranform_vector_to_pixel_df(path_to_tif)

    blue_diff_add = 0
    green_diff_add = 0
    red_diff_add = 0
    nir_diff_add = 0

    if X_specific_point == False:

        if  satellite_image_name != False:
          
            print(satellite_image_name)
            dark_spot_coefficents_file = dark_spot_coefficents[dark_spot_coefficents['filename'].str.contains(satellite_image_name)]
            if dark_spot_coefficents_file.empty:
                print("No coefficients found for satellite image! Defaulting to nothing!")
                logger.info("No coefficients found for satellite image! Defaulting to nothing!")
            else:
                blue_diff_add = dark_spot_coefficents_file['blue_coefficients'].values[0]
                green_diff_add = dark_spot_coefficents_file['green_coefficients'].values[0]
                red_diff_add = dark_spot_coefficents_file['red_coefficients'].values[0]
                nir_diff_add = dark_spot_coefficents_file['nir_coefficients'].values[0]


    else:
        blue_current,green_current,red_current,nir_current = df[(round(df['Y'],6) == round(Y_specific_point,6)) & (round(df['X'],6) == round(X_specific_point,6))]
        blue_diff_add = dark_spot_coefficents['blue_coefficients'].values[0]-blue_current
        green_diff_add = dark_spot_coefficents['green_coefficients'].values[0]-green_current
        red_diff_add = dark_spot_coefficents['red_coefficients'].values[0]-red_current
        nir_diff_add = dark_spot_coefficents['nir_coefficients'].values[0]-nir_current

   

    print(blue_diff_add, green_diff_add, red_diff_add, nir_diff_add )
    src = rasterio.open(path_to_tif).read(masked=True)
    meta = rasterio.open(path_to_tif).meta.copy()
      
    fig, (axrgb, axhist) = pyplot.subplots(1, 2, figsize=(14,7))
    plot_out_image = np.clip(src[2::-1],
                    0,2200)/2200

    rasterio.plot.show(plot_out_image, ax=axrgb, title="Original")
      
    src[0] = src[0]+blue_diff_add
    src[1] = src[1]+green_diff_add 
    src[2] = src[2]+red_diff_add 
    src[3] = src[3]+nir_diff_add 
      
    ahn_outpath = path_to_tif.split(".")[0]+"_dark_point_normalised.tif"

      
    print("Saving file to:")
    print(ahn_outpath)
    logger.info("Saving file to:")
    logger.info(ahn_outpath)
     
    plot_out_image_2 = np.clip(src[2::-1],
                    0,2200)/2200
    
    rasterio.plot.show(plot_out_image_2, ax=axhist, title="Multi-date Dark Point Relative Normalisation")
    pyplot.show()
      
    with rasterio.open(ahn_outpath, 'w', **meta) as outds:        
        outds.write(src)