@echo on
<<<<<<< HEAD
pip uninstall -y dist\satellite_images_nso-1.1.14-py3-none-any.whl
del /Q dist\
python setup.py bdist_wheel
pip install dist\satellite_images_nso-1.1.14-py3-none-any.whl
=======
pip uninstall -y dist\satellite_images_nso-1.1.16-py3-none-any.whl
del /Q dist\
python setup.py bdist_wheel
pip install dist\satellite_images_nso-1.1.16-py3-none-any.whl
>>>>>>> github
