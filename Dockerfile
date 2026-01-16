FROM python:3.11-slim-bookworm

# 1. Enable Unbuffered Logging (Critical for debugging)
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Speed up startup
ENV ONNXRUNTIME_EXECUTION_PROVIDERS=CPUExecutionProvider

# Pre-download the model to disk (so the first user request is faster)
ENV U2NET_HOME=/app/.u2net
RUN mkdir -p $U2NET_HOME \
    && python -c "from rembg import new_session; new_session('u2netp')"

COPY main.py .
COPY static ./static

# Run python directly (Handing control to your main.py logic)
CMD ["python", "main.py"]
