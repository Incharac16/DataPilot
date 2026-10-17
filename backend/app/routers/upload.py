import os
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from app.config import settings
from app.models.schemas import DatasetRecord
from app.services.data_loader import DatasetStore, load_dataframe_from_path, save_upload
from app.utils.file_validator import validate_extension, validate_file_size
from openpyxl.utils.exceptions import InvalidFileException
import pandas as pd

router = APIRouter()


@router.get("/api/datasets", response_model=list[DatasetRecord])
async def list_datasets():
    return [
        {
            "id": record["id"],
            "filename": record["filename"],
            "uploaded_at": record["uploaded_at"],
            "file_format": record["file_format"],
            "rows": record["row_count"],
            "columns": record["column_count"],
            "size_bytes": record["size_bytes"],
            "status": record["status"],
        }
        for record in DatasetStore.list()
    ]


@router.delete("/api/datasets/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: str):
    try:
        DatasetStore.delete(dataset_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return Response(status_code=204)


@router.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    try:
        validate_extension(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        validate_file_size(len(contents), settings.max_upload_mb)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    dataset_id, file_path = save_upload(contents, file.filename)

    try:
        df = load_dataframe_from_path(file_path)
    except (
        ValueError,
        OSError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
        zipfile.BadZipFile,
        InvalidFileException,
    ) as e:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse file: {str(e)}",
        ) from e

    uploaded_at = datetime.now(timezone.utc).isoformat()
    size_bytes = os.path.getsize(file_path)
    try:
        DatasetStore.register(
            file_path,
            file.filename,
            dataset_id,
            row_count=len(df),
            column_count=len(df.columns),
            size_bytes=size_bytes,
            uploaded_at=uploaded_at,
        )
    except sqlite3.Error as e:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not save dataset metadata.",
        ) from e

    return {
        "id": dataset_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "size_bytes": size_bytes,
        "uploaded_at": uploaded_at,
        "status": "ready",
    }
