import unittest
from pathlib import Path
from unittest import mock

import comexdown


@mock.patch("comexdown.download.download_file")
class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.path = Path("tmp")

    def test_get_year(self, mock_download_file):
        comexdown.get_year(self.path, year=2000, exp=True, imp=True)
        # Should be called twice (exp and imp)
        self.assertEqual(mock_download_file.call_count, 2)

        comexdown.get_year(self.path, year=2000, exp=True, imp=True, mun=True)
        # Should be called 2 more times (exp_mun and imp_mun)
        self.assertEqual(mock_download_file.call_count, 4)

    def test_get_year_nbm(self, mock_download_file):
        comexdown.get_year_nbm(self.path, 2000, exp=True, imp=True)
        self.assertEqual(mock_download_file.call_count, 2)

    def test_get_complete(self, mock_download_file):
        comexdown.get_complete(self.path, exp=True, imp=True)
        self.assertEqual(mock_download_file.call_count, 2)

        comexdown.get_complete(self.path, exp=True, imp=True, mun=True)
        self.assertEqual(mock_download_file.call_count, 4)

    def test_get_table(self, mock_download_file):
        comexdown.get_table(self.path, "ncm")
        mock_download_file.assert_called_once()


if __name__ == "__main__":
    unittest.main()
