from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    InsightsRequest,
    InsightsResponse,
)

from app.services.data_loader import DatasetStore
from app.services.insights_service import generate_grounded_insights

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

    try:
        DatasetStore.get(dataset_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found") from e
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Stored file for dataset '{dataset_id}' is missing.",
        ) from e

    question = body.question if body else None

    try:

        insights_text, verified_facts = generate_grounded_insights(
            dataset_id,
            question,
        )

        return InsightsResponse(
            id=dataset_id,
            insights=insights_text,
            generated_at=datetime.now(timezone.utc).isoformat(),
            verified_facts=verified_facts,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=503,
            detail=str(e),
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI insight generation failed.") from e
