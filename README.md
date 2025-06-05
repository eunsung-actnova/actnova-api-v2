
## 🧱 전체 시스템 구조

```
📦 docker-compose.yml
├── 🧩 api_gateway          # REST API + 동영상 처리, 요청 수신, 알림 포함 (서비스가 커질 경우 분리)
├── 🧠 model_trainer        # 모델 학습 + epoch별 콜백
├── 🔍 labeling_monitor     # 라벨링 상태 폴링 + 완료 시 RabbitMQ 트리거
├── 📤 model_exporter       # 모델 결과(csv/json/video) 생성 및 notebook/onnx 변환
├── 🚀 triton_server        # ONNX 모델 호스팅
├── 📨 rabbitmq             # 메시지 브로커
```

---

## 📌 `api_gateway` 역할 상세

| 기능 | 설명 |
| --- | --- |
| 🎬 동영상 처리 | 다운로드, 메타 추출, 변환, 업로드, 검증 |
| 🧪 추론 요청 | 글로벌/최종 모델 추론, 결과 반환 |
| 🏋️ 학습 요청 | train/test split, 라벨 확인, 학습 요청 전달 |
| 🔔 알림 | 각 단계 완료 시 트리거 → 클라이언트 or 내부 큐 전달 |
| 📊 실시간 진행률 | 다운로드/학습 등 실시간 상태 프론트 전송 (WebSocket or Redis pub/sub or DB + polling) |

## actverse steps
```
[video input(path)] -> [비디오 다운로드, 비디오 프레임 추출] -> [비디오 추론] -> [라벨링] -> [모델 학습] -> [모델 배포] -> [모델 추론] -> [추론 결과 업로드] 

background tasks: [labeling monitoring] # 라벨링 완료 모니터링
```

## 결과물
```
# /app/data_storage/
frames/{task_id}/
labels/{task_id}/
videos/{task_id}/
train_log/{task_id}/
ㄴdata
    ㄴimages
        ㄴtrain
        ㄴval
    ㄴlabels
        ㄴtrain
        ㄴval
model.pt
ㄴdata.yaml
inference_results/
models/
```

## TODO
- [ ] 메세지 스텝 로그로 한 번에 알아볼 수 있도록 고치기
- [ ] 세부사항 구현
    - [ ] triton 띄우기
- [x] 공통모듈로 컨테이너 간 중복코드 합치기(e.g: 메세지 발행/구독/소비, 로깅)
- [ ] config로 고정값들(비디오, 프레임 다운로드 경로 등) 정리하기
- [ ] 각 컨테이너별로 공유되는 데이터는 `data_storage` 볼륨에 저장. 더 나은 방법이 있는지 찾아봐야함. (S3와 같은. 더 큰 데이터에 대한 처리)
- [ ] 라벨 업로드 형태
    - [project name] - [task id]
- [ ] 알림(slack, email) 기능
- [ ] 에러 처리(데이터가 없는 경우, 프로세스 중간에 중단된 경우 등등)
- [ ] DI 적용하기
- [ ] 문서 만들기
- [ ] python-sdk에서 YOLO(학습, 추론, 데이터 구성) 부분 추출하기 => python-sdk 리팩토링 
    - [ ] YOLO 학습 데이터 구성 시에 직접 이미지 복사 후 처리


- [ ] vercel blob에 결과 업로드
- [ ] slack에 알림
- [ ] 라벨링 완료 태스크 알림 조건은 리뷰 APPROVE 상태여야함
- [ ] vercel api에 결과 보내줘야함
- [ ] 결과 동영상, 노트북 스크립트


## actverse components
** 각 컴포넌트는 개별 도커 컨테이너로 구성

- api-gateway: 사용자에게 제공할 엔드포인트

- rabbitmq: actverse steps를 메세지로 관리함. 실패 시 재시도 로직과 각 단계별 로깅 적용

- video-processor: 인풋 비디오에 대한 다운로드, 프레임 추출, 업로드 처리

