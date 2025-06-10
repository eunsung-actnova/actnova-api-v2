from celery import chain, chord
from app.celery.app import celery_app

# Placeholder imports of actual processing functions
from app.services import video_service, labeling_service, train_model_service, inference_service


@celery_app.task(bind=True, max_retries=3)
def parse_video_info(self, data):
    video_info = video_service.parse_video_info(data)
    print('비디오 관련 정보가 수집되었습니다. 데이터베이스에 저장됩니다. 비디오 다운로드 단계로 넘어갑니다.')
    return video_info
    

@celery_app.task(bind=True, max_retries=3)
def download_video(self, data):
    video_service.download_video(data)
    print('비디오 파일이 다운로드되었습니다. "글로벌 모델로 분석" 단계를 트리거합니다. 비디오 변환 단계롤 넘어갑니다.')
    return data

@celery_app.task(bind=True, max_retries=3)
def convert_video(self, data):
    video_service.convert_video(data)
    print('비디오 파일이 변환되었습니다. 비디오 업로드와 프레임 추출 단계로 넘어갑니다.')
    return data

@celery_app.task(bind=True, max_retries=3)
def upload_video(self, data):
    '''vercel 저장소에 비디오 파일 업로드'''
    video_service.upload_video(data)
    print("변환한 파일을 업로드합니다.")
    return data
    

@celery_app.task(bind=True, max_retries=3)
def extract_frames(self, data):
    video_service.extract_frames(data)
    print("프레임 추출이 완료되었습니다. 라벨링 이미지 업로드 단계로 넘어갑니다.")
    # '글로벌 모델로 분석'을 트리거하는 RabbitMQ 메세지 호출
    
    return data

@celery_app.task(bind=True, max_retries=3)
def upload_labeling_images(self, data):
    labeling_service.upload_images(data)
    print("라벨링 이미지 업로드가 완료되었습니다. 라벨링 Task를 데이터베이스에 저장합니다.")
    
    
    

@celery_app.task(bind=True, max_retries=3)
def download_labeling_data(self, data):
    labeling_service.download_labels(data)
    print("라벨링 완료 신호를 받았습니다. 완료된 라벨을 다운로드합니다. 학습 데이터 준비 단계로 넘어갑니다.")
    
@celery_app.task(bind=True, max_retries=3)
def prepare_training_data(self, data):
    train_model_service.prepare_training_data(data)
    print("라벨링 데이터 준비가 완료되었습니다. 모델 학습 단계로 넘어갑니다.")
    
    # '사용자 모델 학습'을 트리거하는 RabbitMQ 메세지 호출
    
    return data


@celery_app.task(bind=True, max_retries=3)
def upload_csv(self, data):
    inference_service.upload_csv(data)
    print("모델 추론 결과를 csv로 저장합니다.")
    

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
    inference_service.run(data)
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
    
        