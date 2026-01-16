import os
import uvicorn
import logging
import sys
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from rembg import remove, new_session
from PIL import Image

# 1. SETUP LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 2. GLOBAL SESSION VAR (Init as None)
# We don't load the model here anymore. We wait until the first request.
session = None
model_name = "u2netp"

app = FastAPI()

# 3. MOUNT STATIC FILES
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    global session
    try:
        logger.info(f"Received file: {file.filename}")
        
        # --- LAZY LOAD: Load Model only when needed ---
        if session is None:
            logger.info(f"First run detected. Loading AI model ({model_name})...")
            try:
                session = new_session(model_name)
                logger.info("AI Model loaded!")
            except Exception as load_err:
                logger.error(f"Model Load Failed: {load_err}")
                raise HTTPException(status_code=500, detail="Server failed to wake up AI.")

        # --- READ & RESIZE ---
        input_data = await file.read()
        
        with Image.open(io.BytesIO(input_data)) as input_img:
            input_img = input_img.convert("RGBA")
            # Resize for memory safety (Free Tier Limit)
            if input_img.width > 800 or input_img.height > 800:
                input_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            input_img.save(buffer, format="PNG")
            processed_input_bytes = buffer.getvalue()

        # --- PROCESS ---
        no_bg_data = remove(processed_input_bytes, session=session)
        
        with Image.open(io.BytesIO(no_bg_data)) as img:
            img = img.convert("RGBA")
            rotated = img.rotate(45, expand=True, resample=Image.BICUBIC)
            w, h = rotated.size
            new_h = int(h * 0.57735)
            final_iso = rotated.resize((w, new_h), resample=Image.LANCZOS)
            
            output_buffer = io.BytesIO()
            final_iso.save(output_buffer, format="PNG")
            output_data = output_buffer.getvalue()

        return Response(content=output_data, media_type="image/png")

    except Exception as e:
        logger.error(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
