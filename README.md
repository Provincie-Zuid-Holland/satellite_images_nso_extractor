# Introduction 
This repo can be used to automate extraction/cutting of satellite data from the netherlands space office (NSO).  
Also the NVDI can be calculated on the cut.

# Getting Started

0. Get a NSO account for the satellietdataportaal.nl and fill the .key file with username/password.
1. First GeoJSON file of the region you want to cut. [Geojson.io](https://geojson.io/#map=8/51.821/5.004) can you help you with that.
2. Make a instance of nso_geojsonregion with instance of the geojson region you have, where you want to store the cropped files and the NSO account based on step 0.
2. Retrieve download links for the specific region you want to have.
3. Download the found links.

# Example code.

```python
# This the way the import nso.
import satellite_images_nso.api.nso_georegion as nso
path_geojson = "./TheHague.geojson"
# The first parameter is the path to the geojson, the second the map where the cropped satellite data will be installed
georegion = nso.nso_georegion(path_geojson,"C:/repos/Output/",\
***REMOVED***YOUR_USER_NAME_HERE,\
                             YOUR_PASSWORD_HERE)
links = georegion.retrieve_download_links()
georegion.execute_link(links[0])
```

# Installation.

Install this package with: `pip install satellite_images_nso`

Be sure you've installed GDAL already on your computer. Other python dependencies will install automatically (Fiona>=1.8.13, GDAL>=3.0.4, geopandas>=0.7.0, rasterio>=1.1.3 Shapely>=1.7.0)

## Install GDAL on Windows
If you are a Windows user you have to install the GDAL dependency yourself via a wheels.

Instead install these wheels with pip install XXX.XX.XX.whl.

Go to https://www.lfd.uci.edu/~gohlke/pythonlibs/ for the wheels of these depencies:

Depencencies are : "Fiona>=1.8.13", "GDAL>=3.0.4", "geopandas>=0.7.0","rasterio>=1.1.3","Shapely>=1.7.0"

## Install GDAL on MacOS
Install GDAL by using Brew:  
`brew install GDAL`

# Local development
Run `rebuild.bat` to build and install package on local computer.




# Author
Michael de Winter

