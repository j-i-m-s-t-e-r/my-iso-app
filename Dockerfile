# FIX 1: Use 'slim-bookworm' instead of just 'slim'. 
# This locks us to Debian 12 (stable) which has reliable repositories.
FROM python:3.11-slim-bookworm

# FIX 2: Add '--fix-missing' and '--no-install-recommends'
# We also ensure the update runs immediately before install in the same layer.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- TRICK: Pre-download the U2NET model ---
ENV U2NET_HOME=/app/.u2net
RUN mkdir -p $U2NET_HOME \
    && python -c "from rembg.bg import download_model; download_model('u2net')"

# Copy application code & static files
COPY main.py .
COPY static ./static

# Expose the port
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
