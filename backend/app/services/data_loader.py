import json
import uuid
from pathlib import Path

import pandas as pd

from app.config import settings


class DatasetStore:
    _registry = {}

    @classmethod
    def register(cls, file_path: Path, filename: str, dataset_id: str):
        cls._registry[dataset_id] = {
            "path": file_path,
            "filename": filename,
        }

    @classmethod
    def get(cls, dataset_id: str):
        if dataset_id not in cls._registry:
            raise KeyError(f"Dataset '{dataset_id}' not found")
        return cls._registry[dataset_id]

    @classmethod
    def exists(cls, dataset_id: str):
        return dataset_id in cls._registry


def save_upload(file_content: bytes, filename: str):
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    dataset_id = str(uuid.uuid4())
    ext = Path(filename).suffix.lower()
    file_path = upload_dir / f"{dataset_id}{ext}"

    file_path.write_bytes(file_content)
    DatasetStore.register(file_path, filename, dataset_id)

    return dataset_id, file_path


def load_dataframe(dataset_id: str):
    meta = DatasetStore.get(dataset_id)
    path = Path(meta["path"])

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    if path.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    raise ValueError("Unsupported file type")


def dataframe_preview(df: pd.DataFrame, n: int = 10):
    preview = df.head(n).copy()
    preview = preview.where(preview.notna(), None)
    return json.loads(preview.to_json(orient="records"))