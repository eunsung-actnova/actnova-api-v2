from abc import ABC, abstractmethod
import torch
from ultralytics import YOLO

import subprocess
import os
from shutil import copyfile
from pathlib import Path

from actverse_common.logging import setup_logger

import tensorrt as trt

logger = setup_logger(service_name="model_packaging")
MIN_MEMORY_MB = 2000


class ModelPackaging(ABC):
    @abstractmethod
    def __call__(self, task_id: str):
        raise NotImplementedError
    

class ONNXModelPackaging(ModelPackaging):
    def __call__(self, task_id: str):
        metadata: list = []
        def export_cb(exporter):
            metadata.append(exporter.metadata)

        pt_model = Path(f'/app/data_storage/train_log/{task_id}/model.pt')
        triton_model_path = Path(f'/app/data_storage/models/{task_id}')
        if not pt_model.exists():
            logger.error(f"{pt_model} does not exist")
            raise FileNotFoundError(f"{pt_model} does not exist")

        onnx_model_path = pt_model.with_suffix(".onnx")
        trt_model_path = pt_model.with_suffix(".plan")

        model = YOLO(str(pt_model), task="pose")
        model.add_callback("on_export_end", export_cb)
        onnx_file = model.export(format="onnx", dynamic=True, batch=16)
        Path(onnx_file).rename(onnx_model_path)

        # TensorRT Python API로 ONNX → TensorRT 엔진 변환
        TRT_LOGGER = trt.Logger(trt.Logger.INFO)
        with trt.Builder(TRT_LOGGER) as builder, \
             builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)) as network, \
             trt.OnnxParser(network, TRT_LOGGER) as parser:

            builder.max_workspace_size = 1 << 30  # 1GB
            builder.fp16_mode = True  # FP16 최적화

            with open(onnx_model_path, 'rb') as model_file:
                if not parser.parse(model_file.read()):
                    logger.error('Failed to parse the ONNX file.')
                    for error in range(parser.num_errors):
                        logger.error(parser.get_error(error))
                    raise RuntimeError('ONNX parsing failed')

            engine = builder.build_cuda_engine(network)
            if engine is None:
                logger.error("Failed to build the TensorRT engine!")
                raise RuntimeError("TensorRT engine build failed")

            with open(trt_model_path, "wb") as f:
                f.write(engine.serialize())
            logger.info(f"TensorRT engine saved to {trt_model_path}")

        # 모델 디렉토리 생성 및 파일 복사
        (triton_model_path / "1").mkdir(parents=True, exist_ok=True)
        copyfile(trt_model_path, triton_model_path / "1" / "model.plan")
        (triton_model_path / "config.pbtxt").touch()
        data = (
            """
        optimization {
        execution_accelerators {
            gpu_execution_accelerator {
                name: \"tensorrt\"
                parameters {
                    key: \"precision_mode\"
                    value: \"FP16\"
                }
                parameters {
                    key: \"max_workspace_size_bytes\"
                    value: \"3221225472\"
                }
                parameters {
                    key: \"trt_engine_cache_enable\"
                    value: \"1\"
                }
                parameters {
                    key: \"trt_engine_cache_path\"
                    value: \"/models/yolo/1\"
                }
            }
        }
        }
        parameters {
        key: \"metadata\"
        value: {
            string_value: \"%s\"
        }
        }
        """
            % metadata[0]
        )

        with open(triton_model_path / "config.pbtxt", "w") as f:
            f.write(data)
        logger.info(f"Exported model to {triton_model_path}")
