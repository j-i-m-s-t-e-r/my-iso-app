FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Speed up startup by disabling GPU search
ENV ONNXRUNTIME_EXECUTION_PROVIDERS=CPUExecutionProvider

# Copy app code
COPY main.py .
COPY static ./static

# Run the python script directly
CMD ["python", "main.py"]
