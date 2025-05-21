from abc import ABC, abstractmethod
from dataclasses import dataclass
from glob import glob
import os
import json
import cv2


import spb_label.sdk
from spb_label.utils.search_filter import SearchFilter, Status, ReviewStatus
from spb_label.tasks.manager import TaskManager

from app.repository import LabellingStatus
from actverse_common.logging import setup_logger

logger = setup_logger(service_name="labeling_manager")

class LabellingManager(ABC):
    @abstractmethod
    def upload_images(self, image_path: str):
        raise NotImplementedError

    @abstractmethod
    def get_labelling_status(self):
        raise NotImplementedError


@dataclass
class LabellingInfo:
    completed_count: int
    total_count: int
    status: LabellingStatus


def parse_box(single_label):
    height = single_label["annotation"]["coord"]["height"]
    width = single_label["annotation"]["coord"]["width"]
    x = single_label["annotation"]["coord"]["x"]
    y = single_label["annotation"]["coord"]["y"]
    return x, y, width, height


def parse_pose(single_label):
    pose = []
    for point in single_label["annotation"]["coord"]["points"]:
        x = point["x"]
        y = point["y"]
        visible = point["state"]["visible"]
        valid = point["state"]["valid"]
        if visible and valid:  # visible
            visibility = 2
        elif not visible and valid:  # not visible but labeled
            visibility = 1
        elif not visible and not valid:  # not labeled
            visibility = 0
        else:
            raise ValueError("Invalid state")

        pose.extend([x, y, visibility])
    return pose




def match_boxes_and_poses(boxes: list, poses: list, n_keypoints: int):
    copied_boxes = [box.copy() for box in boxes]
    # 각 포즈에 가장 적합한 box를 찾아야함
    matched_boxes = []
    for pose in poses:
        hit_counts = []
        for box in copied_boxes:
            hit_count = 0
            for i in range(0, len(pose), 3):
                px, py = pose[i], pose[i + 1]
                if box[0] < px < box[0] + box[2] and box[1] < py < box[1] + box[3]:
                    hit_count += 1
            hit_counts.append(hit_count)
        matched_index = hit_counts.index(max(hit_counts))
        # boxes에서 matched_index에 해당하는 box를 제거하고 matched_boxes에 추가
        matched_box = copied_boxes.pop(matched_index)
        matched_boxes.append(matched_box)

    # pose보다 많은 box가 있을 경우 나머지 box들은 pose가 없는 것으로 간주
    for box in copied_boxes:
        matched_boxes.append(box)
        poses.append([0] * (n_keypoints * 3))
    return matched_boxes, poses

def box_x0y0wh_to_xcycwhn(box_x0y0wh, image_width, image_height):
    x0, y0, w, h = box_x0y0wh
    xc = (x0 + w / 2) / image_width
    yc = (y0 + h / 2) / image_height
    wn = w / image_width
    hn = h / image_height
    return [xc, yc, wn, hn]

def pose_xyv_to_xyvn(pose, image_width, image_height, min_visibility=None):
    """COCO 형식 keypoint [x, y, v] 배열을 YOLOv8-pose 형식 [x, y, v]로 변환

    min_visibility가 None이면 원래 가시성 값을 유지합니다.
    min_visibility가 정수(0~2)이면, 해당 값 이상이면 2, 미만이면 0으로 설정합니다.
    """
    normalized_pose = []
    for i in range(0, len(pose), 3):
        x, y, v = pose[ i:i+3 ]
        nx = x / image_width
        ny = y / image_height
        if min_visibility is None:
            nv = v
        else:
            nv = 2 if v >= min_visibility else 0
        normalized_pose.extend([nx, ny, nv])
    return normalized_pose



