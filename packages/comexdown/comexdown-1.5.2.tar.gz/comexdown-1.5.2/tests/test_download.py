import unittest
from pathlib import Path
from unittest import mock

from comexdown import download


class TestDownloadFile(unittest.TestCase):
    @mock.patch("comexdown.download.sys")
    @mock.patch("comexdown.download.requests")
    @mock.mock_open()
    def test_download_file(self, mock_open, mock_requests, mock_sys):
        # Setup mock response
        mock_response = mock.Mock()
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"data"]
        mock_response.raise_for_status = mock.Mock()
        mock_requests.get.return_value.__enter__.return_value = mock_response

        # Mock HEAD request for update check (returning different time ensuring download happens)
        mock_head = mock.Mock()
        mock_head.headers = {}
        mock_requests.head.return_value = mock_head

        download.download_file("http://www.example.com/file.csv", Path("data/file.csv"))

        mock_requests.get.assert_called()
        mock_open.assert_called_with(Path("data/file.csv"), "wb")
        mock_sys.stdout.write.assert_called()


if __name__ == "__main__":
    unittest.main()
