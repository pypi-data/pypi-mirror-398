"""Module containing tests for yr_meteogram_downloader"""

import glob
import os
import unittest
import asyncio

from yr_meteogram_util import fetch, extract_info

LOCATION_ID = '2-5847504'
TESTFILEPATH = 'testfiles'

def save_to_file(filename, contents):
    """Save the contents to a file with filename."""
    with open(TESTFILEPATH + '/' + filename, mode='w', encoding='utf-8') as file:
        file.write(contents)

class DownloadTestCase(unittest.TestCase):
    """Class for performing the tests."""
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TESTFILEPATH):
            os.makedirs(TESTFILEPATH)
        else:
            svg_files = glob.glob(TESTFILEPATH + '/*.svg')
            for file in svg_files:
                try:
                    os.remove(file)
                except OSError:
                    print('Error while deleting file ' + file)

    def test_standard(self):
        """The most simple test. Just download the standard meteogram and save it to a file."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID))
        save_to_file('standard.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertIn('style="background-color:#ffffff"', meteogram)

    def test_crop(self):
        """Download the standard meteogram, crop it and save it to a file."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID, crop = True))
        save_to_file('cropped.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertIn('style="background-color:#ffffff"', meteogram)
        self.assertIn(' viewBox="0 85 782 300"', meteogram)

    def test_transparent(self):
        """Download the standard meteogram, make it transparent and save it to a file."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID, make_transparent = True))
        save_to_file('transparent.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertNotIn('style="background-color:#ffffff"', meteogram)

    def test_cropped_transparent(self):
        """Download the standard meteogram, make it transparent and save it to a file."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID, crop = True, make_transparent = True))
        save_to_file('cropped_transparent.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertNotIn('style="background-color:#ffffff"', meteogram)
        self.assertIn(' viewBox="0 85 782 300"', meteogram)

    def test_dark(self):
        """The second most simple test. Just download the dark meteogram and save it to a file."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID, dark = True))
        save_to_file('dark.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertIn('style="background-color:#020a14"', meteogram)

    def test_dark_cropped(self):
        """Download the dark meteogram, crop it and save it to a file."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID, dark = True, crop = True))
        save_to_file('dark_cropped.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertIn('style="background-color:#020a14"', meteogram)
        self.assertIn(' viewBox="0 85 782 300"', meteogram)

    def test_dark_unhide(self):
        """Download the dark meteogram, fix colors and save it to a file."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID, dark = True, unhide_dark_objects = True))
        save_to_file('dark_unhide.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertIn('style="background-color:#020a14"', meteogram)

    def test_dark_transparent(self):
        """This tests downloading the dark version and makes it transparent."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID, dark = True, make_transparent = True))
        save_to_file('dark_transparent.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertNotIn('style="background-color:"', meteogram)
        self.assertNotIn('<rect x="0" y="0" width="782" height="391"', meteogram)

    def test_dark_cropped_transparent(self):
        """Download the dark version, make it transparent, crop it and save to file."""
        meteogram = asyncio.run(
            fetch.fetch_svg_async(LOCATION_ID, dark = True, crop = True, make_transparent = True))
        save_to_file('dark_cropped_transparent.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertNotIn('style="background-color:"', meteogram)
        self.assertNotIn('<rect x="0" y="0" width="782" height="391"', meteogram)
        self.assertIn(' viewBox="0 85 782 300"', meteogram)

    def test_dark_cropped_transparent_unhide(self):
        """Download the dark version, make it transparent, crop it and save to file."""
        meteogram = asyncio.run(
            fetch.fetch_svg_async(LOCATION_ID, dark = True, crop = True,
                            make_transparent = True, unhide_dark_objects = True))
        save_to_file('dark_cropped_transparent_unhide.svg', meteogram)
        self.assertIn('<svg', meteogram)
        self.assertNotIn('style="background-color:"', meteogram)
        self.assertNotIn('<rect x="0" y="0" width="782" height="391"', meteogram)
        self.assertIn(' viewBox="0 85 782 300"', meteogram)

    def test_extract_location_name(self):
        """Download the standard meteogram and extract it's location name."""
        meteogram = asyncio.run(fetch.fetch_svg_async(LOCATION_ID))
        location_name = extract_info.get_location_name(meteogram)
        self.assertEqual('Kailua-Kona', location_name)
