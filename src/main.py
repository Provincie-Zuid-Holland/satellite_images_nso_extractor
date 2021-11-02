import satellite_images_nso.api.nso_georegion as nso

nso_username = 'micwin'
nso_password = 'REDACTED'

# give path to geojson en output,!!!!! rewrite these directories to your file system!!!!
path_geojson = "C:/repos/github/satellite_images_nso/input_data/waterleidingduin_aaneensluitende_polygon.geojson"
output_path = "C:/repos/github/satellite_images_nso/output"

print("I am running")
# This method fetches all the download links to all the satelliet images which contain region in the geojson
georegion = nso.nso_georegion(path_geojson,output_path,\
***REMOVED***nso_username,\
                            nso_password)

links = georegion.retrieve_download_links()

print("Results:")
print(links)