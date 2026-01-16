# Use slim-bookworm for a stable Debian base
FROM python:3.11-slim-bookworm

# Install system dependencies (required for image processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- FIX: Pre-download the U2NET model (Robust Method) ---
# We use 'new_session' which triggers the download automatically.
ENV U2NET_HOME=/app/.u2net
RUN mkdir -p $U2NET_HOME \
    && python -c "from rembg import new_session; new_session('u2net')"

# Copy application code & static files
COPY main.py .
COPY static ./static

# Expose the port
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
