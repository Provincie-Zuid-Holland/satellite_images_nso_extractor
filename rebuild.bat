@echo on
pip uninstall -y dist\satellite_images_nso-2.0.0-py3-none-any.whl
del /Q dist\
python -m build
pip install dist\satellite_images_nso-2.0.0-py3-none-any.whl
