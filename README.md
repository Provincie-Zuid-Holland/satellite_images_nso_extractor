# Introduction

This python code is intended to automate/make easier the data extraction and cropping of satellite image data from the netherlands space office (NSO).
NSO provides free satellite images from the Netherlands, but a downside is that the NSO does not provide satellite images fitted to a specific area but only a large overlapping region.
This leads to a unnecessary large amount of data especially if you only want to study a smaller specific region and as such cropping is needed, which is what this package provides.

This python code does the following steps:

1. Searches the NSO for satellite images which contain a selected geoarea in .geojson file. Parameters can used for how strict this containment should be.
2. Downloads, unzips and crops the satellite image, found in step 1, to the selected area.
3. An option can also be set for calculating the Normalized difference vegetation index (NVDI, used in for example crop analysis) or normalisation of the cropped region as a extra band.
4. Add lidar height data as extra band.
5. Saves the cropped satellite image to a .tif file with the option to also save it as a geopandas dataframe. And deletes the unused data.

This image gives a illustration:
![Alt text](example.png?raw=true "Title")

If you only need a few satellite files, the data portal of the NSO should be enough: [https://www.satellietdataportaal.nl/](https://www.satellietdataportaal.nl/).
Although you still need to crop the satellite image in a other way.

Depending on your purpose however, for example machine learning/A.I, you want to have as much satellite images (in a time series) and automate it as much as possible, for which this python code is also intended.

\*This satellite data is only intended for dutch legal entities, dutch institutions or dutch citizens.
For the license terms of the NSO see this links: [https://www.spaceoffice.nl/nl/satellietdataportaal/toegang-data/licentievoorwaarden/](https://www.spaceoffice.nl/nl/satellietdataportaal/toegang-data/licentievoorwaarden/)

# Getting Started

0. Get a NSO account, register at [https://satellietdataportaal.nl/register.php](https://satellietdataportaal.nl/register.php)
1. First get a GeoJSON file of the selected region you want to study and be cropped to. [Geojson.io](https://geojson.io/#map=8/51.821/5.004) can you help you with that. Note the coordinates have to be in WGS84! ( Which should be standard for a geojson.)
2. Make a instance of nso_georegion with instance of the geojson region you have, where you want to store the cropped files and the NSO account based on step 0.
3. Retrieve download links of satellite images which contain the selected region, parameters can be set to how strict this containment should be.
4. Download, unzip and crop the found links.

# Example code

```python
# This the way the import nso.
import satellite_images_nso.api.nso_georegion as nso
# The sat_manipulator gives other handy manipulations on satellite data .tif files to a geopandas dataframe.
import satellite_images_nso.api.sat_manipulator as sat_manipulator

path_geojson = "/src/example/example.geojson"
output_folder = "./src/output/"
# The first parameter is the path to the geojson, the second the map where the cropped satellite data will be downloaded, the third is your NSO username and the last your NSO password.
georegion = nso.nso_georegion(path_geojson,output_folder,\
                              YOUR_USER_NAME_HERE,\
                             YOUR_PASSWORD_HERE)

# This method fetches all the download links with all the satellite images the NSO has which contain the region in the given geojson.
# Max_diff parameters represents the amount of percentage the selected region has to be in the satellite image.
# So 1 is the the selected region has to be fully in the satellite images while 0.7 donates only 70% of the selected region is in the
links = georegion.retrieve_download_links(max_diff = 0.7)


# This example filters out only 50 cm RGB Infrared Superview satellite imagery in the summer from all the links
season = "Summer"
links_group = []
for link in links:
            if 'SV' in link and '50cm' in link and 'RGBI' in link:
                if sat_manipulator.get_season_for_month(int(link.split("/")[len(link.split("/"))-1][4:6]))[0] == season:
                    links_group.append(link)



# Downloads a satellite image from the NSO, makes a crop out of it so it fits the geojson region and calculates the NVDI index.
# The output will stored in the output folder.
# The parameters are : link, delete_zip_file = False, delete_source_files = True,  plot=True, in_image_cloud_percentage = False,  add_ndvi_band = False, add_height_band = False
# description of these parameters can be found in the code.
georegion.execute_link(links_group[0], add_ndvi_band = True)

# This function reads a .tif file, which is a format in which the satellite data is stored in, and converts it to a pixel based geopandas dataframe.
# Mainly for machine learning purposes.
path_to_vector = "path/to/folder/*.tif"
geo_df_pixel = sat_manipulator.tranform_vector_to_pixel_gpdf(path_to_vector)
```

See also the jupyter notebook in src/nso_notebook_example.ipynb

# Class diagram

![Alt text](class_diagram.PNG?raw=true "Title")

# Installation

When working with 64x Windows and Anaconda for your python environment management execute the following terminal commands in order:

```sh
conda create -n satellite_images_nso_extractor python=3.9 -y
conda activate satellite_images_nso_extractor
pip install -r requirements.txt
```

Navigate to the [satellite-images-nso-datascience repository](https://github.com/Provincie-Zuid-Holland/satellite-images-nso-datascience) and then run:

```sh
pip install .
```

### Additional steps for running postprocessing scripts

Additionally, the postprocessing scripts use the Azure SDK, requiring Azure CLI to log in. Follow the [Microsoft Instructions](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) on how to install the Azure CLI.

# Application

Copy `settings_example.py` and rename to `settings.py`. Change the variables in there as desired and then execute `nso_notebook_example.ipynb`.

# Run as a docker container

```console
docker run -it --entrypoint bash dockerhubpzh/satellite_images_nso_docker
```

See: https://hub.docker.com/r/dockerhubpzh/satellite_images_nso_docker

# Local development

Run `rebuild.bat` to build and install package on local computer.

# Author

Michael de Winter

Jeroen Esseveld

Daniel Overdevest

Yilong Wen

# Contact

Contact us at vdwh@pzh.nl
