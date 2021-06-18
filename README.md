# Introduction 
This python code is intended to automate/make easier the data extraction and cutting of satellite data from the netherlands space office (NSO).
NSO provides free satellite images from the Netherlands, a downside however is that the NSO provides a very large region and as such a very large data file.
This leads to a unnecessary large amount of data especially if you only want to study a smaller specific region.

This python code cuts a selected region out of the original satellite image based on a geojson, provided that the selected region is smaller than the original file.
And then saves this cutout thus reducing the unnecessary saved data. 
A option can also be set for calculating the Normalized difference vegetation index (NVDI, used in for example crop analysis) of the cutout region.
We are working on extracting more variables on satellite images!

This image gives a illustration: 
![Alt text](example.png?raw=true "Title")



# Getting Started

0. Get a NSO account, register at [https://satellietdataportaal.nl/register.php](https://satellietdataportaal.nl/register.php)
1. First get a GeoJSON file of the region you want to cut. [Geojson.io](https://geojson.io/#map=8/51.821/5.004) can you help you with that. Note the coordinates have to be in WGS84! ( Which should be standard for a geojson.) 
2. Make a instance of nso_geojsonregion with instance of the geojson region you have, where you want to store the cropped files and the NSO account based on step 0.
2. Retrieve download links for the specific region you want to have.
3. Download the found links.

# Example code.

```python
# This the way the import nso.
import satellite_images_nso.api.nso_georegion as nso
path_geojson = "/src/example/example.geojson"
# The first parameter is the path to the geojson, the second the map where the cropped satellite data will be installed
georegion = nso.nso_georegion(path_geojson,"/src/output/",\
                              YOUR_USER_NAME_HERE,\
                             YOUR_PASSWORD_HERE)

# This method fetches all the download links to all the satelliet images which contain the region in the geojson.
# Filter out for which satellite you want to download links from! SV for example stands for the Suoerview satellite
links = georegion.retrieve_download_links()


# Downloads a satelliet image from the NSO, make a crop out of it so it fits the geojson region and calculate the NVDI index.
# The output will stored in the designated output folder.
georegion.execute_link(links[0])
# The parameters are : execute_link(self, link, delete_zip_file = True, delete_source_files = True, check_if_file_exists = True)
# With the parameters you can decide if you want to keep the original satellite files, such  as wether to keep the downloaded zip file or the extracted source files from which the cutout will be made.

# The sat_manipulator gives other handy transmations on satellite data.
import satellite_images_nso.api.sat_manipulator as sat_manipulator

# This function reads a .tif file, which is a format the satellite data is stored in,  and converts it to a pixel based geopandas dataframe.
# For machine learning purposes.
path_to_vector = "path/to/folder/*.tif"
geo_df_pixel = sat_manipulator.tranform_vector_to_pixel_gpdf(path_to_vector)
```
See also the jupyter notebook in src/nso_notebook_example.ipynb
# Installation.

Install this package with: `pip install satellite_images_nso`

Be sure you've installed GDAL already on your computer. Other python dependencies will install automatically (Fiona>=1.8.13, GDAL>=3.0.4, geopandas>=0.9.0, rasterio>=1.1.3 Shapely>=1.7.0).
Or look into the requirements.txt file.

If you don't have gdal installed on your computer or if it doesn't work follow the instruction below.

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

