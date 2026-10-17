import json
import math
import re
from typing import Any

import pandas as pd

from app.services.data_types import semantic_type

MAX_FACTS_CHARACTERS = 12_000
MAX_COLUMNS_IN_CONTEXT = 15
MAX_CATEGORY_VALUES = 10


def _column_matches_question(column: str, question: str) -> bool:
    normalized_column = re.sub(r"[_\-]+", " ", column).casefold().strip()
    normalized_question = re.sub(r"[_\-]+", " ", question).casefold()
    return bool(normalized_column and normalized_column in normalized_question)


def _json_value(value: Any) -> str | int | float | bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value if isinstance(value, (str, int, float, bool)) else str(value)


def _numeric_facts(df: pd.DataFrame, column: str) -> dict[str, Any]:
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    values = values[values.map(math.isfinite)]
    return {
        "count": int(values.count()),
        "mean": float(values.mean()) if not values.empty else None,
        "median": float(values.median()) if not values.empty else None,
        "minimum": float(values.min()) if not values.empty else None,
        "maximum": float(values.max()) if not values.empty else None,
        "standard_deviation": float(values.std()) if len(values) > 1 else None,
    }


def calculate_dataset_facts(df: pd.DataFrame, question: str | None = None) -> dict[str, Any]:
    question_text = (question or "").strip()
    numeric = [
        column
        for column in df.columns
        if semantic_type(str(column), df[column])[0] == "numeric"
        and df[column].dropna().nunique() > 1
    ]
    categorical = [
        column
        for column in df.columns
        if semantic_type(str(column), df[column])[0] in {"categorical", "boolean"}
        and df[column].dropna().nunique() > 1
    ]
    dates = [
        column
        for column in df.columns
        if semantic_type(str(column), df[column])[0] == "datetime"
    ]

    matched = [
        column
        for column in df.columns
        if _column_matches_question(str(column), question_text)
    ]
    selected = matched[:MAX_COLUMNS_IN_CONTEXT]
    if not selected:
        selected = list(df.columns[:MAX_COLUMNS_IN_CONTEXT])

    facts: dict[str, Any] = {
        "overview": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "duplicate_rows": int(df.duplicated().sum()),
            "missing_cells": int(df.isna().sum().sum()),
            "missing_by_column": {},
        },
        "columns": {},
    }
    missing_counts = df.isna().sum().sort_values(ascending=False)
    facts["overview"]["most_missing_column"] = (
        {
            "name": str(missing_counts.index[0])[:200],
            "count": int(missing_counts.iloc[0]),
        }
        if not missing_counts.empty
        else None
    )
    facts["overview"]["missing_by_column"] = {
        str(column)[:100]: int(count)
        for column, count in missing_counts.head(30).items()
        if count > 0
    }
    if len(missing_counts) > 30:
        facts["overview"]["missing_columns_omitted"] = len(missing_counts) - 30

    for column in selected:
        column_type = semantic_type(str(column), df[column])[0]
        profile: dict[str, Any] = {
            "semantic_type": column_type,
            "missing_count": int(df[column].isna().sum()),
            "unique_count": int(df[column].nunique(dropna=True)),
        }
        if column_type == "numeric":
            profile["statistics"] = _numeric_facts(df, column)
        elif column_type in {"categorical", "boolean"}:
            counts = df[column].value_counts(dropna=True).head(MAX_CATEGORY_VALUES)
            denominator = int(df[column].notna().sum())
            profile["category_counts"] = [
                {
                    "value": str(_json_value(value)),
                    "count": int(count),
                    "percentage_of_non_missing": (
                        round(float(count) * 100 / denominator, 2)
                        if denominator
                        else None
                    ),
                }
                for value, count in counts.items()
            ]
        elif column_type == "datetime":
            dates_series = pd.to_datetime(df[column], errors="coerce").dropna()
            profile["earliest"] = _json_value(dates_series.min()) if not dates_series.empty else None
            profile["latest"] = _json_value(dates_series.max()) if not dates_series.empty else None
        facts["columns"][str(column)] = profile

    if re.search(r"\b(by|group(?:ed)?|highest|lowest|most|least)\b", question_text, re.I):
        relevant_categories = [
            column
            for column in categorical
            if _column_matches_question(str(column), question_text)
        ]
        relevant_numeric = [
            column
            for column in numeric
            if _column_matches_question(str(column), question_text)
        ]
        if not relevant_categories:
            relevant_categories = categorical[:2]
        if not relevant_numeric:
            relevant_numeric = numeric[:2]

        grouped = []
        for category in relevant_categories[:2]:
            for measure in relevant_numeric[:2]:
                valid = df[[category, measure]].dropna()
                valid = valid[
                    pd.to_numeric(valid[measure], errors="coerce").map(math.isfinite)
                ]
                if valid.empty:
                    continue
                valid[measure] = pd.to_numeric(valid[measure], errors="coerce")
                totals = (
                    valid.groupby(category, dropna=True)[measure]
                    .sum()
                    .sort_values(ascending=False)
                    .head(MAX_CATEGORY_VALUES)
                )
                grouped.append(
                    {
                        "category_column": str(category),
                        "measure_column": str(measure),
                        "aggregation": "sum",
                        "groups": [
                            {
                                "category": str(_json_value(value))[:200],
                                "total": _json_value(total),
                            }
                            for value, total in totals.items()
                        ],
                    }
                )
        facts["grouped_aggregates"] = grouped

    if re.search(r"\b(correlation|correlat|relationship)\b", question_text, re.I):
        selected_numeric = numeric[:MAX_COLUMNS_IN_CONTEXT]
        if len(selected_numeric) >= 2:
            correlations = df[selected_numeric].corr().round(4)
            facts["correlations"] = {
                str(row): {
                    str(column): _json_value(value)
                    for column, value in values.items()
                }
                for row, values in correlations.iterrows()
            }

    return facts


