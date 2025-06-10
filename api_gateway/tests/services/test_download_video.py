import os

from app.services import video_service

def test_비디오를_다운로드한다():
    sample_video = "https://ueqgyaa7lbfff1ok.public.blob.vercel-storage.com/cmam9n7gu0000lb04muxloagt/videos/Trial____17-Actverse-3DCOYW73YpN8wrOw0HwAKhmPlVTOqH.mp4"
    
    video_service.download_video(sample_video, './tmp')
    
    # 다운로드 파일이름 뒤에 해시값이 떨어져서 다운로드된다. 
    # e.g) sample-{hash값}.mp4 -> sample.mp4 [실제 다운로드 파일명] 
    
    download_filename = sample_video.split('/')[-1]
    fname, ext = os.path.splitext(download_filename)
    fname_without_hash, hash = fname.rsplit('-', 1)
    fname_without_hash += ext
    assert os.path.exists(os.path.join('./tmp', fname_without_hash))