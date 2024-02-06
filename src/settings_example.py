# get credentials
nso_username = ""
nso_password = ""

# give path to geojson, height_band (ahn) file, output path folder and cloud_detection_model_path
path_geojson = ""
height_band_filepath = ""
output_path = ""
cloud_detection_model_path = None

links_must_contain = []  # i.e. ["SV", "50cm", "RGBI", "2022"]
account_url = (
    ""  # blob storage account url, only relevant when using postprocessing scripts
)
