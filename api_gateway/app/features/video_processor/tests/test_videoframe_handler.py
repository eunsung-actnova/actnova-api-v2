import os
import sys

import cv2
import numpy as np
import pytest

from api_gateway.app.videoframe_handler import NaiveVideoFrameCurator, VideoFrameHandler


class TestVideoFrameHandler:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before test execution"""
        self.handler = VideoFrameHandler()
        self.test_video_path = "tests/test_data/test_video.mp4"

        # Create test video directory if it doesn't exist
        os.makedirs(os.path.dirname(self.test_video_path), exist_ok=True)

        # Create test videos
        if not os.path.exists(self.test_video_path):
            self._create_test_video()

        # Create short video (for frame count testing)
        self.short_video_path = "tests/test_data/short_video.mp4"
        if not os.path.exists(self.short_video_path):
            self._create_test_video(
                self.short_video_path, duration=0.5
            )  # 0.5 seconds (15 frames)

    def _create_test_video(self, video_path=None, duration=2.0):
        """Create a simple test video file"""
        if video_path is None:
            video_path = self.test_video_path

        # Video settings
        width, height = 320, 240
        fps = 30

        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

        # Create and save frames
        for i in range(int(fps * duration)):
            # Add frame number and timestamp for reference
            frame = np.ones((height, width, 3), dtype=np.uint8) * 255
            frame_text = f"Frame: {i}, Time: {i / fps:.2f}s"
            cv2.putText(
                frame,
                frame_text,
                (10, height // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
            )
            out.write(frame)

        out.release()

    def test_extract_frames(self):
        """Test frame extraction functionality"""
        # 1. Test frame extraction from normal video
        frames = self.handler.extract(self.test_video_path)

        # Verify the number of extracted frames (FPS * video length)
        assert len(frames) == 60  # 30fps * 2s = 60 frames

        # Verify frame format
        assert isinstance(frames[0], np.ndarray)
        assert len(frames[0].shape) == 3  # (height, width, channels)

        # 2. Test frame extraction from short video (when frames are few)
        short_frames = self.handler.extract(self.short_video_path)

        # Verify short video frame count
        assert len(short_frames) == 15  # 30fps * 0.5s = 15 frames

        # Directly verify frame count from the video file
        cap = cv2.VideoCapture(self.short_video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        # Verify VideoFrameHandler.extract extracted all frames
        assert len(short_frames) == frame_count

    def test_naive_curator(self):
        """Test NaiveVideoFrameCurator - evenly spaced frame extraction"""
        frames = self.handler.extract(self.test_video_path)

        # 1. Basic curating test
        num_frames = 10
        naive_curator = NaiveVideoFrameCurator(num_frames=num_frames)
        curated_frames = self.handler.curate(frames, naive_curator)

        # Verify curated frame count
        assert len(curated_frames) == num_frames

        # Verify even spacing
        frame_interval = len(frames) // num_frames

        for i in range(num_frames):
            expected_frame_index = i * frame_interval
            # Verify frame match
            if expected_frame_index < len(frames):
                np.testing.assert_array_equal(
                    curated_frames[i], frames[expected_frame_index]
                )

        # 2. Test when requested frame count is more than original frame count
        short_frames = self.handler.extract(self.short_video_path)
        many_frames = 20  # More than original video frames (15)

        naive_curator = NaiveVideoFrameCurator(num_frames=many_frames)
        curated_frames = self.handler.curate(short_frames, naive_curator)

        # Filtered frames shouldn't exceed original frame count
        assert len(curated_frames) <= len(short_frames)
        # Should get as many frames as possible with even spacing
        assert len(curated_frames) == len(short_frames)
