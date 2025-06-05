from abc import ABC, abstractmethod
import os, json, zipfile
import pandas as pd
from typing import Dict, Any, Tuple

from actnova.model import Yolov8KeypointEstimator
from actverse_common.logging import setup_logger

logger = setup_logger(service_name="model_inference")




# TODO: 코드 정리

KEYPOINT_NAMES_MOUSE: dict[str, int] = {
    "nose": 0,
    "left_ear": 1,
    "right_ear": 2,
    "left_forepaw": 3,
    "right_forepaw": 4,
    "left_hindpaw": 5,
    "right_hindpaw": 6,
    "tail_root": 7,
    "tail_center": 8,
    "tail_tip": 9,
    "body_center": 10,
}


def convert_dict_to_dataframe(
    dict_data: Dict[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Convert dictionary Prediction data to DataFrame.

    Args:
        dict_data (Dict[str, Any]): Dictionary format data

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: metadata and pose results converted to DataFrames
    """

    # KEYPOINT_NAMES_MOUSE의 키값을 나열, 단 KEYPOINT_NAMES_MOUSE의 value를 오름차순으로 정렬함
    keypoint_names = sorted(
        KEYPOINT_NAMES_MOUSE.keys(), key=lambda x: KEYPOINT_NAMES_MOUSE[x]
    )

    # Create metadata DataFrame
    metadata_df = pd.DataFrame([dict_data["metadata"]])

    # Create results DataFrame
    rows = []
    for frame_idx, result in enumerate(dict_data["results"]):
        num_objects = max(len(result["ids"]), len(result["boxes"]))
        for i in range(num_objects):
            row_data = {
                "frame_idx": frame_idx,
                "timestamp": result["timestamp"],
                "id": result["ids"][i] if i < len(result["ids"]) else -1,
                "box_x": result["boxes"][i][0],
                "box_y": result["boxes"][i][1],
                "box_w": result["boxes"][i][2],
                "box_h": result["boxes"][i][3],
                "box_score": result["boxes_score"][i],
            }
            # Add keypoints data
            if result["keypoints"] and i < len(result["keypoints"]):
                for k, kp in enumerate(result["keypoints"][i]):
                    # row_data[f"keypoint_{k}_x"] = kp[0]
                    # row_data[f"keypoint_{k}_y"] = kp[1]
                    row_data[f"{keypoint_names[k]}_x"] = kp[0]
                    row_data[f"{keypoint_names[k]}_y"] = kp[1]

            # Add keypoints_score data
            if result["keypoints_score"] and i < len(result["keypoints_score"]):
                for k, score in enumerate(result["keypoints_score"][i]):
                    row_data[f"{keypoint_names[k]}_score"] = score

            # Add smoothed_keypoints data
            if result["smoothed_keypoints"] and i < len(result["smoothed_keypoints"]):
                for k, kp in enumerate(result["smoothed_keypoints"][i]):
                    row_data[f"smoothed_{keypoint_names[k]}_x"] = kp[0]
                    row_data[f"smoothed_{keypoint_names[k]}_y"] = kp[1]

            rows.append(row_data)

    results_df = pd.DataFrame(rows)

    return metadata_df, results_df



class ModelInference(ABC):

    @abstractmethod
    def __call__(self, input_data: str) -> str:
        raise NotImplementedError


class YOLOv8KeypointInference(ModelInference):
    def __init__(self, download_path: str):
        self.download_path = download_path

    def __call__(self, video_file: str, model_path: str, task_id: str):
        prediction_path = self.download_path / (
            f"prediction_{task_id}.json" if task_id else "prediction.json"
        )
        score_json_file = self.download_path / (
            f"score_{task_id}.json" if task_id else "score.json"
        )
        csv_metadata_file = self.download_path / (
            f"csv_metadata_{task_id}.csv" if task_id else "csv_metadata.csv"
        )
        csv_results_file = self.download_path / (
            f"csv_results_{task_id}.csv" if task_id else "csv_results.csv"
        )
        prediction_csv_path = self.download_path / (
            f"prediction_{task_id}.zip" if task_id else "prediction.zip"
        )
        base_name, ext = os.path.splitext(os.path.basename(video_file))
        result_video_file = self.download_path / f"{base_name}-Actverse.mp4" if task_id else None

        
        model = Yolov8KeypointEstimator(model_path)

        prediction = model.predict(video_file, num_mice=1)
    
        model.save_result_video(video_file, prediction, output=result_video_file)

        mean_num_mice = prediction.get_mean_num_mice()
        mean_box_score = prediction.get_mean_box_score()

        # 평가 결과 저장
        logger.info(f"Mean number of mice: {mean_num_mice}")
        logger.info(f"Mean box score: {mean_box_score}")

        score_data = ({"mean_num_mice": mean_num_mice, "mean_box_score": mean_box_score},)
        with open(score_json_file, "w") as f:
            json.dump(score_data, f, indent=None)

        prediction_json = prediction.to_json()
        with open(prediction_path, "w") as f:
            json.dump(prediction_json, f, indent=None)

        csv_metadata, csv_results = convert_dict_to_dataframe(prediction_json)
        csv_metadata.to_csv(csv_metadata_file, index=False)
        csv_results.to_csv(csv_results_file, index=False)

        # CSV 파일들을 ZIP으로 압축
        with zipfile.ZipFile(prediction_csv_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(csv_metadata_file, arcname=csv_metadata_file.name)
            zipf.write(csv_results_file, arcname=csv_results_file.name)

        return (
            str(prediction_path),
            str(prediction_csv_path),
            result_video_file,
            score_data,
        )




    