from app.repositories.fake_repository import FakeRepository
from app.services import video_service

import os

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
    
    
def test_비디오_정보를_수집한다():
    task_id = "test_task_id"
    sample_video = "./tmp/mp4_sample.mp4"
    video_repository = FakeRepository()
    video_info = video_service.parse_video_info(task_id, sample_video, video_repository)
    
    assert hasattr(video_info, "frame_count")
    assert hasattr(video_info, "codec")
    assert hasattr(video_info, "video_type")
    assert hasattr(video_info, "duration_sec")
    assert hasattr(video_info, "camera_angle")
    assert hasattr(video_info, "video_quality")
    
    assert video_repository.get(task_id) == video_info
    

def test_다양한_유형의_비디오를_mp4로_변환한다():
    """
    처리 가능 영상 유형: avi, mov, mkv, wmv, flv, webm, mp4
    TODO: 이미 mp4파일이더라도 mp4로 변환해야하는 경우?
    """
    video_list = [
        "./tmp/avi_sample.avi",
        "./tmp/mov_sample.mov",
        "./tmp/mkv_sample.mkv",
        "./tmp/wmv_sample.wmv",
        "./tmp/flv_sample.flv",
        "./tmp/webm_sample.webm",
        "./tmp/mp4_sample.mp4",
    ]
    convert_file_path = './tmp/converted'
    os.makedirs(convert_file_path, exist_ok=True)
    
    for videofile in video_list:
        video_service.convert_video(videofile, convert_file_path)
