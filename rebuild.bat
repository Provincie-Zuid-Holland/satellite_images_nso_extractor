@echo on
pip uninstall -y dist\satellite_images_nso-1.0.0-py3-none-any.whl
del /Q dist\
python setup.py bdist_wheel
pip install dist\satellite_images_nso-1.0.0-py3-none-any.whl