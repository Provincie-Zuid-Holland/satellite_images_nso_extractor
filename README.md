# Introduction

This Python code simplifies data extraction and cropping of satellite image data from the Netherlands Space Office (NSO).

The NSO offers free satellite images of the Netherlands. However, a limitation is that the NSO provides images of large overlapping regions rather than specific areas. This results in unnecessarily large amounts of data, especially if you are only interested in a smaller, specific region. To address this issue, this package includes a cropping feature.

If you only need a few satellite files, the NSO data portal should suffice: [https://www.satellietdataportaal.nl/](https://www.satellietdataportaal.nl/).
However, you will still need to crop the satellite images using another method.

Depending on your purpose, such as for machine learning or A.I. applications, you may need to process a large number of satellite images in a time series and automate the workflow as much as possible. This Python code is designed to meet those needs.


Features of the Python code:

1. Searches the NSO for satellite images containing a selected geographical area defined in a .geojson file. You need to create this .geojson file yourself in WGS84 format. Parameters can be adjusted to control how strictly the area must be contained within the images.
2. Downloads, unzips, and crops the satellite images identified in step 1 to the selected area.
3. Calculates various indices, such as NDVI or NDWI, if this option is enabled.
4. Saves the cropped satellite images as .tif files, with the option to save them as a GeoPandas DataFrame. Unused data is automatically deleted.
   
The image below provides an illustration:
![Alt text](example.png?raw=true "Title")


\*This satellite data is only intended for dutch legal entities, dutch institutions or dutch citizens.
For the license terms of the NSO see this links: [https://www.spaceoffice.nl/nl/satellietdataportaal/toegang-data/licentievoorwaarden/](https://www.spaceoffice.nl/nl/satellietdataportaal/toegang-data/licentievoorwaarden/)

# Getting Started

0. Get a NSO account, register at [https://satellietdataportaal.nl/register.php](https://satellietdataportaal.nl/register.php)
1. First, create or obtain a GeoJSON file representing the region you want to study and crop to. This file defines the geographical boundaries of your area of interest and is essential for the cropping process. Ensure the GeoJSON file uses the WGS84 coordinate system. [Geojson.io](https://geojson.io/#map=8/51.821/5.004) can you help you with that.
2. Make a instance of nso_georegion with instance of the geojson region you have, where you want to store the cropped files and the NSO account based on step 0.
3. Retrieve download links of satellite images which contain the selected region, parameters can be set to how strict this containment should be, if you want to fill missing data in the region with data from a other satellite and/or add extra indexes.
4. Download, unzip and crop the found links.

# Example code

```python
import satellite_images_nso.api.nso_georegion as nso
from settings import nso_username, nso_password, path_geojson,  output_path
# Optional
from settings import height_band_filepath, cloud_detection_model_path, links_must_contain

path_geojson = "/src/example/example.geojson"
output_folder = "./src/output/"

# Make a georegion object
georegion = nso.nso_georegion(
    path_to_geojson=path_geojson, 
    output_folder=output_path,
    username=nso_username,
    password=nso_password,
    )

# This method fetches all the download links with all the satellite images the NSO has which contain the region in the given geojson.
# Max_diff parameters represents the amount of percentage the selected region has to be in the satellite image.
# So 1 is the the selected region has to be fully in the satellite images while 0.5 donates only 50% of the selected region is in the satellite image.
# The start date parameters denotes the datetime the start date of the satellite images.
links = georegion.retrieve_download_links(max_diff=0.5, start_date="2022-01-01")


# This example filters out only 30 cm RGBNED  from all the links
links = links[links['resolution'] == "30cm"]
links = links[links["link"].str.contains("RGBNED")]


# Downloads a satellite image from the NSO, makes a crop out of it so it fits the geojson region and calculates the NVDI index.
# The output will stored in the output folder.
# Look in the python documentation for the values of the parameters.
georegion.execute_link(links[1:2]["link"].values[0], add_ndvi_band = True)

```

See also the jupyter notebook in src/nso_notebook_example.ipynb

# Class diagram

![Alt text](class_diagram.PNG?raw=true "Title")

# Installation

When working with 64x Windows and Anaconda for your python environment management execute the following terminal commands in order:

```sh
conda create -n satellite_images_nso_extractor python=3.12 -y
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

Pieter Kouyzer

Jeroen Esseveld

Daniel Overdevest

Yilong Wen

# Contact

Contact us at vdwh@pzh.nl
