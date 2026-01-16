import os
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from rembg import remove, new_session
from PIL import Image
import io

# Initialize the model session on startup to prevent "downloading" lag
new_session("u2net")

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    input_data = await file.read()
    no_bg_data = remove(input_data)
    
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

# --- NEW SECTION: Programmatic Start ---
if __name__ == "__main__":
    # Get the PORT from Render's environment, default to 10000 if missing
    port = int(os.environ.get("PORT", 10000))
    # Run Uvicorn directly from Python
    uvicorn.run(app, host="0.0.0.0", port=port)
