import os
from pathlib import Path
from unittest import mock

import requests

from app.features.video_processor import VercelVideoDownloader


def test_downloads_video(tmp_path):
    url = "https://example.com/sample.mp4"
    dest = tmp_path

    # Fake requests.get to avoid external network call
    fake_content = b"data"

    class FakeResponse:
        headers = {"content-length": str(len(fake_content))}

        def iter_content(self, chunk_size=1024):
            yield fake_content

    with mock.patch.object(requests, "get", return_value=FakeResponse()):
        downloader = VercelVideoDownloader()
        downloaded = downloader.download(url, str(dest))

    assert Path(downloaded).exists()
