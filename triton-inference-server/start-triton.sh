docker run \
    -d \
    --name triton-server \
    --gpus all \
    -v ./models:/models \
    -p 8000:8000 nvcr.io/nvidia/tritonserver:24.03-py3 tritonserver \
    --model-repository=/models \
    --log-verbose=1 \
    --load-model=* \
    --model-control-mode=explicit
    