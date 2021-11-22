# Introduction 
This python code is intended to automate/make easier the data extraction and cropping of satellite data from the netherlands space office (NSO).
NSO provides free satellite images from the Netherlands, but a downside however is that the NSO provides very large regions and as such a very large data size files.
This leads to a unnecessary large amount of data especially if you only want to study a smaller specific region.

If you only need a few satellite files the data portal of the NSO should be enough: [https://www.satellietdataportaal.nl/](https://www.satellietdataportaal.nl/).
Depending on your purpose however, for example machine learning, you want to have as much satellite images (in a time series) as possible, for which this python code is intended.

This python code does the following steps, which can be done in a loop.
1. Searches the NSO for satellite images which contain the selected area. Parameters can used for how strict this containment should be.
2. Crops the satellite image, found in step 1, to the selected area.
3. A option can also be set for calculating the Normalized difference vegetation index (NVDI, used in for example crop analysis) or normalisation of the cropped region.
4. Saves to cropped satellite image to a .tif file with A option to also save it as a geopandas dataframe.



This image gives a illustration: 
![Alt text](example.png?raw=true "Title")






*This satellite data is only intended for dutch legal entities, dutch institutions or dutch citizens.
For the license terms of the NSO see this links: [https://www.spaceoffice.nl/nl/satellietdataportaal/toegang-data/licentievoorwaarden/](https://www.spaceoffice.nl/nl/satellietdataportaal/toegang-data/licentievoorwaarden/)

# Getting Started

0. Get a NSO account, register at [https://satellietdataportaal.nl/register.php](https://satellietdataportaal.nl/register.php)
1. First get a GeoJSON file of the selected region you want to study and be cropped to. [Geojson.io](https://geojson.io/#map=8/51.821/5.004) can you help you with that. Note the coordinates have to be in WGS84! ( Which should be standard for a geojson.) 
2. Make a instance of nso_georegion with instance of the geojson region you have, where you want to store the cropped files and the NSO account based on step 0.
2. Retrieve download links of satellite images which contain the selected region, parameters can be set to how strict this containment should be. 
3. Download the found links.

# Example code.

```python
# This the way the import nso.
import satellite_images_nso.api.nso_georegion as nso
# The sat_manipulator gives other handy transmations on satellite data .tif files to a geopandas dataframe.
import satellite_images_nso.api.sat_manipulator as sat_manipulator

path_geojson = "/src/example/example.geojson"
output_folder = "./src/output/"
# The first parameter is the path to the geojson, the second the map where the cropped satellite data will be downloaded, the third is your NSO usernamen and the last your NSO password.
georegion = nso.nso_georegion(path_geojson,output_folder,\
                              YOUR_USER_NAME_HERE,\
                             YOUR_PASSWORD_HERE)

# This method fetches all the download links with all the satelliet images the NSO has which contain the region in the given geojson.
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



# Downloads a satelliet image from the NSO, make a crop out of it so it fits the geojson region and calculate the NVDI index.
# The output will stored in the output folder.
# The parameters are : execute_link(self, link, calculate_nvdi = True,  delete_zip_file = True, delete_source_files = True, check_if_file_exists = True, relative_75th_normalize = False)
# description of these parameters can be found in the code.
georegion.execute_link(links_group[0])

# This function reads a .tif file, which is a format in which the satellite data is stored in, and converts it to a pixel based geopandas dataframe.
# Mainly for machine learning purposes.
path_to_vector = "path/to/folder/*.tif"
geo_df_pixel = sat_manipulator.tranform_vector_to_pixel_gpdf(path_to_vector)
```
See also the jupyter notebook in src/nso_notebook_example.ipynb
# Installation.

Install this package with: `pip install satellite_images_nso`

Be sure you have installed the required packages, follow the instructions below.
## Install GDAL on Windows
If you are a Windows user you have to install the GDAL dependency yourself via a wheels.

Instead install these wheels with pip install XXX.XX.XX.whl.

Go to https://www.lfd.uci.edu/~gohlke/pythonlibs/ for the wheels of these depencies:
 
Depencencies are : "Fiona>=1.8.13", "GDAL>=3.0.4", "geopandas>=0.9.0","rasterio>=1.1.3","Shapely>=1.7.0"
NOTE: You can't use normal pip for the installation of any of these depencies or else they won't find GDAL. So use all the .whl files!
Then follow the fourth solution on this stackoverflow question:
https://gis.stackexchange.com/questions/2276/installing-gdal-with-python-on-windows


# Install GDAL on Databricks
If you are using databricks use this code to set up a init script which installs GDAL.

```python
    dbutils.fs.mkdirs("dbfs:/databricks/FileStore/init_script")
    dbutils.fs.put("/databricks/FileStore/init_script/gdal.sh","""
        #!/bin/bash
        set -ex
        /databricks/python/bin/python -V
        ./databricks/conda/etc/profile.d/conda.sh
        conda activate /databricks/python
        conda install -y gdal""", True)
```

## Install GDAL on MacOS
Install GDAL by using Brew:  
`brew install GDAL`

# Run as a docker container
```console
docker run -it --entrypoint bash dockerhubpzh/satellite_images_nso_docker
```
See: https://hub.docker.com/r/dockerhubpzh/satellite_images_nso_docker

# Local development
Run `rebuild.bat` to build and install package on local computer.




# Author
Michael de Winter

Daniel Overdevest

Yilong Wen

# Contact

Contact us at vdwh@pzh.nl

