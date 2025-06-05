from celery import chain, chord
from .app import celery_app

# Placeholder imports of actual processing functions
from app.services import video_service, labeling_service, train_model_service, inference_service
from model_inference.worker import process_inference_requested


@celery_app.task(bind=True, max_retries=3)
def parse_video_info(self, data):
    video_info = video_service.parse_video_info(data)
    return video_info
    

@celery_app.task(bind=True, max_retries=3)
def download_video(self, data):
    video_service.download_video(data)
    return data

@celery_app.task(bind=True, max_retries=3)
def convert_video(self, data):
    video_service.convert_video(data)
    return data

@celery_app.task(bind=True, max_retries=3)
def upload_video(self, data):
    '''vercel 저장소에 비디오 파일 업로드'''
    video_service.upload_video(data)
    return data
    

@celery_app.task(bind=True, max_retries=3)
def extract_frames(self, data):
    video_service.extract_frames(data)
    
    # '글로벌 모델로 분석'을 트리거하는 RabbitMQ 메세지 호출
    
    return data

@celery_app.task(bind=True, max_retries=3)
def upload_labeling_images(self, data):
    labeling_service.upload_images(data)
    

@celery_app.task(bind=True, max_retries=3)
def download_labeling_data(self, data):
    labeling_service.download_labels(data)
    
@celery_app.task(bind=True, max_retries=3)
def prepare_training_data(self, data):
    train_model_service.prepare_training_data(data)
    
    # '사용자 모델 학습'을 트리거하는 RabbitMQ 메세지 호출
    
    return data


@celery_app.task(bind=True, max_retries=3)
def upload_csv(self, data):
    inference_service.upload_csv(data)
    

@celery_app.task(bind=True, max_retries=3)
def upload_json(self, data):
    inference_service.upload_json(data)
    
@celery_app.task(bind=True, max_retries=3)    
def upload_overlaid_video(self, data):
    inference_service.upload_overlaid_video(data)

# @celery_app.task(bind=True, max_retries=3)
# def train_model(self, data):
#     process_model_training_requested(data)
#     return data

# @celery_app.task(bind=True, max_retries=3)
# def deploy_model(self, data):
#     process_model_deployment_requested(data)
#     return data

@celery_app.task(bind=True, max_retries=3)
def run_inference(self, data):
    process_inference_requested(data)
    return data


def video_pipeline(task_data):
    workflow = chain(
        parse_video_info.s(task_data),
        download_video.s(),
        convert_video.s(),
        upload_video.s(),
        extract_frames.s(),
        upload_labeling_images.s(),
    )
    workflow.delay()



def upload_inference_result_pipeline(task_data):
    workflow = chain(
        chord(
            upload_csv.s(task_data),
            upload_json.s(task_data),
            upload_overlaid_video.s(task_data),
        )()
    )
    workflow.delay()
    
        