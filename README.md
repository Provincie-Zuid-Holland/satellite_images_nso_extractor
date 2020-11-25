# Introduction 
This program can be used to automate/make easier the extraction/cutting of satellite data from the netherlands space office (NSO).
NSO provides free satellite data for the Netherlands, a downside however is that the NSO provides a very large region and as such a very large file.
This leads to a large amount of unnecessary data, if you only want to study a specific region.

This repo cuts a selected region out of the original file, provided that the selected region is smaller than the original file.
While also calculating the NVDI the cutout region.

# Getting Started

0. Get a NSO account, register at https://satellietdataportaal.nl/register.php.
1. First select a region with want to have and make a geojson for it, you can use 
2. Make a instance of nso_geojsonregion with instance of the geojson region you have, where you want to store the cropped files and the NSO account based on step 0.
2. Retrieve download links for the specific region you want to have.
3. Download the found links.


# Installation.

Install the setup file with pip install setup.py.

Or run the rebuild.bat file.

If you are a windows user you have to install the depencies yourself via wheels.

Instead install these wheels with pip install XXX.XX.XX.whl.

Go to https://www.lfd.uci.edu/~gohlke/pythonlibs/ for the wheels of these depencies:
 
Depencencies are : "Fiona>=1.8.13", "GDAL>=3.0.4", "geopandas>=0.7.0","rasterio>=1.1.3","Shapely>=1.7.0"
# Example code.

```
# This the way the import nso.
import satellite_images_nso.api.nso_georegion as nso
path_geojson = "C:/repos/satellite_images/nso/data/solleveld_sweco.geojson"
# The first parameter is the path to the geojson, the second the map where the cropped satellite data will be installed
georegion = nso.nso_georegion(path_geojson,"C:/repos/Output/",\
                              YOUR_USER_NAME_HERE,\
                             YOUR_PASSWORD_HERE)

# This method fetches all the download links to all the satelliet images which contain region in the geojson.
links = georegion.retrieve_download_links()

# Downloads a satelliet image from the NSO, make a crop out of it so it fits the geojson region and calculate the NVDI index.
# The output will stored in the designated output folder.
georegion.execute_link(links[0])
```


# Author
Michael de Winter