class SuperbLabellingManager(LabellingManager):
    def __init__(self, project_name: str, team_name: str, superbai_token: str):
        self.project_name = project_name
        self.team_name = team_name
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

    def get_labelling_status(self, task_id: str) -> LabellingInfo:
        task_filter = SearchFilter()
        task_filter.dataset_is_any_one_of = [task_id]
        num_total = self.client.get_num_labels(filter=task_filter)
        
        in_progress_filter = SearchFilter()
        in_progress_filter.status_is_any_one_of = [Status.WORKING.value]
        in_progress_filter.dataset_is_any_one_of = [task_id]


        # 완료된 라벨만 필터링
        completed_filter = SearchFilter()
        completed_filter.status_is_any_one_of = [Status.SUBMITTED.value]  # 완료된 라벨만 선택
        # TODO: review_is_any_one_of = [ReviewStatus.APPROVE.value]
        completed_filter.dataset_is_any_one_of = [task_id]

        num_completed = self.client.get_num_labels(filter=completed_filter)
        num_in_progress = self.client.get_num_labels(filter=in_progress_filter)
        logger.info(f"task id: {task_id}, num_completed: {num_completed}, num_in_progress: {num_in_progress}, num_total: {num_total}")

        return LabellingInfo(
            completed_count=num_completed,
            total_count=num_total,
            status=LabellingStatus.INPROGRESS if num_in_progress > 0 else LabellingStatus.COMPLETE,
        )
    
    def download_labels(self, task_id: str, save_dir: str) -> str:
        # 완료된 라벨만 필터링
        completed_filter = SearchFilter()
        completed_filter.status_is_any_one_of = [Status.SUBMITTED.value]  # 완료된 라벨만 선택
        # TODO: review_is_any_one_of = [ReviewStatus.APPROVE.value]
        completed_filter.dataset_is_any_one_of = [task_id]

        # 라벨 데이터 가져오기
        basename_list, boxes_list, poses_list = self._read_labels(completed_filter)

        # 라벨 데이터 저장
        self._save_labels(save_dir, task_id, basename_list, boxes_list, poses_list)

        


    def _read_labels(self, filter: SearchFilter):
        n_label, handlers, cursor = self.client.get_labels(filter=filter)
        
        # Collect all handlers first
        all_handlers = []
        count = 0
        while count < n_label:
            all_handlers.extend(handlers)
            count += len(handlers)
            n_label, handlers, cursor = self.client.get_labels(
                filter, cursor=cursor
            )    

        basename_list, boxes_list, poses_list = [], [], []
        for handler in handlers:
            basename = handler.data.data_key  # trimouse_00001234.png
            label = handler.data.to_json()["result"]["objects"]
            
            boxes = []
            poses = []
            for single_label in label:
                if "box" in single_label["annotation_type"]:
                    x, y, width, height = parse_box(single_label)
                    boxes.append([x, y, width, height])
                elif "keypoint" in single_label["annotation_type"]:
                    pose = parse_pose(single_label)
                    poses.append(pose)

            basename_list.append(basename)
            boxes_list.append(boxes)
            poses_list.append(poses)

        return basename_list, boxes_list, poses_list


    def _save_labels(self, save_dir: str, task_id: str, basename_list: list, boxes_list: list, poses_list: list):
        label_dir = os.path.join(save_dir, 'labels', task_id)
        image_dir = os.path.join(save_dir, 'frames', task_id)

        os.makedirs(label_dir, exist_ok=True)
        logger.info(f"basename_list: {basename_list}")
        for basename, boxes, poses in zip(basename_list, boxes_list, poses_list):
            label_file = os.path.join(label_dir, f"{os.path.splitext(basename)[0]}.txt")
            image_file = os.path.join(image_dir, basename)
            logger.info(f"label_file: {label_file}, image_file: {image_file}")
            image_height, image_width = cv2.imread(image_file).shape[:2]
            boxes, poses = match_boxes_and_poses(boxes, poses, n_keypoints=11)
            boxes_xywhn = [
                box_x0y0wh_to_xcycwhn(box, image_width, image_height) for box in boxes
            ]
            poses_xyn = [
                pose_xyv_to_xyvn(pose, image_width, image_height) for pose in poses
            ]

            with open(label_file, "w") as f:
                for box_xywhn, pose_xyn in zip(boxes_xywhn, poses_xyn):
                    box_str = " ".join(map(str, box_xywhn))
                    pose_str = " ".join(map(str, pose_xyn))
                    line = f"0 {box_str} {pose_str}"
                    f.write(line + "\n")

