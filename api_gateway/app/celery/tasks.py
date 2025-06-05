from celery import chain
from .app import celery_app

# Placeholder imports of actual processing functions
from video_processor.app.worker import process_video_download_request, process_frames_extraction_request
from labeling_manager.app.worker import process_frames_extracted
from model_trainer.app.worker import process_model_training_requested
from model_deployer.app.worker import process_model_deployment_requested
from model_inference.app.worker import process_inference_requested

@celery_app.task(bind=True, max_retries=3)
def download_video(self, data):
    process_video_download_request(data)
    return data

@celery_app.task(bind=True, max_retries=3)
def extract_frames(self, data):
    process_frames_extraction_request(data)
    return data

@celery_app.task(bind=True, max_retries=3)
def request_labeling(self, data):
    process_frames_extracted(data)
    return data

@celery_app.task(bind=True, max_retries=3)
def train_model(self, data):
    process_model_training_requested(data)
    return data

@celery_app.task(bind=True, max_retries=3)
def deploy_model(self, data):
    process_model_deployment_requested(data)
    return data

@celery_app.task(bind=True, max_retries=3)
def run_inference(self, data):
    process_inference_requested(data)
    return data


def start_pipeline(task_data):
    workflow = chain(
        download_video.s(task_data),
        extract_frames.s(),
        request_labeling.s(),
        train_model.s(),
        deploy_model.s(),
        run_inference.s(),
    )
    workflow.delay()

