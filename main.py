from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from rembg import remove
from PIL import Image
import io
import os

app = FastAPI()

# 1. Mount the static folder to serve CSS/JS if needed in the future
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Serve the Frontend at the root URL
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# 3. The Processing Endpoint
@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    # Read file
    input_data = await file.read()

    # Remove Background (AI)
    # alpha_matting=True helps with softer edges, but is slower. 
    # Default is fine for logos.
    no_bg_data = remove(input_data)
    
    # Geometric Transformation
    with Image.open(io.BytesIO(no_bg_data)) as img:
        img = img.convert("RGBA")
        
        # Rotate 45 degrees Counter-Clockwise
        # expand=True ensures we don't crop the corners
        rotated = img.rotate(45, expand=True, resample=Image.BICUBIC)
        
        # Calculate new height for 30-degree isometric view (tan(30) = 0.57735)
        w, h = rotated.size
        new_h = int(h * 0.57735) 
        
        # Squash the height
        final_iso = rotated.resize((w, new_h), resample=Image.LANCZOS)
        
        # Save to buffer
        output_buffer = io.BytesIO()
        final_iso.save(output_buffer, format="PNG")
        output_data = output_buffer.getvalue()

    return Response(content=output_data, media_type="image/png")

@app.get("/health")
def health_check():
    return {"status": "ok"}
