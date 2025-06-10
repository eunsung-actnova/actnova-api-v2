import abc
from typing import List
from pathlib import Path

# import cv2
import numpy as np


class VideoFrameCurator(abc.ABC):
    @abc.abstractmethod
    def curate(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        pass


class CompositeCurator(VideoFrameCurator):
    """여러 필터를 하나의 필터로 결합하는 컴포지트 필터 클래스입니다."""

    def __init__(self, filters: List[VideoFrameCurator] = None):
        self.filters = filters or []

    def add_curation(self, video_filter: VideoFrameCurator) -> "CompositeCurator":
        """필터를 추가하고 자신을 반환하여 메서드 체이닝을 지원합니다."""
        self.filters.append(video_filter)
        return self

    def curate(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """모든 필터를 순차적으로 적용합니다."""
        result = frames
        for video_filter in self.filters:
            result = video_filter.curate(result)
        return result


class NaiveVideoFrameCurator(VideoFrameCurator):
    """
    num_frames만큼 frame을 균등하게 추출
    """

    def __init__(self, num_frames: int):
        self.num_frames = num_frames

    def curate(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        filtered_frames = []

        # 요청된 프레임 수가 원본 프레임 수보다 많으면 원본 프레임 수로 제한
        actual_num_frames = min(self.num_frames, len(frames))

        # 프레임이 없거나 요청 프레임 수가 0이면 빈 리스트 반환
        if not frames or actual_num_frames <= 0:
            return []

        # 균등한 간격 계산
        interval = max(1, len(frames) // actual_num_frames)
        frame_index = 0

        while frame_index < len(frames) and len(filtered_frames) < actual_num_frames:
            filtered_frames.append(frames[frame_index])
            frame_index += interval

        return filtered_frames


class VideoFrameHandler:
    def extract(self, video_path: str) -> List[np.ndarray]:
        cap = cv2.VideoCapture(video_path)

        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = []

        for _ in range(num_frames):
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)

        cap.release()

        return frames

    def curate(
        self, frames: List[np.ndarray], frame_curator: VideoFrameCurator, prediction=None
    ) -> List[np.ndarray]:
        return frame_curator.curate(frames)

    def save(self, frames: List[np.ndarray], output_path: str):
        """저장된 프레임들을 개별 이미지 파일로 저장합니다.

        Args:
            frames: 저장할 프레임 리스트
            output_path: 저장할 디렉토리 경로
        """
        if not frames:
            raise ValueError("No frames to save")

        # 출력 디렉토리 생성
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 각 프레임을 개별 이미지로 저장
        for i, frame in enumerate(frames):
            # 프레임이 흑백인 경우 컬러로 변환
            if len(frame.shape) == 2 or frame.shape[2] == 1:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            # 프레임 번호를 포함한 파일명 생성
            frame_filename = f"frame_{i:04d}.jpg"
            frame_path = output_dir / frame_filename

            # 이미지 저장
            cv2.imwrite(str(frame_path), frame)

        return str(output_dir)

    def overlay_keypoints(self, frames, keypoints):
        pass
