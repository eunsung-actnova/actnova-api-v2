from abc import ABC, abstractmethod
import os
from actnova.model import Yolov8KeypointEstimator
from actnova.model.utils import select_device

import logging
logger = logging.getLogger(__name__)

import traceback

MIN_MEMORY_MB = 2_000  # test


class Trainer(ABC):
    @abstractmethod
    def train(self, 
              train_data_path: str, 
              valid_data_path: str, 
              epochs: int, 
              batch_size: int, 
              lr: float, 
              model_save_dir: str):
        raise NotImplementedError



def on_train_epoch_end(trainer):
    """학습 에포크가 끝날 때마다 호출되는 콜백 함수"""
    metrics = trainer.metrics
    logger.info(f"Epoch {trainer.epoch}: {metrics}")


def on_train_end(trainer):
    """학습이 완료될 때 호출되는 콜백 함수"""
    metrics = trainer.metrics
    logger.info(f"Training completed. Final metrics: {metrics}")


class YoloTrainer(Trainer):
    def train(self, 
              yaml_path: str,
              epochs: int, 
              batch_size: int, 
              lr: float, 
              model_save_path: str):
        
        try:
            device = select_device(min_memory=MIN_MEMORY_MB)
        except Exception as e:
            logger.error(f"Failed to select device: {e}")
            raise e

        config = {
            'model': 'yolo12l',
            'device': device,
        }

        train_params = {
            "batch": batch_size,
            "epochs": epochs,
        }  # 약 9GB 정도의 메모리 사용
        logger.info(f"train_params: {train_params}")


        try:
            model = Yolov8KeypointEstimator(**config)   
        except Exception as e:
            logger.error(f"Failed to create model: {e}\n{traceback.format_exc()}")
            raise e

        logger.info(f"model: {model}")

        # 콜백 함수 등록
        model.model.add_callback("on_train_epoch_end", on_train_epoch_end)
        model.model.add_callback("on_train_end", on_train_end)

        model.train(yaml_path, **train_params)
        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)

        model.model.save(os.path.join(model_save_path, "model.pt"))
        logger.info(f"Saved model to {model_save_path}")