- labeling-manager: 라벨링 툴에 라벨링할 이미지 전송, 태스크 완료율 조회
    - labeling-monitor: 태스크의 라벨링 완료율 모니터링 후, 완료 시 재학습 트리거링

- celery-worker: 라벨링 태스크 

- model-trainer: 모델 학습 

- model-deployer: 완료된 모델 배포

- model-inference: 모델 추론

- event-worker: 각 단계의 완료 이벤트 구독 및 트리거링 이벤트 발행


## 메세지 프로세스

api 요청 -> mq -> 비디오 다운로드  
api 요청 -> mq -> 요청기록 저장  
비디오 다운로드 -> mq -> 비디오 프레임 추출  
비디오 프레임 추출 -> mq -> 비디오 추론  
비디오 프레임 추출 -> mq -> 라벨링 요청  
라벨링 완료 -> mq -> 재학습  
재학습 완료 -> mq -> 모델 배포  
모델 배포 -> mq -> 모델 추론  
모델 추론 -> mq -> 모델 결과 업로드  

## 메세지 세부정보

- EVENT_VIDEO_DOWNLOAD_REQUESTED, data = {'task_id', 'video_path', 'user_id'} -> EVENT_VIDEO_DOWNLOADED  
- EVENT_VIDEO_DOWNLOADED, data = {'task_id', 'downloaded_video_path', 'original_video_path', 'status' } -> EVENT_FRAMES_EXTRACTION_REQUESTED
- EVENT_FRAMES_EXTRACTED, data = {'task_id', 'frames_path', 'num_frames', 'status'} -> EVENT_LABELING_REQUESTED
- EVENT_LABELING_REQUESTED, data = {'task_id', 'frames_path', 'status': 'created'}
- EVENT_LABELING_COMPLETED, data = {'task_id', 'label_path', 'status'}
- EVENT_MODEL_TRAINED, data = {'task_id', 'model_path', 'status', 'metrics'}
- EVENT_MODEL_DEPLOYMENT_REQUESTED, data = {'task_id', 'model_path', 'deployment_id', 'status', 'endpoint'} -> EVENT_MODEL_DEPLOYED
- EVENT_INFERENCE_REQUESTED, data = {'task_id', 'model_path', 'inference_data_path'}
- EVENT_INFERENCE_COMPLETED, data = {'task_id', 'result_json_path', 'status'}


# 공통 메시지 타입 정의 (별도 파일)
#### api_gateway
- publish
EVENT_TASK_CREATED = "task.created"  
EVENT_VIDEO_DOWNLOAD_REQUESTED = "video.download.requested"  

#### video_processor
- subscribe 
EVENT_VIDEO_DOWNLOAD_REQUESTED = "video.download.requested"  
EVENT_FRAMES_EXTRACTION_REQUESTED = "frames.extraction.requested"  
- publish
EVENT_VIDEO_DOWNLOADED = "video.downloaded"
EVENT_FRAMES_EXTRACTED = "frames.extracted"

#### labeling_manager
- subscribe
EVENT_FRAMES_EXTRACTED = "frames.extracted"
- publish
EVENT_LABELING_REQUESTED = "labeling.requested"

#### labeling_monitor
- publish
EVENT_LABELING_COMPLETED = "labeling.completed"

#### model_trainer
- subscribe
EVENT_LABELING_COMPLETED = "labeling.completed"
- publish
EVENT_MODEL_TRAINING_COMPLETED = "model.training.completed"

#### model_deployer
- subscribe
EVENT_MODEL_DEPLOYMENT_REQUESTED = "model.deployment.requested"
- publish
EVENT_MODEL_DEPLOYED = "model.deployed"

### model-inference
- subscribe
EVENT_MODEL_DEPLOYED = "model.deployed"
EVENT_INFERENCE_REQUESTED = "inference.requested"
- publish
EVENT_INFERENCE_COMPLETED = "inference.completed"

