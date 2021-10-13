from typing import Container
from azure.storage.blob import ContainerClient
import pandas as pd
from os import path
"""

Class for working with Azure blob storage.

Used for downloading and checking if files where already uploaded to blobstorage.


@Author: Michael de Winter, Jeroen Esseveld

"""
class blob_container:

    def __init__(self, connection_string: str, container_name: str):
        """
            Init a blob storage container.
        """

        self.container = ContainerClient.from_connection_string(conn_str=connection_string,\
***REMOVED***                     container_name=container_name)      


    def create_df_current_tiff_files(self,blob_url,folder =""):
        """
            Create a pandas dataframe of the current .tif stored in the blob storage.
            Basically it stores meta data about the cropped .tif images in the databases.
        """
        urls = []
        filenames = []

        for blob in self.container.list_blobs(prefix = folder):
            if '.tif' in blob['name']:
                urls.append(blob_url+"/"+blob['container']+"/"+blob['name'])
                filenames.append(blob['name'])

        df_filenames = pd.DataFrame(filenames, columns=['filename'])
        df_filenames['datetime']=  df_filenames['filename'].str.split("_").str[0]+" "+df_filenames['filename'].str.split("_").str[1]
        df_filenames['download_urls'] = urls

        return df_filenames


    def upload_file_rm_blob(self,path_to_file, name):

        with open(path_to_file, "rb") as data:      
            self.container.upload_blob(name,data)

    def get_container(self):
        return self.container
    
    def check_new_tiff_file(owned_files, nso_files):
        """
            Check whether NSO provides new tiff files with respect to the list of stored tiff files.
        """
        owned_files = "#".join([path.basename(file) for file in owned_files])
        nso_files = [path.basename(file) for file in nso_files]
        return list(filter(lambda x: x not in owned_files, nso_files))
