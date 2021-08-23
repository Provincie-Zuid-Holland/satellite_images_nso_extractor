# Rename to nso_manipulator for more apporiate name.
import satellite_images_nso._manipulation.nso_manipulator as nso_manipulator

def tranform_vector_to_pixel_gpdf(path_to_vector):
    """
        Public wrapper around the nso manipulator for transforming a vector to a pixel geoDataFrame.

        @path_to_vector: Path to a .tiff file.
    """
    return nso_manipulator.tranform_vector_to_pixel_df(path_to_vector)


def crop_nso_satellite_image(shape_file, path_to_tiff_file, output_path):
    """ 
        Public wrapper around the nso manipulator to make a cut out of a NSO satellite image.

        @oaram shape_file: Path to a geojson file.
        @param path_to_tiff_file: Path to a tiff file to be cut.
        @param output_path: Where the cut should be stored.
    """
    return nso_manipulator.__make_the_cut(shape_file, path_to_tiff_file, output_path)


def get_season_for_month(month):
    """
        A function that retrieves the season for a month/

        @param a int month     
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