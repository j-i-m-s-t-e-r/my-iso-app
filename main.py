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
# This ensures errors show up in the Render dashboard logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 2. LOAD AI MODEL (LIGHTWEIGHT VERSION)
# We use 'u2netp' because it uses ~170MB RAM vs 1GB+ for standard models.
# We load it globally on startup so the first user request isn't slow.
model_name = "u2netp"
try:
    logger.info(f"Loading AI model: {model_name}...")
    session = new_session(model_name)
    logger.info("AI model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load AI model: {e}")
    sys.exit(1)

# 3. INITIALIZE APP (This was missing in your error)
app = FastAPI()

# 4. MOUNT STATIC FILES
# This serves your index.html and any future CSS/JS
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/health")
def health_check():
    # Render checks this endpoint to know if the app is alive
    return {"status": "ok"}

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file: {file.filename}")
        
        # Read the uploaded bytes
        input_data = await file.read()
        
        # --- MEMORY PROTECTION STEP ---
        # The Render Free Tier has 512MB RAM. If we process a 4K image, it crashes.
        # We assume the input is a logo, so we resize it to max 800px.
        with Image.open(io.BytesIO(input_data)) as input_img:
            input_img = input_img.convert("RGBA")
            
            # Resize if larger than 800px
            if input_img.width > 800 or input_img.height > 800:
                logger.info(f"Resizing image from {input_img.size} to max 800px to save RAM.")
                input_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save the resized image back to bytes for rembg to use
            buffer = io.BytesIO()
            input_img.save(buffer, format="PNG")
            processed_input_bytes = buffer.getvalue()

        # 5. REMOVE BACKGROUND
        # We pass the pre-loaded 'session' to speed it up
        try:
            no_bg_data = remove(processed_input_bytes, session=session)
            logger.info("Background removed successfully.")
        except Exception as bg_error:
            logger.error(f"REMBG Error: {bg_error}")
            raise HTTPException(status_code=500, detail="AI Background Removal Failed")

        # 6. ISOMETRIC TRANSFORMATION
        with Image.open(io.BytesIO(no_bg_data)) as img:
            img = img.convert("RGBA")
            
            # Rotate 45 degrees Counter-Clockwise
            # expand=True ensures corners don't get clipped
            rotated = img.rotate(45, expand=True, resample=Image.BICUBIC)
            
            # Calculate new height for 30-degree isometric view
            # tan(30) approx 0.57735
            w, h = rotated.size
            new_h = int(h * 0.57735)
            
            # Squash the height to create the isometric perspective
            final_iso = rotated.resize((w, new_h), resample=Image.LANCZOS)
            
            # Save result to buffer
            output_buffer = io.BytesIO()
            final_iso.save(output_buffer, format="PNG")
            output_data = output_buffer.getvalue()

        logger.info("Transformation complete. Returning response.")
        return Response(content=output_data, media_type="image/png")

    except Exception as e:
        logger.error(f"CRITICAL ERROR processing request: {str(e)}")
        # This returns a 500 error to the browser so the JS can catch it
        raise HTTPException(status_code=500, detail=str(e))

# 7. APP ENTRY POINT
if __name__ == "__main__":
    # Render sets the PORT environment variable. Default to 10000 locally.
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
