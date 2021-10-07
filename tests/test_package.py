# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package

import unittest

import satellite_images_nso.api.nso_georegion as nso


class TestSimple(unittest.TestCase):

    def test_importpackage(self):
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()