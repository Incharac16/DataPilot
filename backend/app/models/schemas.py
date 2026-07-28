from typing import Any, Optional

from pydantic import BaseModel


# ----------------------------
# Upload
# ----------------------------

class UploadResponse(BaseModel):
    id: str
    filename: str
    rows: int
    columns: int
    size_bytes: int
    uploaded_at: str
    status: str = "ready"


# ----------------------------
# Dataset Summary
# ----------------------------

class ColumnSummary(BaseModel):
    name: str
    dtype: str

    missing_count: int
    missing_pct: float

    unique_count: int

    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None

    top_value: Optional[str] = None


class DatasetSummary(BaseModel):
    id: str
    filename: str

    rows: int
    columns: int

    duplicate_rows: int
    # Required by the frontend's DatasetSummary type (AnalyticsPage reads
    # this directly). Total count of missing/NaN cells across every column.
    missing_values_total: int

    column_summaries: list[ColumnSummary]

    preview_rows: list[dict[str, Any]]


# ----------------------------
# Charts
# ----------------------------

class ChartSpec(BaseModel):
    title: str
    type: str
    figure: dict[str, Any]


class ChartsResponse(BaseModel):
    id: str
    charts: list[ChartSpec]


# ----------------------------
# AI Insights
# ----------------------------

class InsightsRequest(BaseModel):
    question: Optional[str] = None


class InsightsResponse(BaseModel):
    id: str
    insights: str
    generated_at: str


# ----------------------------
# Error
# ----------------------------

class ErrorResponse(BaseModel):
    detail: str
