import os
import sys
import json
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.uploader import LocalUploader

def test_local_uploader_video(tmp_path):
    src = tmp_path / "sample.mp4"
    src.write_text("video")
    dest = tmp_path / "out"
    uploader = LocalUploader()
    uploaded = uploader.upload_video(str(src), str(dest))
    assert os.path.exists(uploaded)


def test_local_uploader_frames(tmp_path):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    for i in range(3):
        (frames_dir / f"f{i}.jpg").write_text("img")
    dest = tmp_path / "dest"
    uploader = LocalUploader()
    uploader.upload_frames(str(frames_dir), str(dest))
    for i in range(3):
        assert (dest / f"f{i}.jpg").exists()


def test_local_uploader_csv_json(tmp_path):
    csv_path = tmp_path / "data.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["a", "b"])

    json_path = tmp_path / "data.json"
    with open(json_path, "w") as f:
        json.dump({"a": 1}, f)

    dest = tmp_path / "upload"
    uploader = LocalUploader()
    csv_uploaded = uploader.upload_csv(str(csv_path), str(dest))
    json_uploaded = uploader.upload_json(str(json_path), str(dest))

    assert os.path.exists(csv_uploaded)
    assert os.path.exists(json_uploaded)
