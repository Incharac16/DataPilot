import re

import pandas as pd

from app.models.schemas import (
    ColumnSummary,
    DataQualitySummary,
    DatasetSummary,
    QualityComponent,
    QualityRecommendation,
)
from app.services.data_loader import (
    DatasetStore,
    dataframe_preview,
    load_dataframe,
)
from app.services.data_types import semantic_type

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_PATTERN = re.compile(
    r"^(?!\d{4}-\d{2}-\d{2}$)(?=(?:\D*\d){7,15}\D*$)\+?[\d().\-\s]+$"
)


def _common_value(series: pd.Series) -> tuple[str, int | None, str, list[str], int]:
    counts = series.value_counts(dropna=True)
    if counts.empty:
        return "No available values", None, "no_values", [], 0

    duplicate_value_count = int(counts.sum() - len(counts))
    repeated = counts[counts > 1]
    if repeated.empty:
        return "No repeated value", None, "no_repeated_value", [], duplicate_value_count

    highest_count = int(repeated.max())
    ties = sorted(
        (str(value) for value in repeated[repeated == highest_count].index),
        key=str.casefold,
    )
    if len(ties) > 1:
        return (
            f"Tie: {', '.join(ties)} ({highest_count} occurrences each)",
            highest_count,
            "tie",
            ties,
            duplicate_value_count,
        )

    return ties[0], highest_count, "repeated", [], duplicate_value_count


def _format_issue_count(name: str, series: pd.Series, identifier_reason: str | None) -> int:
    if not identifier_reason:
        return 0

    values = series.dropna().astype(str)
    if "email" in identifier_reason.lower():
        valid = values.str.fullmatch(_EMAIL_PATTERN)
    elif "phone" in identifier_reason.lower():
        valid = values.str.fullmatch(_PHONE_PATTERN)
    else:
        return 0
    return int((~valid).sum())


def summarize_column(df: pd.DataFrame, column: str) -> ColumnSummary:
    series = df[column]
    column_type, identifier_reason = semantic_type(column, series)
    missing_count = int(series.isna().sum())
    total_rows = len(series)
    missing_pct = round(missing_count * 100 / total_rows, 2) if total_rows else 0.0
    top_value, top_value_count, top_value_status, ties, duplicate_value_count = (
        _common_value(series)
    )

    stats: dict[str, float] = {}
    if column_type == "numeric":
        clean = series.dropna()
        if not clean.empty:
            stats = {
                "min": float(clean.min()),
                "max": float(clean.max()),
                "mean": float(clean.mean()),
                "median": float(clean.median()),
                "std": float(clean.std()) if len(clean) > 1 else 0.0,
            }

    non_missing_count = int(series.notna().sum())
    boolean_stats: dict[str, int | float] = {}
    if column_type == "boolean":
        true_count = int(series.eq(True).sum())
        false_count = int(series.eq(False).sum())
        boolean_stats = {
            "true_count": true_count,
            "true_pct": round(true_count * 100 / non_missing_count, 2) if non_missing_count else 0.0,
            "false_count": false_count,
            "false_pct": round(false_count * 100 / non_missing_count, 2) if non_missing_count else 0.0,
        }

    datetime_stats: dict[str, str] = {}
    if column_type == "datetime":
        clean = series.dropna()
        if not clean.empty:
            datetime_stats = {
                "earliest": clean.min().isoformat(),
                "latest": clean.max().isoformat(),
            }

    return ColumnSummary(
        name=column,
        dtype=str(series.dtype),
        semantic_type=column_type,
        identifier_reason=identifier_reason,
        missing_count=missing_count,
        missing_pct=missing_pct,
        unique_count=int(series.nunique(dropna=True)),
        duplicate_value_count=duplicate_value_count,
        top_value=top_value,
        top_value_count=top_value_count,
        top_value_status=top_value_status,
        top_value_ties=ties,
        format_issue_count=_format_issue_count(column, series, identifier_reason),
        **stats,
        **boolean_stats,
        **datetime_stats,
    )


def search_and_paginate(
    df: pd.DataFrame,
    page: int,
    page_size: int,
    search: str,
    sort_by: str | None = None,
    sort_desc: bool = False,
) -> tuple[pd.DataFrame, int, int]:
    query = search.strip()
    filtered = df
    if query:
        string_df = df.astype("string")
        matches = string_df.apply(
            lambda column: column.str.contains(
                query,
                case=False,
                regex=False,
                na=False,
            )
        ).any(axis=1)
        filtered = df.loc[matches]

    matching_rows = len(filtered)
    if sort_by is not None:
        if sort_by not in df.columns:
            raise ValueError(f"Unknown sort column: {sort_by}")
        filtered = filtered.sort_values(
            by=sort_by,
            ascending=not sort_desc,
            na_position="last",
            kind="stable",
        )

    total_pages = max(1, (matching_rows + page_size - 1) // page_size)
    current_page = min(page, total_pages)
    start = (current_page - 1) * page_size

    return filtered.iloc[start : start + page_size], matching_rows, current_page


def _outlier_summary(df: pd.DataFrame, columns: list[ColumnSummary]) -> list[QualityRecommendation]:
    findings = []
    for column in columns:
        if column.semantic_type != "numeric":
            continue
        values = df[column.name].dropna()
        if len(values) < 4:
            continue
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        count = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())
        if count:
            outlier_values = values[(values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)]
            examples = ", ".join(str(value) for value in outlier_values.head(3).tolist())
            findings.append(
                QualityRecommendation(
                    issue="potential_outlier",
                    affected_count=count,
                    message=(
                        f"{column.name}: {count} values fall outside the 1.5×IQR fences. "
                        f"Examples: {examples}. Review as potential anomalies; this rule does not imply they are errors."
                    ),
                )
            )
    return findings


