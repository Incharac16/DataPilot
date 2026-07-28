import os
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.services.data_loader import save_upload
from app.utils.file_validator import validate_extension, validate_file_size

router = APIRouter()


@router.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    try:
        validate_extension(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    contents = await file.read()

    try:
        validate_file_size(len(contents), settings.max_upload_mb)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    dataset_id, file_path = save_upload(contents, file.filename)

    try:
        if file.filename.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse file: {str(e)}",
        ) from e

    return {
        "id": dataset_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "size_bytes": os.path.getsize(file_path),
        "uploaded_at": datetime.utcnow().isoformat(),
        "status": "ready",
    }
