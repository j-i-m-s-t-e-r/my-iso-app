@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file: {file.filename}")
        
        # 1. READ FILE
        input_data = await file.read()
        
        # --- MEMORY SAVER STEP ---
        # Open the image with Pillow first to resize it
        with Image.open(io.BytesIO(input_data)) as input_img:
            # Convert to RGBA to handle any format safely
            input_img = input_img.convert("RGBA")
            
            # Force resize to max 800x800px
            # This ensures the AI model never eats more than ~300MB RAM
            input_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save back to bytes to feed into rembg
            buffer = io.BytesIO()
            input_img.save(buffer, format="PNG")
            resized_bytes = buffer.getvalue()
            
        logger.info("Image resized for memory safety.")
        # -------------------------

        # 2. REMOVE BACKGROUND (Now using the smaller image)
        try:
            # We pass the resized bytes, NOT the original large file
            no_bg_data = remove(resized_bytes, session=session)
            logger.info("Background removed successfully.")
        except Exception as bg_error:
            logger.error(f"Error in REMBG: {bg_error}")
            raise HTTPException(status_code=500, detail="AI Processing Failed")

        # 3. GEOMETRY (Isolating the result)
        with Image.open(io.BytesIO(no_bg_data)) as img:
            img = img.convert("RGBA")
            
            # Rotate 45 degrees
            rotated = img.rotate(45, expand=True, resample=Image.BICUBIC)
            
            # Squash height
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
