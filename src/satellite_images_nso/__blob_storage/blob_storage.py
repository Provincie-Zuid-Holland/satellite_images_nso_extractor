from typing import Container
from azure.storage.blob import ContainerClient
import pandas as pd



class blob_container:

    def __init__(self, connection_string: str, container_name: str):
        """
            Init a blob storage container.
        """

        self.container = ContainerClient.from_connection_string(conn_str=connection_string,\
                                                   container_name=container_name)      


    def create_df_current_tiff_files(self,blob_url,folder =""):
        """
            Create a pandas dataframe of the current .tif stored in the blob storage.
            Basically it stores meta data about the cut off .tif images in the databases.
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


    def upload_file_rm_blob(self,path_to_file,container, name):

        with open(path_to_file, "rb") as data:      
            self.container.upload_blob(name,data)

    def get_container(self):
        return self.container