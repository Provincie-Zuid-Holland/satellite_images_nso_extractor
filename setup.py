from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="satellite_images_nso_extractor",
    version="2.0.0",
    author="Michael de Winter",
    author_email="m.r.dewinter88@live.nl",
    description="NSO Satellite Extractor and cropper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Provincie-Zuid-Holland/satellite_images_nso_extractor",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
