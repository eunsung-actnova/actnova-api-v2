import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import types
sys.modules['common'] = types.ModuleType('common')
sys.modules['common.actverse_common'] = types.ModuleType('actverse_common')
utils_mod = types.ModuleType('utils')
utils_mod.sanitize_filename = lambda x: x
sys.modules['common.actverse_common.utils'] = utils_mod

from app.video_downloader import VercelVideoDownloader
import requests


class FakeResponse:
    def __init__(self, content: bytes):
        self._content = content
        self.headers = {"content-length": str(len(content)),
                        "Content-Disposition": 'attachment; filename="video.mp4"'}

    def iter_content(self, chunk_size=1024):
        yield self._content


def fake_get(url, stream=True):
    return FakeResponse(b"video")

def test_vercel에서_비디오_다운로드(monkeypatch, tmp_path):
    monkeypatch.setattr(requests, "get", fake_get)
    vercel_downloader = VercelVideoDownloader()

    url = "https://example.com/video.mp4"
    download_path = tmp_path

    downloaded_file_name = vercel_downloader.download(url, str(download_path))

    assert os.path.exists(downloaded_file_name)

