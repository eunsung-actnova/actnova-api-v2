import os

from app.features.video_processor import VercelVideoDownloader


def test_비디오를_다운로드한다():
    sample_video = "https://ueqgyaa7lbfff1ok.public.blob.vercel-storage.com/cmam9n7gu0000lb04muxloagt/videos/Trial____17-Actverse-3DCOYW73YpN8wrOw0HwAKhmPlVTOqH.mp4"
    video_downloader = VercelVideoDownloader()
    video_downloader.download(sample_video, "/tmp")
    
    assert os.path.exists(f"/tmp/{sample_video.split('/')[-1]}")
    
    