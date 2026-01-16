# Use a slim Python image
FROM python:3.11-slim

# Install system libs for Pillow/OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python libs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- PRE-DOWNLOAD AI MODEL ---
# This prevents the app from crashing on the first request
ENV U2NET_HOME=/app/.u2net
RUN mkdir -p $U2NET_HOME \
    && python -c "from rembg.bg import download_model; download_model('u2net')"

# Copy the app code AND the static folder
COPY main.py .
COPY static ./static

# Expose port (Render expects 10000 or similar, but we bind 0.0.0.0)
EXPOSE 8000

# Run Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
