FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Explicitly install onnxruntime (CPU) to prevent it hunting for GPU packages
RUN pip install --no-cache-dir onnxruntime rembg[cpu] fastapi python-multipart uvicorn pillow numpy

# Speed up startup
ENV ONNXRUNTIME_EXECUTION_PROVIDERS=CPUExecutionProvider

# --- FIX: Pre-download the LIGHTWEIGHT model ---
ENV U2NET_HOME=/app/.u2net
RUN mkdir -p $U2NET_HOME \
    && python -c "from rembg import new_session; new_session('u2netp')"

COPY main.py .
COPY static ./static

CMD ["python", "main.py"]
