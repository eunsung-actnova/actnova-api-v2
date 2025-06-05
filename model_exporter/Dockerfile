FROM python:3.9-slim

WORKDIR /app

# Install common library
COPY common /app/common
RUN pip install -e /app/common

# Install service-specific dependencies
COPY ./model_exporter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY ./model_exporter/app /app/app

CMD ["python", "-m", "app.main"]
