import os
import ffmpeg

from app.features.video_processor.video_downloader import VercelVideoDownloader
from app.features.video_processor.videoframe_handler import VideoFrameHandler, NaiveVideoFrameCurator
from app.features.video_processor.video_parser import OpenCVVideoParser
from app.entities import Video
from app.repositories.base_repository import BaseRepository


def download_video(url: str, download_path: str):
    downloader = VercelVideoDownloader()
    return downloader.download(url, download_path)


def extract_frames(video_path: str, output_path: str):
    handler = VideoFrameHandler()
    frames = handler.extract(video_path)
    
    curator = NaiveVideoFrameCurator()
    curated_frames = handler.curate(frames, curator)
    
    handler.save(curated_frames, output_path)

    
def convert_video(video_path: str, output_path: str):
    """
    주어진 비디오 파일을 mp4(H.264/AAC)로 변환한다.

    ffmpeg-python 필요: pip install ffmpeg-python
    """
    import sys
    output_file = os.path.join(output_path, os.path.basename(video_path))

    try:
        (
            ffmpeg.input(video_path)
            .output(
                output_file,
                vcodec="libx264",
                acodec="aac",
                preset="fast",
                crf=18,
                movflags="faststart",
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print("ffmpeg error:", file=sys.stderr)
        print(e.stderr.decode('utf8'), file=sys.stderr)
        raise


def parse_video_info(task_id: str, video_path: str, repository: BaseRepository):
    video_parser = OpenCVVideoParser()
    video_info = video_parser.extract_info(video_path)
    # TODO: 카메라 앵글 파악, 비디오 퀄리티 파악

    # 비디오 정보 ORM 객체 생성
    video = Video(
        id=task_id,
        task_id=task_id,
        frame_count=video_info.get("frame_count"),
        video_type=video_info.get("video_type"),
        duration_sec=video_info.get("duration_sec"),
        camera_angle=video_info.get("camera_angle"),
        video_quality=video_info.get("video_quality"),
    )

    # 비디오 정보 DB에 저장
    repository.add(video)

    return video

def check_labeling_status():
    ## TODO
    pass