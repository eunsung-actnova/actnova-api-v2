from actnova.model import Yolov8KeypointEstimator
from actnova.model.utils import select_device

device = select_device(min_memory=2000)

config = {
            'model': 'yolo12l',
            'device': device,
        }


model = Yolov8KeypointEstimator(**config)   

