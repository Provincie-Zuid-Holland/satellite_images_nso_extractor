from azure.storage.blob import ContainerClient
import pandas as pd


def get_container(connection_string = False, container_name = False):
    """
        Get the current container account for remote sensing.
    """
    
    container = ContainerClient.from_connection_string(conn_str=connection_string,\
***REMOVED***                     container_name=container_name)***REMOVED***                 
    return container

def create_df_current_tiff_files(blob_url, container):
    """
        Create a pandas dataframe of the current .tif stored in the blob storage.
        Basically it stores meta data about the cut off .tif images in the databases.
    """
    urls = []
    filenames = []

    for blob in container.list_blobs():
        if '.tif' in blob['name']:
            urls.append(blob_url+"/"+blob['container']+"/"+blob['name'])
            filenames.append(blob['name'])

    df_filenames = pd.DataFrame(filenames, columns=['filename'])
    df_filenames['datetime']=  df_filenames['filename'].str.split("_").str[0]+" "+df_filenames['filename'].str.split("_").str[1]
    df_filenames['download_urls'] = urls

    return df_filenames


def upload_file_rm_blob(path_to_file,container, name):

    with open(path_to_file, "rb") as data:      
        container.upload_blob(name,data)

