from app.video_processor.video_downloader import VercelVideoDownloader
from app.video_processor.videoframe_handler import VideoFrameHandler, NaiveVideoFrameCurator

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
    ## TODO
    pass

def parse_video_info(video_path: str):
    ## TODO
    pass

def check_labeling_status():
    ## TODO
    pass