def factual_context(facts: dict[str, Any]) -> str:
    serialized = json.dumps(facts, ensure_ascii=False, allow_nan=False, indent=2)
    if len(serialized) <= MAX_FACTS_CHARACTERS:
        return serialized
    trimmed = dict(facts)
    trimmed["overview"] = dict(facts["overview"])
    trimmed["overview"]["missing_by_column"] = dict(
        list(facts["overview"]["missing_by_column"].items())[:10]
    )
    trimmed.pop("correlations", None)
    trimmed.pop("grouped_aggregates", None)
    trimmed["columns"] = dict(facts["columns"])
    while trimmed["columns"]:
        serialized = json.dumps(trimmed, ensure_ascii=False, allow_nan=False, indent=2)
        if len(serialized) <= MAX_FACTS_CHARACTERS:
            return serialized
        trimmed["columns"].pop(next(reversed(trimmed["columns"])))
    trimmed["note"] = "Column detail omitted to keep context bounded."
    serialized = json.dumps(trimmed, ensure_ascii=False, allow_nan=False, indent=2)
    return serialized


def verified_facts_for_answer(facts: dict[str, Any]) -> list[str]:
    overview = facts["overview"]
    output = [
        f"Computed dataset size: {overview['rows']} rows and {overview['columns']} columns.",
        f"Computed missing cells: {overview['missing_cells']}; duplicate rows: {overview['duplicate_rows']}.",
    ]
    for aggregate in facts.get("grouped_aggregates", []):
        groups = aggregate["groups"]
        if groups:
            highest = groups[0]
            output.append(
                f"Computed {aggregate['aggregation']} of {aggregate['measure_column']} by "
                f"{aggregate['category_column']}: highest is {highest['category']} "
                f"({highest['total']:g})."
            )
    for name, profile in facts["columns"].items():
        statistics = profile.get("statistics")
        if statistics:
            output.append(
                f"Computed {name} mean: "
                f"{statistics['mean']:g}."
                if statistics["mean"] is not None
                else f"No numeric values were available for {name}."
            )
        if profile.get("category_counts"):
            output.append(
                f"Computed category shares for {name}: "
                + "; ".join(
                    f"{item['value']} = {item['percentage_of_non_missing']}%"
                    for item in profile["category_counts"]
                )
                + "."
            )
    highest_missing = overview.get("most_missing_column")
    if highest_missing and highest_missing["count"] > 0:
        output.append(
            f"Computed missing-value maximum: {highest_missing['name']} has {highest_missing['count']}."
        )
    return list(dict.fromkeys(output))
