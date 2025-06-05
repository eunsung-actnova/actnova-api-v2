import os
import shutil
from glob import glob

class LocalUploader:
    """Simple uploader that copies files or directories to a destination."""

    def _ensure_dir(self, dest: str):
        os.makedirs(dest, exist_ok=True)

    def upload_video(self, file_path: str, dest_dir: str) -> str:
        self._ensure_dir(dest_dir)
        return shutil.copy(file_path, dest_dir)

    def upload_frames(self, frames_dir: str, dest_dir: str) -> str:
        self._ensure_dir(dest_dir)
        for frame in glob(os.path.join(frames_dir, '*')):
            shutil.copy(frame, dest_dir)
        return dest_dir

    def upload_csv(self, file_path: str, dest_dir: str) -> str:
        return self.upload_video(file_path, dest_dir)

    def upload_json(self, file_path: str, dest_dir: str) -> str:
        return self.upload_video(file_path, dest_dir)
