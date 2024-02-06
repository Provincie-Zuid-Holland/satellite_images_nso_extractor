import os

import rasterio
import tqdm
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, BlobServiceClient, ContainerClient
from settings import account_url

# Set variables
default_credential = DefaultAzureCredential()
container_name = "satellite-images-nso"
blob_files_start_with = "SV_50cm/Meijendel & Berkheide/2"
blob_suffix = "ndvi_height.tif"
folder_path = "E:/Data/remote_sensing/satellite-images/temp"
column_names = ("r", "g", "b", "i", "ndvi", "height")

# Create the BlobServiceClient object
blob_service_client = BlobServiceClient(account_url, credential=default_credential)
container_client = blob_service_client.get_container_client(container=container_name)

print("\nUpdating tif files meta data...")

# List the blobs in the container
blob_list = container_client.list_blobs(name_starts_with=blob_files_start_with)
blob_list = list(blob_list)
blob_list = [blob for blob in blob_list if blob_suffix in blob.name]

# Update tif files in blob storage with column_names and interleave = band and tiled = True
for i in tqdm.tqdm(range(len(blob_list))):
    blob = blob_list[i]
    filename = os.path.split(blob.name)[-1]
    local_filepath = os.path.join(folder_path, filename)
    print(f"\nStarted on {blob.name}")

    print("Downloading file")
    if not os.path.exists(local_filepath):
        with open(file=local_filepath, mode="wb") as target_filepath:
            download_stream = container_client.download_blob(blob.name)
            target_filepath.write(download_stream.readall())

    print("Update file with new meta data")
    local_filepath_new = local_filepath.replace(".tif", "_new.tif")
    with rasterio.open(local_filepath, "r") as src:
        profile = src.profile
        profile.update({"interleave": "band", "tiled": True})

        with rasterio.open(local_filepath_new, "w", **profile) as dest:
            dest.write(src.read())
            dest.descriptions = column_names

    print("Upload file")
    with open(file=local_filepath_new, mode="rb") as bitstream:
        container_client.upload_blob(name=blob.name, data=bitstream, overwrite=True)

    print("Clean up local files")
    os.remove(local_filepath_new)
    os.remove(local_filepath)
