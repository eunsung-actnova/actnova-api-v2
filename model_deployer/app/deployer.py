from abc import ABC, abstractmethod
from typing import Union
import os, shutil
import requests

class ModelDeployer(ABC):
    @abstractmethod
    def request_model_update(self, task_id: str):
        raise NotImplementedError
    
class TritonModelDeployer(ModelDeployer):
    def request_model_update(self, triton_url: str, task_id: str, action: str): # TODO: action 명시하기 load, unload

        # 모델 경로에 모델이 있는지 확인
        triton_model_path = f'/app/data_storage/models/{task_id}/1/model.plan'
        if not os.path.exists(triton_model_path):
            raise FileNotFoundError(f"Model not found at {triton_model_path}")
        

        if action == "load":
            # 모델 교체 요청
            url = f"{triton_url}/v2/repository/models/{task_id}/{action}"
            response = requests.post(url)

        elif action == "unload":
            shutil.rmtree(triton_model_path, ignore_errors=True)

        return response
    
    
