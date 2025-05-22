from abc import ABC, abstractmethod
from glob import glob
import random
import os
import shutil 
from pathlib import Path
import yaml


class DataHandler(ABC):
    @abstractmethod
    def split_data(self, train_valid_ratio: float):
        pass



class YamlDataHandler(DataHandler):
    def split_data(self, data_path: str, task_id: str, train_valid_ratio: float):
        # label_path 기준 images, labels 폴더 파악
        image_path = f'{data_path}/frames/{task_id}'
        label_path = f'{data_path}/labels/{task_id}'

        # 전체 데이터 갯수 파악
        image_list = glob(f'{image_path}/*.jpg')
        label_list = glob(f'{label_path}/*.txt')

        # shuffle
        random.shuffle(image_list)
        random.shuffle(label_list)

        # TODO: 예외 처리
        if len(image_list) != len(label_list):
            raise ValueError("image와 label의 갯수가 다릅니다.")
        
        # 숫자가 적을 경우 예외 처리
        if len(image_list) < 2:
            raise ValueError("데이터가 너무 적습니다.")
        
        return image_list, label_list

    def save_data(self, data_path: str,  image_list: list, label_list: list, train_valid_ratio: float):
        # train_valid_ratio 비율에 맞게 데이터 분리
        train_image_list = image_list[:int(len(image_list) * train_valid_ratio)]
        valid_image_list = image_list[int(len(image_list) * train_valid_ratio):]
        train_label_list = label_list[:int(len(label_list) * train_valid_ratio)]
        valid_label_list = label_list[int(len(label_list) * train_valid_ratio):]
        # 분리된 데이터 저장
        train_image_path = f'{data_path}/images/train'
        valid_image_path = f'{data_path}/images/valid'
        train_label_path = f'{data_path}/labels/train'
        valid_label_path = f'{data_path}/labels/valid'

        os.makedirs(train_image_path, exist_ok=True)
        os.makedirs(valid_image_path, exist_ok=True)
        os.makedirs(train_label_path, exist_ok=True)
        os.makedirs(valid_label_path, exist_ok=True)

        for image, label in zip(train_image_list, train_label_list):
            shutil.copy(image, train_image_path)
            shutil.copy(label, train_label_path)

        for image, label in zip(valid_image_list, valid_label_list):
            shutil.copy(image, valid_image_path)
            shutil.copy(label, valid_label_path)

    def create_yaml(self, data_path: str):
        # TODO: yaml에 필요없는 부분 제거
        flip_idx = [0, 2, 1, 4, 3, 6, 5, 7, 8, 9, 10]

        data_yaml = {
            "path": data_path,
            "train": "data/images/train/",
            "val": "data/images/valid/",
            "kpt_shape": [len(flip_idx), 3],
            "flip_idx": flip_idx,
            "names": {0: "mouse"},
        }
        yaml_path = f'{data_path}/data.yaml'
        with open(yaml_path, "w") as yaml_file:
            yaml.dump(data_yaml, yaml_file, default_flow_style=False)
        return yaml_path