## 엔드포인트
#### API Gateway
| 엔드포인트 | 메소드 | Body | Params | 출력 | 설명 | 발생 가능한 에러 |
|------------|--------|------|--------|------|------|----------------|
| /tasks/ | `POST` | file_path, user_id | - | task_id | actverse 프로세스 요청 | 400: 잘못된 요청 데이터<br>401: 인증 실패<br>500: 서버 오류 |
| /status/{task_id} | `GET` | - | task_id | process_status | actverse 프로세스 진행율 요청 | 404: task_id 찾을 수 없음<br>500: 서버 오류 |

#### Video Processor
| 엔드포인트 | 메소드 | Body | Params | 출력 | 설명 | 발생 가능한 에러 |
|------------|--------|------|--------|------|------|----------------|
| /video/download | `POST` | file_path, download_path | - | download_path | 비디오 다운로드 | 400: 잘못된 파일 경로<br>404: 파일 찾을 수 없음<br>500: 다운로드 실패 |
| /video/extract-frames | `POST` | file_path, num_frames | - | frame_path | 비디오 프레임 추출 | 400: 잘못된 요청 데이터<br>404: 파일 찾을 수 없음<br>500: 프레임 추출 실패 |
| /video/upload | `POST` | file_path, upload_path | - | - | 404: 파일 찾을 수 없음<br>500: 업로드 실패 |

#### Labeling Manager
| 엔드포인트 | 메소드 | Body | Params | 출력 | 설명 | 발생 가능한 에러 |
|------------|--------|------|--------|------|------|----------------|
| /labeling | `POST` | folder_path, task_id, user_id | - | - | 라벨링 요청 | 400: 잘못된 폴더 경로<br>404: 폴더 찾을 수 없음<br>500: 라벨링 작업 실패 |
| /labeling/{task_id} | `GET` | - | task_id | - | 라벨링 태스크 상태 요청 | 404: task_id 찾을 수 없음<br>500: 서버 오류 |

#### Model Trainer
| 엔드포인트 | 메소드 | Body | Params | 출력 | 설명 | 발생 가능한 에러 |
|------------|--------|------|--------|------|------|----------------|
| /training | `POST` | data_path, mode_train_info | - | - | 모델 학습 요청 | 400: 잘못된 데이터 경로<br>422: 잘못된 학습 설정<br>500: 학습 실패 |
| /training/{task_id} | `GET` | - | task_id | current_epoch | 모델 학습 태스크 상태 요청 | 404: task_id 찾을 수 없음<br>500: 서버 오류 |

#### Model Deployer
| 엔드포인트 | 메소드 | Body | Params | 출력 | 설명 | 발생 가능한 에러 |
|------------|--------|------|--------|------|------|----------------|
| /deployments | `POST` | task_id, model_path | - | - | 모델 배포 요청 | 400: 잘못된 모델 경로<br>404: 모델 찾을 수 없음<br>500: 배포 실패 |

#### Model Inference
| 엔드포인트 | 메소드 | Body | Params | 출력 | 설명 | 발생 가능한 에러 |
|------------|--------|------|--------|------|------|----------------|
| /models | `GET` | - | - | - | 배포 모델 리스트 조회 | 500: 서버 오류 |
| /models/{task_id}/inference | POST | data_path, confidence, iou, batch_size, frame_skip, max_frames | - | results | 모델 추론 요청 | 400: 잘못된 데이터 경로<br>404: 모델 찾을 수 없음<br>422: 잘못된 추론 파라미터<br>500: 추론 실패 |

#### logging
#### Notification



## 물리적 분리
- api gateway, /video/download, /video/upload, /labeling, /labeling/{task_id}, /training/{task_id} (라우터로 구분)
- /video/extract-frames  
- model trainer  
- model deployer  
- model inference  
- labeling monitor(celery beat)
- labeling worker


## 라벨링 상태
IN_PROGRESS
COMPLETED