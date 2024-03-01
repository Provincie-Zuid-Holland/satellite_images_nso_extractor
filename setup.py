from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="satellite_images_nso",  # Replace with your own username
    version="2.0.0",
    author="Michael de Winter",
    author_email="m.r.dewinter88@live.nl",
    description="NSO Satellite Extractor and cropper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ProvZH/satellite_images_nso",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "requests>=2.25.0",
        "objectpath>=0.6.1",
        "earthpy>=0.9.2",
        "Fiona>=1.9.5",
        "geopandas>=0.14.3",
        "rasterio>=1.3.9",
        "Shapely>=2.0.3",
    ],
)
