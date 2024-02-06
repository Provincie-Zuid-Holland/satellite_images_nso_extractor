import glob

import satellite_images_nso._manipulation.nso_manipulator as nso_manipulator

# Set variables
ahn_height_filepath = "C:/Users/pzhadmin/Data/remote-sensing/ahn/ahn4_voornes_duin.tif"
filepath_regex = (
    "E:/Data/remote_sensing/satellite-images/PNEO_30CM/Voornes Duin/*crop.tif"
)

# Add height to files in filepath_regex
for file in glob.glob(filepath_regex):
    print(file)
    cropped_path = nso_manipulator.add_height(file, ahn_height_filepath)
