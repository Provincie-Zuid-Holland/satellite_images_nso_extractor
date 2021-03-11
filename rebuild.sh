pip uninstall -y dist/satellite_images_nso-1.1.10-py3-none-any.whl
rm -rf dist/
python setup.py bdist_wheel
pip install dist/satellite_images_nso-1.1.10-py3-none-any.whl