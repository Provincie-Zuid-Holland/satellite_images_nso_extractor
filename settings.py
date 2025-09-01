import os

from dotenv import load_dotenv

load_dotenv()

# get credentials
nso_username = os.getenv("NSO_USERNAME", "")
nso_password = os.getenv("NSO_PASSWORD", "")

# give path to geojson, height_band (ahn) file, output path folder and cloud_detection_model_path
path_geojson = "path/to/geojson_file"

output_path = "path/to/output_tif_files"

# optional
height_band_filepath = "path/to/height_band_file"
cloud_detection_model_path = "path/to/cloud_detection_model"

links_must_contain = (
    os.getenv("LINKS_MUST_CONTAIN", "").split(",")
    if os.getenv("LINKS_MUST_CONTAIN")
    else []
)
account_url = os.getenv("ACCOUNT_URL", "")

# Test data path
path_test_input_data = os.getenv("PATH_TEST_INPUT_DATA", "")
