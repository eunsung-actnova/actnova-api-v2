import subprocess
from pathlib import Path
from shutil import copyfile

import actnova
from ultralytics import YOLO


def export_on_trt(
    triton_root_path,
    triton_repo_path,
    triton_model_name,
    exported_trt_model_name,
    download_path,
    onnx_model_path,
    f16=False,
):
    # triton 레포 디렉토리 생성
    triton_model_path = triton_repo_path / triton_model_name
    (triton_model_path / "1").mkdir(parents=True, exist_ok=True)

    # 모델 다운로드
    model_path = actnova.downloader.ModelDownloader.download(
        "yolo12l", download_path=download_path, output="yolo12l.pt"
    )

    # 모델 export to onnx
    model = YOLO(model_path, task="pose")
    metadata = []

    def export_cb(exporter):
        metadata.append(exporter.metadata)

    model.add_callback("on_export_end", export_cb)
    onnx_file = model.export(format="onnx", dynamic=True, batch=16)
    Path(onnx_file).rename(onnx_model_path)

    # Docker 컨테이너 내에서는 별도 Docker 실행이 불필요
    # TensorRT 변환을 로컬에서 직접 수행
    import os

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    commands = [
        "trtexec",
        f"--onnx={onnx_model_path}",
        f"--saveEngine={exported_trt_model_name}",
        "--minShapes=images:1x3x80x80",
        "--maxShapes=images:16x3x640x640",
    ]
    if f16:
        commands.append("--fp16")
    subprocess.run(commands)

    # 모델 파일과 설정 복사
    copyfile(exported_trt_model_name, triton_model_path / "1" / "model.plan")
    (triton_model_path / "config.pbtxt").touch()

    data = (
        """
optimization {
  execution_accelerators {
    gpu_execution_accelerator {
      name: "tensorrt"
      parameters {
        key: "precision_mode"
        value: "FP16"
      }
      parameters {
        key: "max_workspace_size_bytes"
        value: "3221225472"
      }
      parameters {
        key: "trt_engine_cache_enable"
        value: "1"
      }
      parameters {
        key: "trt_engine_cache_path"
        value: "/models/yolo/1"
      }
    }
  }
}
parameters {
  key: "metadata"
  value: {
    string_value: "%s"
  }
}
"""
        % metadata[0]
    )

    with open(triton_model_path / "config.pbtxt", "w") as f:
        f.write(data)

    print("Triton 모델 초기화가 완료되었습니다.")


if __name__ == "__main__":
    # Docker 환경에 맞게 경로 수정
    root_path = Path("/workspace")
    triton_repo_path = Path("/workspace/triton_repository")
    triton_repo_path.mkdir(parents=True, exist_ok=True)

    triton_model_name = "yolo12l"
    download_path = root_path / "models"
    download_path.mkdir(parents=True, exist_ok=True)

    onnx_path = download_path / "yolo12l"
    onnx_path.mkdir(parents=True, exist_ok=True)

    exported_trt_model_name = onnx_path / "yolo12l.plan"
    onnx_model_path = onnx_path / "yolo12l.onnx"

    export_on_trt(
        root_path,
        triton_repo_path,
        triton_model_name,
        exported_trt_model_name,
        download_path,
        onnx_model_path,
        f16=True,  # FP16 사용
    )
