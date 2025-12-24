import unittest
from unittest.mock import patch, MagicMock, mock_open
import os

from sima_cli.download import (
    download_file_from_url,
    download_folder_from_url,
)

class TestDownloader(unittest.TestCase):

    @patch("sima_cli.download.downloader.requests.get")
    @patch("sima_cli.download.downloader.requests.head")
    def test_download_file_success(self, mock_head, mock_get):
        # Simulate HEAD response
        mock_head_response = MagicMock()
        mock_head_response.headers = {'content-length': '9'}
        mock_head_response.raise_for_status = lambda: None
        mock_head.return_value = mock_head_response

        # Simulate GET response
        mock_get_response = MagicMock()
        mock_get_response.iter_content = lambda chunk_size: [b"test data"]
        mock_get_response.headers = {'content-length': '9'}
        mock_get_response.raise_for_status = lambda: None
        mock_get_response.__enter__.return_value = mock_get_response
        mock_get.return_value = mock_get_response

        dest_folder = "test_output"
        url = "https://127.0.0.1/sima/file.tar"
        downloaded_path = download_file_from_url(url, dest_folder)

        self.assertTrue(os.path.exists(downloaded_path))
        with open(downloaded_path, "rb") as f:
            self.assertEqual(f.read(), b"test data")

        os.remove(downloaded_path)
        os.rmdir(dest_folder)

    @patch("sima_cli.download.downloader.requests.head")
    def test_invalid_url_raises(self, mock_head):
        # HEAD response without a file name
        mock_head.return_value = MagicMock(headers={'content-length': '10'}, raise_for_status=lambda: None)
        with self.assertRaises(ValueError):
            download_file_from_url("https://example.com/", "somewhere")

    @patch("sima_cli.download.downloader.requests.get")
    @patch("sima_cli.download.downloader.requests.head")
    def test_skip_already_downloaded_file(self, mock_head, mock_get):
        dest_folder = "test_output"
        os.makedirs(dest_folder, exist_ok=True)
        test_file_path = os.path.join(dest_folder, "file.txt")

        # Create a complete file manually
        with open(test_file_path, "wb") as f:
            f.write(b"123456789")

        mock_head_response = MagicMock()
        mock_head_response.headers = {'content-length': '9'}
        mock_head_response.raise_for_status = lambda: None
        mock_head.return_value = mock_head_response

        url = "https://127.0.0.1/sima/file.txt"
        returned_path = download_file_from_url(url, dest_folder)

        self.assertEqual(returned_path, test_file_path)
        mock_get.assert_not_called()

        os.remove(test_file_path)
        os.rmdir(dest_folder)

    @patch("sima_cli.download.downloader.requests.get")
    def test_list_directory_files_parses_links(self, mock_get):
        from sima_cli.download.downloader import _list_directory_files

        # Simulated directory listing HTML
        mock_html = '''
            <a href="../">Parent</a>
            <a href="model1.onnx">model1.onnx</a>
            <a href="readme.txt">readme.txt</a>
            <a href="subfolder/">subfolder/</a>
        '''
        mock_get_response = MagicMock()
        mock_get_response.text = mock_html
        mock_get_response.headers = {"Content-Type": "text/html"}
        mock_get_response.raise_for_status = lambda: None
        mock_get_response.__enter__.return_value = mock_get_response
        mock_get.return_value = mock_get_response

        result = _list_directory_files("http://host/folder/")
        self.assertEqual(result, [
            "http://host/folder/model1.onnx",
            "http://host/folder/readme.txt"
        ])

    @patch("sima_cli.download.downloader.download_file_from_url")
    @patch("sima_cli.download.downloader._list_directory_files")
    def test_download_folder_from_url(self, mock_list_files, mock_download_file):
        mock_list_files.return_value = [
            "http://server/file1.txt",
            "http://server/file2.txt"
        ]
        mock_download_file.side_effect = lambda url, dest: os.path.join(dest, os.path.basename(url))

        dest = "test_output"
        os.makedirs(dest, exist_ok=True)
        downloaded = download_folder_from_url("http://server/", dest)

        self.assertEqual(len(downloaded), 2)
        self.assertIn(os.path.join(dest, "file1.txt"), downloaded)

        os.rmdir(dest)

if __name__ == "__main__":
    unittest.main()
