from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    InsightsRequest,
    InsightsResponse,
)

from app.services.data_loader import DatasetStore
from app.services.insights_service import generate_insights

router = APIRouter(
    prefix="/api/datasets",
    tags=["AI Insights"],
)


@router.post(
    "/{dataset_id}/insights",
    response_model=InsightsResponse,
)
async def get_insights(
    dataset_id: str,
    body: InsightsRequest | None = None,
):

    if not DatasetStore.exists(dataset_id):
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found",
        )

    question = body.question if body else None

    try:

        insights_text = generate_insights(
            dataset_id,
            question,
        )

        return InsightsResponse(
            id=dataset_id,
            insights=insights_text,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except ValueError as e:

        raise HTTPException(
            status_code=503,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"AI Insight generation failed: {str(e)}",
        )
