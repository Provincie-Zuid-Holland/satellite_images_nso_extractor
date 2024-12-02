# give path to geojson en output,!!!!! rewrite these directories to your file system!!!!
# path_geojson = "C:/Users/pzhadmin/Documents/natura2000_coepelduynen.geojson"
path_test_input_data = "C:/repos/satellite-images-nso/tests/test_data/"
path_geojson = path_test_input_data + "Test_region.geojson"
height_band_filepath = ""
output_path = "E:/data/test"
cloud_detection_model_path = (
    "C:/repos/satellite-images-nso/models/cloud_detection_logistic_regression_v1.0.sav"
)
links_must_contain = ["RGBNED"]  # i.e. ["SV", "50cm", "RGBI", "2022"]
account_url = (
    ""  # blob storage account url, only relevant when using postprocessing scripts
)
