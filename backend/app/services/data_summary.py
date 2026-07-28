import pandas as pd

from app.models.schemas import ColumnSummary, DatasetSummary
from app.services.data_loader import (
    DatasetStore,
    dataframe_preview,
    load_dataframe,
)


def _safe_numeric_stats(series: pd.Series) -> dict:
    """
    Returns numeric statistics for numeric columns.
    """
    if not pd.api.types.is_numeric_dtype(series):
        return {}

    clean = series.dropna()

    if clean.empty:
        return {}

    return {
        "min": float(clean.min()),
        "max": float(clean.max()),
        "mean": float(clean.mean()),
        "median": float(clean.median()),
        "std": float(clean.std()) if len(clean) > 1 else 0.0,
    }


def summarize_column(df: pd.DataFrame, column: str) -> ColumnSummary:
    series = df[column]

    stats = _safe_numeric_stats(series)

    missing_count = int(series.isna().sum())
    total_rows = len(series)

    missing_pct = (
        round((missing_count / total_rows) * 100, 2)
        if total_rows > 0
        else 0.0
    )

    top_value = None

    try:
        mode = series.mode(dropna=True)
        if not mode.empty:
            top_value = str(mode.iloc[0])
    except Exception:
        top_value = None

    return ColumnSummary(
        name=column,
        dtype=str(series.dtype),

        missing_count=missing_count,
        missing_pct=missing_pct,

        unique_count=int(series.nunique(dropna=True)),

        mean=stats.get("mean"),
        median=stats.get("median"),
        std=stats.get("std"),
        min=stats.get("min"),
        max=stats.get("max"),

        top_value=top_value,
    )


def build_dataset_summary(dataset_id: str) -> DatasetSummary:
    """
    Builds the dataset summary in the exact format expected by the React frontend.
    """

    meta = DatasetStore.get(dataset_id)
    df = load_dataframe(dataset_id)

    duplicate_rows = int(df.duplicated().sum())
    missing_values_total = int(df.isna().sum().sum())

    column_summaries = [
        summarize_column(df, col)
        for col in df.columns
    ]

    preview_rows = dataframe_preview(df)

    return DatasetSummary(
        id=dataset_id,
        filename=meta["filename"],

        rows=len(df),
        columns=len(df.columns),

        duplicate_rows=duplicate_rows,
        missing_values_total=missing_values_total,

        column_summaries=column_summaries,

        preview_rows=preview_rows,
    )
