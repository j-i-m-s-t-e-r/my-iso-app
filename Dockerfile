# Use slim-bookworm for stable Debian 12
FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- SPEED FIXES ---
# 1. Force ONNX to use CPU only (Prevents "GPU device discovery" delay)
ENV ONNXRUNTIME_EXECUTION_PROVIDERS=CPUExecutionProvider
# 2. Set Render's default port explicitly
ENV PORT=10000
# 3. Pre-download model
ENV U2NET_HOME=/app/.u2net
RUN mkdir -p $U2NET_HOME \
    && python -c "from rembg import new_session; new_session('u2net')"

# Copy application code
COPY main.py .
COPY static ./static

# Expose port 10000 (Render's Standard)
EXPOSE 10000

# --- CMD FIX ---
# We use the shell form (no brackets) so it can read the $PORT variable
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
