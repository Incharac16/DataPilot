from typing import Any, Optional

from pydantic import BaseModel, Field


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


class DatasetRecord(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    file_format: str
    rows: int
    columns: int
    size_bytes: int
    status: str


# ----------------------------
# Dataset Summary
# ----------------------------

class ColumnSummary(BaseModel):
    name: str
    dtype: str
    semantic_type: str
    identifier_reason: Optional[str] = None

    missing_count: int
    missing_pct: float

    unique_count: int
    duplicate_value_count: int
    top_value: Optional[str] = None
    top_value_count: Optional[int] = None
    top_value_status: str
    top_value_ties: list[str] = Field(default_factory=list)

    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    true_count: Optional[int] = None
    true_pct: Optional[float] = None
    false_count: Optional[int] = None
    false_pct: Optional[float] = None
    earliest: Optional[str] = None
    latest: Optional[str] = None
    format_issue_count: int = 0


class QualityComponent(BaseModel):
    name: str
    score: float
    explanation: str


class QualityRecommendation(BaseModel):
    issue: str
    affected_count: int
    message: str


class DataQualitySummary(BaseModel):
    overall_score: float
    components: list[QualityComponent]
    potential_outliers: list[QualityRecommendation]
    recommendations: list[QualityRecommendation]


class DatasetSummary(BaseModel):
    id: str
    filename: str

    rows: int
    total_rows: int
    matching_rows: int
    current_page: int
    page_size: int
    columns: int

    duplicate_rows: int
    # Required by the frontend's DatasetSummary type (AnalyticsPage reads
    # this directly). Total count of missing/NaN cells across every column.
    missing_values_total: int
    data_quality: DataQualitySummary

    column_summaries: list[ColumnSummary]

    preview_rows: list[dict[str, Any]]


# ----------------------------
# Charts
# ----------------------------

class ChartSpec(BaseModel):
    title: str
    type: str
    figure: dict[str, Any]
    x_column: Optional[str] = None
    y_column: Optional[str] = None


class UnsupportedChart(BaseModel):
    type: str
    reason: str


class ChartsResponse(BaseModel):
    id: str
    charts: list[ChartSpec]
    diagnostics: list[str] = Field(default_factory=list)
    unsupported_charts: list[UnsupportedChart] = Field(default_factory=list)
    available_columns: dict[str, list[str]] = Field(default_factory=dict)


# ----------------------------
# AI Insights
# ----------------------------

class InsightsRequest(BaseModel):
    question: Optional[str] = Field(default=None, max_length=2000)


class InsightsResponse(BaseModel):
    id: str
    insights: str
    generated_at: str
    verified_facts: list[str] = Field(default_factory=list)


# ----------------------------
# Error
# ----------------------------

class ErrorResponse(BaseModel):
    detail: str
