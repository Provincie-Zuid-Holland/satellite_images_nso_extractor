FROM osgeo/gdal:latest

RUN apt-get update
RUN apt-get install python3-pip

RUN python -m pip install satellite-images-nso

