

## Developer
[contributing](README_CONTRIBUTING.md)


## TODO
- [ ] CI-CD 구성 
    - [ ] dev, prod 분리
    - [ ] Makefile 작성
    - [ ] 테스트 케이스 작성
    - [ ] 무중단 배포
- [ ] 테스트 작성.
- [ ] 알림 기능. 스텝별 적용하기
- [ ] 상태 호출 API - redis에 적재한 후, 주기적으로 front에 전송
- [ ] 에러 처리(데이터가 없는 경우, 프로세스 중간에 중단된 경우 등등)
- [ ] DI 적용하기
- [ ] 문서 만들기
- [ ] python-sdk에서 YOLO(학습, 추론, 데이터 구성) 부분 추출하기 => python-sdk 리팩토링 
    - [ ] YOLO 학습 데이터 구성 시에 직접 이미지 복사 후 처리



## 🧱 전체 시스템 구조

```
📦 docker-compose.yml
├── 🧩 api_gateway                # REST API, 동영상 처리, 요청 수신, 알림 등
│   ├── celery                   # 비동기 태스크 처리
│   ├── features                 # 주요 기능별 도메인 코드
│   │   ├── labeling_manager     # 라벨링 요청, 완료율 모니터링
│   │   ├── video_processor      # 동영상 다운로드, 프레임 추출, 업로드
│   │   ├── model_inference      # 모델 추론, 결과 처리/업로드
│   │   └── notification         # 알림
│   ├── routers                  # API 라우팅
│   ├── services                 # 서비스 로직(features에서 함수 사용)
│   ├── entities                 # DB ORM 엔티티(Task 등, RDB 테이블 매핑)
│   ├── schemas                  # API 입출력(Pydantic)
│   │   ├── task.py
│   │   ├── video.py
│   │   └── label.py
│   ├── main.py
├── 🧠 model_trainer              # 모델 학습 + epoch별 콜백
├── 📤 model_exporter             # 모델 결과(csv/json/video) 생성 및 notebook/onnx 변환
├── 🚀 triton_server              # ONNX 모델 호스팅
├── 📨 rabbitmq                   # 메시지 브로커
```



## actverse components

물리적(도커 컨테이너) 구분
- api-gateway
- celery worker
- celery beat: 태스크의 라벨링 완료율 모니터링 후, 완료 시 재학습 트리거링
- rabbitmq: actverse steps를 메세지로 관리함. 실패 시 재시도 로직과 각 단계별 로깅 적용
- model-trainer: 모델 학습
- model-deployer: onnx 변환
- triton-server: 모델 호스팅

<br></br>

- celery worker
    - video-processor: 인풋 비디오에 대한 다운로드, 프레임 추출, 업로드 처리
    - labeling-manager: 라벨링 툴에 라벨링할 이미지 전송, 태스크 완료율 조회
    - model-inference: 모델 추론
    - notification: 슬랙, 이메일 알림




#### Celery로 chain할 부분
- 동영상 다운로드 -> 동영상 검증 -> 동영상 변환 -> 프레임 추출 -> 라벨링 요청
- 분석 결과 csv, json, overlaid video, json chunks chord로 병렬 업로드

#### RabbitMQ로 처리해야할 부분(컨테이너 분리로 인한)
- 동영상 처리 -> 모델 학습 EVENT_VIDEO_DOWNLOADED -> EVENT_MODEL_TRAINING_REQUESTED
- 모델 학습 완료 -> 모델 저장(변환) EVENT_MODEL_TRAINING_COMPLETED -> EVENT_MODEL_CONVERSION_REQUESTED
- 모델 저장(변환) -> 모델 로드(서빙) EVENT_MODEL_CONVERSION_COMPLETED -> EVENT_MODEL_DEPLOYMENT_REQUESTED
- 모델 로드(서빙) -> 분석 EVENT_MODEL_DEPLOYED -> EVENT_INFERENCE_REQUESTED




## 📌 `api_gateway` 역할 상세

| 기능 | 설명 |
| --- | --- |
| 🎬 동영상 처리 | 다운로드, 메타 추출, 변환, 업로드, 검증(celery worker로 구성) |
| 🧪 추론 요청 | 글로벌/최종 모델 추론, 결과 반환(celery worker로 구성) |
| 🏋️ 학습 요청 | train/test split, 라벨 확인, 학습 요청 전달(celery worker로 구성) |
| 🔔 알림 | 각 단계 완료 시 트리거 → 클라이언트 or 내부 큐 전달(celery worker로 구성) |
| 📊 실시간 진행률 | (celery worker로 구성)다운로드/학습 등 실시간 상태 프론트 전송 (WebSocket or Redis pub/sub or DB + polling) |
| 🔍 labeling_monitor     | 라벨링 상태 폴링(celery beat로 구성) + 완료 시 RabbitMQ 트리거 |

## actverse steps
```
[video input(url)] -> [비디오 다운로드] -> [비디오 변환] -> [비디오 프레임 추출] -> [글로벌 모델로 분석] -> [라벨링 중] -> (라벨링 완료 시) -> [라벨링 다운로드] -> [사용자 모델 학습] -> [사용자 모델 저장] -> [사용자 모델 배포] -> [사용자 모델로 분석] -> [분석 결과 업로드]

[비디오 다운로드] -> [글로벌 모델로 분석]
[분석 결과 업로드] -> [csv 업로드]
                  -> [json 업로드]
                  -> [overlaid video 업로드]


background tasks: [labeling monitoring] # 라벨링 완료 모니터링
```

## 단계별 input/output

| 단계                | Input                                                      | Output                                   |
|---------------------|-----------------------------------------------------------|------------------------------------------|
| 모델 초기 요청      | -                                                          | -                                        |
| 동영상 처리         | task_id, user_id, download_path, frame_path                | mb, frames, video_type, frame_path       |
| 글로벌 모델로 분석  | task_id, user_id, download_path                            | task_id, user_id, inference_result_path  |
| 라벨링 요청         | task_id, user_id, frame_path                               | -                                        |
| 라벨링 완료         | task_id, user_id                                           | task_id, user_id, labeling_path          |
| 사용자 모델 학습    | task_id, user_id, labeling_path                            | task_id, user_id, model_path             |
| 사용자 모델 저장    | task_id, user_id, model_path                               | task_id, user_id, deployment_id          |
| 사용자 모델 로드    | task_id, user_id, deployment_id                            | -                                        |
| 사용자 모델로 분석  | task_id, user_id, deployment_id, inference_data_path       | task_id, user_id, inference_result_path  |
| 분석 파일 업로드    | task_id, user_id, inference_result_path                    | task_id, user_id                         |


## 결과물
```
# /app/data_storage/
frames/{task_id}/
labels/{task_id}/
videos/{task_id}/
train_log/{task_id}/
ㄴdata
    ㄴimages
        ㄴ{imagename}.jpg
        ...
    ㄴlabels    
        ㄴ{imagename}.txt
        ...
    train_test_split.txt
model.pt
ㄴdata.yaml
inference_results/
    - results.csv
    - results.json
    - chunks/ 
        ㄴresult_chunk_1.json
        ...
    - overlaid_results.mp4
models/
```


## Storage
- Redis: 태스크 status 저장(상태 덮어쓰기), 태스크 진행률 저장
- RDB(PostgresSQL): label task 저장, 전체 태스크 진행 기록 저장(시작 시간, 걸린 시간 등등)



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