def _data_quality(
    df: pd.DataFrame,
    duplicate_rows: int,
    missing_values_total: int,
    columns: list[ColumnSummary],
) -> DataQualitySummary:
    cells = len(df) * len(df.columns)
    missing_score = 100.0 * (1 - missing_values_total / cells) if cells else 100.0
    duplicate_score = 100.0 * (1 - duplicate_rows / len(df)) if len(df) else 100.0

    checked_identifiers = [
        column
        for column in columns
        if column.identifier_reason
        and ("email" in column.identifier_reason.lower() or "phone" in column.identifier_reason.lower())
    ]
    checked_values = sum(
        len(df[column.name].dropna())
        for column in checked_identifiers
    )
    format_issues = sum(column.format_issue_count for column in checked_identifiers)
    consistency_score = (
        100.0 * (1 - format_issues / checked_values)
        if checked_values
        else 100.0
    )
    scores = [missing_score, duplicate_score, consistency_score]
    overall_score = sum(scores) / len(scores)

    components = [
        QualityComponent(
            name="Missing data",
            score=round(missing_score, 2),
            explanation=(
                f"100 − missing cells ({missing_values_total}) / all cells ({cells}) × 100; "
                "empty datasets score 100 because there are no cells to assess."
            ),
        ),
        QualityComponent(
            name="Duplicate rows",
            score=round(duplicate_score, 2),
            explanation=(
                f"100 − duplicate rows ({duplicate_rows}) / total rows ({len(df)}) × 100; "
                "empty datasets score 100."
            ),
        ),
        QualityComponent(
            name="Type/format consistency",
            score=round(consistency_score, 2),
            explanation=(
                f"100 − invalid values ({format_issues}) / checked email and phone values "
                f"({checked_values}) × 100; no such fields score 100."
            ),
        ),
    ]

    recommendations: list[QualityRecommendation] = []
    for column in columns:
        if column.missing_count:
            recommendations.append(
                QualityRecommendation(
                    issue="missing_values",
                    affected_count=column.missing_count,
                    message=(
                        f"{column.name}: {column.missing_count} of {len(df)} rows "
                        f"({column.missing_pct:.2f}%) are missing; review before deciding how to handle them."
                    ),
                )
            )
    if duplicate_rows:
        duplicate_examples = df.loc[df.duplicated(keep=False)].head(3).to_dict(orient="records")
        recommendations.append(
            QualityRecommendation(
                issue="duplicate_rows",
                affected_count=duplicate_rows,
                message=(
                    f"{duplicate_rows} duplicate rows were detected across all columns. "
                    f"Example repeated rows: {duplicate_examples}. No rows are removed automatically."
                ),
            )
        )
    for column in checked_identifiers:
        if column.format_issue_count:
            values = df[column.name].dropna().astype(str)
            pattern = _EMAIL_PATTERN if "email" in (column.identifier_reason or "").lower() else _PHONE_PATTERN
            examples = values[~values.str.fullmatch(pattern)].head(3).tolist()
            recommendations.append(
                QualityRecommendation(
                    issue="format_consistency",
                    affected_count=column.format_issue_count,
                    message=(
                        f"{column.name}: {column.format_issue_count} values do not match the inferred format. "
                        f"Examples: {examples}."
                    ),
                )
            )
    return DataQualitySummary(
        overall_score=round(overall_score, 2),
        components=components,
        potential_outliers=_outlier_summary(df, columns),
        recommendations=recommendations,
    )


def build_dataset_summary(
    dataset_id: str,
    page: int = 1,
    page_size: int = 10,
    search: str = "",
    sort_by: str | None = None,
    sort_desc: bool = False,
) -> DatasetSummary:
    meta = DatasetStore.get(dataset_id)
    df = load_dataframe(dataset_id)

    duplicate_rows = int(df.duplicated().sum())
    missing_values_total = int(df.isna().sum().sum())
    column_summaries = [summarize_column(df, col) for col in df.columns]

    preview_df, matching_rows, current_page = search_and_paginate(
        df,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    return DatasetSummary(
        id=dataset_id,
        filename=meta["filename"],
        rows=len(df),
        total_rows=len(df),
        matching_rows=matching_rows,
        current_page=current_page,
        page_size=page_size,
        columns=len(df.columns),
        duplicate_rows=duplicate_rows,
        missing_values_total=missing_values_total,
        data_quality=_data_quality(
            df,
            duplicate_rows,
            missing_values_total,
            column_summaries,
        ),
        column_summaries=column_summaries,
        preview_rows=dataframe_preview(preview_df),
    )
