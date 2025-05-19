import os
from fastapi import FastAPI
from app.routers import tasks, status, video, labeling, training, deployments, models
from app.services.task_tracker import TaskTracker
app = FastAPI(
    title="ActVerse API Gateway",
    description="ActVerse API 게이트웨이",
    version="0.1.0"
)

# 모든 라우터 등록
app.include_router(tasks.router)
app.include_router(status.router)
app.include_router(video.router)
app.include_router(labeling.router) 
app.include_router(training.router)
app.include_router(deployments.router)
app.include_router(models.router)

# 시작 시 태스크 트래커 시작
@app.on_event("startup")
async def startup_event():
    task_tracker = TaskTracker.get_instance(os.getenv("DATABASE_URL"))
    task_tracker.start()

@app.get("/")
async def root():
    return {"message": "ActVerse API Gateway"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)