import os

from dotenv import load_dotenv

load_dotenv()

# get credentials from the .env file, be sure to set them!
nso_username = os.getenv("NSO_USERNAME", "")
nso_password = os.getenv("NSO_PASSWORD", "")

# Base directory for tests (relative to this file)
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.dirname(_tests_dir)

# Test data paths - use environment variables or fallback to relative paths
path_test_input_data = os.getenv(
    "TEST_INPUT_DATA_PATH", os.path.join(_tests_dir, "test_data")
)
if not path_test_input_data.endswith(os.sep):
    path_test_input_data += os.sep

path_geojson = os.getenv(
    "PATH_GEOJSON", os.path.join(path_test_input_data, "Test_region.geojson")
)
height_band_filepath = os.getenv("HEIGHT_BAND_FILEPATH", "")
output_path = os.getenv("TEST_OUTPUT_PATH", os.path.join(_tests_dir, "output"))
cloud_detection_model_path = os.getenv(
    "CLOUD_DETECTION_MODEL_PATH",
    os.path.join(_repo_root, "models", "cloud_detection_logistic_regression_v1.0.sav"),
)

# Ensure output directory exists
os.makedirs(output_path, exist_ok=True)
links_must_contain = ["RGBNED"]  # i.e. ["SV", "50cm", "RGBI", "2022"]
account_url = (
    ""  # blob storage account url, only relevant when using postprocessing scripts
)
