import os
import pytest

from app.video_downloader import VercelVideoDownloader

def test_vercel에서_비디오_다운로드():
    vercel_downloader = VercelVideoDownloader()
    url = "https://ueqgyaa7lbfff1ok.public.blob.vercel-storage.com/cm9ifxjsc0000pkgqpr4j1ucs/videos/one-mouse-5sec-YfKPsl7vbZhQXtwau9q2FZXbTK2RLg.mp4"
    download_path = "tests/test_data/"

    downloaded_file_name = vercel_downloader.download(url, download_path)

    assert os.path.exists(download_path)

    os.remove(downloaded_file_name)
