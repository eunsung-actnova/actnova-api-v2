from abc import ABC, abstractmethod
from dataclasses import dataclass
from glob import glob
import os

import spb_label.sdk
from spb_label.tasks.manager import TaskManager

class LabellingManager(ABC):
    @abstractmethod
    def upload_images(self, image_path: str):
        raise NotImplementedError

    @abstractmethod
    def get_labelling_status(self):
        raise NotImplementedError


@dataclass
class LabellingStatus:
    completed_count: int
    total_count: int
    status: str




class SuperbLabellingManager(LabellingManager):
    def __init__(self, project_name: str, team_name: str, superbai_token: str):
        self.client = spb_label.sdk.Client(
            project_name=project_name, team_name=team_name, access_key=superbai_token
        )
        self.task_manager = TaskManager(
            self.client.credential["team_name"], self.client.credential["access_key"]
        )

    def upload_images(self, image_path: str, task_id: str):
        image_paths = glob(os.path.join(image_path, "*.jpg"))
        for image_path in image_paths:
            self.client.upload_image(image_path, dataset_name=task_id)

    def get_labelling_status(self, task_id: str) -> LabellingStatus:
        task_progress = self.task_manager.get_task_progress_by_id(task_id)

        return LabellingStatus(
            completed_count=task_progress.total_count,
            total_count=task_progress.progress,
            status=task_progress.status,
        )
