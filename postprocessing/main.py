import satellite_images_nso.api.nso_georegion as nso
from settings import nso_username, nso_password, path_geojson, output_path
import shapely
import json

georegion = nso.nso_georegion(
    path_to_geojson=path_geojson,
    output_folder=output_path,
    username=nso_username,
    password=nso_password,
)

links = georegion.retrieve_download_links(max_diff=0.5, start_date="2022-01-01")
links = links.sort_values("percentage_geojson")

georegion.execute_link(
    links[1:2]["link"].values[0],
    fill_with_nearest_date=True,
    fill_coordinates=json.loads(
        shapely.to_geojson(links[1:2]["missing_polygon"].values[0])
    )["coordinates"],
)
