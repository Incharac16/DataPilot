import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Literal

from app.models.schemas import ChartsResponse, DatasetSummary
from app.services.chart_generator import generate_charts
from app.services.data_loader import DatasetStore
from app.services.data_summary import build_dataset_summary
from app.services.report_service import generate_pdf_report

router = APIRouter(prefix="/api/datasets", tags=["analysis"])
logger = logging.getLogger(__name__)


def _ensure_dataset(dataset_id: str) -> None:
    try:
        DatasetStore.get(dataset_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found") from e
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Stored file for dataset '{dataset_id}' is missing.",
        ) from e


@router.get("/{dataset_id}/summary", response_model=DatasetSummary)
async def get_summary(
    dataset_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str = Query(default=""),
    sort_by: str | None = Query(default=None),
    sort_desc: bool = Query(default=False),
):
    _ensure_dataset(dataset_id)
    try:
        return build_dataset_summary(
            dataset_id,
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{dataset_id}/charts", response_model=ChartsResponse)
async def get_charts(
    dataset_id: str,
    chart_type: Literal["bar", "pie", "histogram", "line", "scatter", "box", "heatmap"] | None = None,
    x_column: str | None = None,
    y_column: str | None = None,
):
    _ensure_dataset(dataset_id)
    try:
        return generate_charts(
            dataset_id,
            chart_type=chart_type,
            x_column=x_column,
            y_column=y_column,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{dataset_id}/report.pdf", tags=["reports"])
async def get_dataset_report(dataset_id: str):
    _ensure_dataset(dataset_id)
    try:
        pdf_bytes, filename = generate_pdf_report(dataset_id)
    except Exception as e:
        logger.exception("PDF report generation failed for dataset %s", dataset_id)
        raise HTTPException(
            status_code=500,
            detail="PDF report generation failed. Please retry; see server logs for details.",
        ) from e
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
