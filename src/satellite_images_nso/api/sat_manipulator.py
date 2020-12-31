# Rename to nso_manipulator for more apporiate name.
import satellite_images_nso._manipulation.nso_manipulator as nso_manipulator

def tranform_vector_to_pixel_df(path_to_vector):
    """
        Public wrapper around the nso manipulator.
    """
    return nso_manipulator.tranform_vector_to_pixel_df(path_to_vector )