# Introduction 
This repo can be used to automate extraction/cutting of satellite data from the netherlands space office (NSO).
Also the NVDI can be calculated on the cut.

# Getting Started

0. Get a NSO account and fill the .key file with username/password.
1. First select a region with want to have and make a geojson for it.
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
```


# Author
Michael de Winter

