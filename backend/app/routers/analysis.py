from fastapi import APIRouter, HTTPException

from app.models.schemas import ChartsResponse, DatasetSummary
from app.services.chart_generator import generate_charts
from app.services.data_loader import DatasetStore
from app.services.data_summary import build_dataset_summary

router = APIRouter(prefix="/api/datasets", tags=["analysis"])


def _ensure_dataset(dataset_id: str) -> None:
    if not DatasetStore.exists(dataset_id):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")


@router.get("/{dataset_id}/summary", response_model=DatasetSummary)
async def get_summary(dataset_id: str):
    _ensure_dataset(dataset_id)
    try:
        return build_dataset_summary(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{dataset_id}/charts", response_model=ChartsResponse)
async def get_charts(dataset_id: str):
    _ensure_dataset(dataset_id)
    try:
        return generate_charts(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
