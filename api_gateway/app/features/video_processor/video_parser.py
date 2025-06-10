from abc import ABC, abstractmethod

import cv2
import os


class VideoParser(ABC):
    @abstractmethod
    def extract_info(self, video_path: str) -> dict:
        """
        비디오 파일을 분석해 주요 정보를 반환합니다.
        반환 예시:
        {
            "frame_count": int,
            "video_type": str,
            "duration_sec": float,
            "camera_angle": Optional[str],
            "video_quality": Optional[str],
        }
        """
        pass




class OpenCVVideoParser(VideoParser):
    def extract_info(self, video_path: str) -> dict:
        _, ext = os.path.splitext(video_path)
        ext = ext.lower().replace('.', '')

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration_sec = frame_count / fps if fps else None
        
        # FOURCC 코드 추출 및 문자열 변환
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
        fourcc = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
        codec = fourcc.strip()

        cap.release()

        # TODO: 카메라 앵글, 퀄리티는 추후 구현
        return {
            "frame_count": frame_count,
            "codec": codec,
            "video_type": ext,
            "duration_sec": duration_sec,
            "camera_angle": None,
            "video_quality": None,
        }