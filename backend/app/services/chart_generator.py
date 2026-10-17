import json
from itertools import combinations, product
from typing import Literal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.models.schemas import ChartSpec, ChartsResponse, UnsupportedChart
from app.services.data_loader import load_dataframe
from app.services.data_types import semantic_type

MAX_CHARTS = 6
MAX_CATEGORIES = 20
MAX_HEATMAP_COLUMNS = 15
MAX_SCATTER_POINTS = 2_000
MAX_BOX_POINTS = 5_000
ChartType = Literal["bar", "pie", "histogram", "line", "scatter", "box", "heatmap"]


class UnsuitableChartError(ValueError):
    pass


def _fig_to_dict(fig: go.Figure) -> dict:
    return json.loads(fig.to_json())


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [
        column
        for column in df.columns
        if semantic_type(column, df[column])[0] == "numeric"
        and df[column].dropna().nunique() > 1
    ]


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    columns = [
        column
        for column in df.columns
        if semantic_type(column, df[column])[0] in {"categorical", "boolean"}
        and df[column].dropna().nunique() > 1
    ]
    return sorted(
        columns,
        key=lambda column: not any(
            term in column.casefold() for term in ("category", "type", "class")
        ),
    )


def _datetime_columns(df: pd.DataFrame) -> list[str]:
    return [
        column
        for column in df.columns
        if semantic_type(column, df[column])[0] == "datetime"
        and df[column].dropna().nunique() > 1
    ]


def _column_options(df: pd.DataFrame) -> dict[str, list[str]]:
    return {
        "numeric": _numeric_columns(df),
        "categorical": _categorical_columns(df),
        "datetime": _datetime_columns(df),
    }


def chart_column_options(df: pd.DataFrame) -> dict[str, list[str]]:
    return _column_options(df)


def _chart_spec(title: str, chart_type: str, fig: go.Figure, x: str | None, y: str | None) -> ChartSpec:
    return ChartSpec(
        title=title,
        type=chart_type,
        figure=_fig_to_dict(fig),
        x_column=x,
        y_column=y,
    )


def _build_chart(
    df: pd.DataFrame,
    chart_type: ChartType,
    x_column: str | None,
    y_column: str | None,
) -> ChartSpec:
    numeric = _numeric_columns(df)
    categorical = _categorical_columns(df)
    dates = _datetime_columns(df)

    if chart_type == "heatmap":
        if len(numeric) < 2:
            raise UnsuitableChartError("A correlation heatmap requires at least two numeric measurement columns.")
        corr = df[numeric[:MAX_HEATMAP_COLUMNS]].corr()
        fig = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            labels={"x": "Numeric column", "y": "Numeric column", "color": "Correlation"},
        )
        title = "Correlation Between Numeric Variables"
        fig.update_layout(title=title)
        return _chart_spec(title, chart_type, fig, None, None)

    if chart_type == "box" and x_column is None:
        if y_column not in numeric:
            raise UnsuitableChartError("Choose a numeric measurement column for the box plot.")
        values = df[y_column].dropna()
        if values.empty:
            raise UnsuitableChartError("A box plot needs at least one non-missing numeric value.")
        fig = px.box(df, y=y_column, title=f"Distribution of {y_column}")
        fig.update_layout(xaxis_title="", yaxis_title=y_column)
        return _chart_spec(f"Distribution of {y_column}", chart_type, fig, None, y_column)

    allowed_x = {
        "bar": categorical,
        "pie": categorical,
        "histogram": numeric,
        "line": dates,
        "scatter": numeric,
        "box": categorical,
    }[chart_type]
    if x_column not in allowed_x:
        raise UnsuitableChartError(f"Choose a valid {chart_type} x-axis column from: {', '.join(allowed_x) or 'none'}.")

    if chart_type in {"bar", "line", "scatter", "box"} and y_column not in numeric:
        raise UnsuitableChartError(f"Choose a numeric measurement column for the {chart_type} y-axis.")
    if chart_type == "pie" and y_column is not None and y_column not in numeric:
        raise UnsuitableChartError("For a pie chart, choose a numeric measurement for y or leave it blank to count categories.")

    if chart_type == "histogram":
        values = df[x_column].dropna()
        if values.empty:
            raise UnsuitableChartError("The selected numeric column has no non-missing values to plot.")
        counts, edges = pd.cut(
            values,
            bins=min(30, max(1, int(values.nunique()))),
            retbins=True,
            duplicates="drop",
        )
        histogram = counts.value_counts(sort=False)
        centers = [
            (edges[index] + edges[index + 1]) / 2
            for index in range(len(edges) - 1)
        ]
        fig = go.Figure(
            go.Bar(x=centers, y=histogram.to_list(), name="Count")
        )
        fig.update_layout(title=f"Distribution of {x_column}")
        fig.update_layout(xaxis_title=x_column, yaxis_title="Count")
        return _chart_spec(f"Distribution of {x_column}", chart_type, fig, x_column, None)

    if chart_type == "pie":
        valid = df[[x_column] + ([y_column] if y_column else [])].dropna(subset=[x_column])
        if y_column:
            valid = valid.dropna(subset=[y_column]).groupby(x_column, as_index=False)[y_column].sum()
            valid = valid.nlargest(MAX_CATEGORIES, y_column)
            values = y_column
            value_label = f"Total {y_column}"
        else:
            valid = valid[x_column].value_counts().head(MAX_CATEGORIES).rename_axis(x_column).reset_index(name="Count")
            values = "Count"
            value_label = "Count"
        if valid[x_column].nunique() < 2:
            raise UnsuitableChartError("A pie chart needs at least two non-missing categories.")
        fig = px.pie(valid, names=x_column, values=values, hole=0.35, title=f"{value_label} by {x_column}")
        fig.update_traces(hovertemplate="%{label}<br>%{value}<br>%{percent}<extra></extra>")
        return _chart_spec(f"{value_label} by {x_column}", chart_type, fig, x_column, y_column)

    valid = df[[x_column, y_column]].dropna()
    if chart_type == "bar":
        valid = valid.groupby(x_column, as_index=False)[y_column].sum().nlargest(MAX_CATEGORIES, y_column)
        if len(valid) < 2:
            raise UnsuitableChartError("A category comparison needs at least two non-missing categories.")
        fig = px.bar(valid, x=x_column, y=y_column, title=f"{y_column} by {x_column}")
        fig.update_layout(xaxis_title=x_column, yaxis_title=f"Total {y_column}")
        return _chart_spec(f"{y_column} by {x_column}", chart_type, fig, x_column, y_column)

    if chart_type == "line":
        valid = df[[x_column, y_column]].dropna().groupby(x_column, as_index=False)[y_column].sum()
        valid = valid.sort_values(x_column)
        if len(valid) < 2:
            raise UnsuitableChartError("A line chart needs at least two valid time points.")
        if len(valid) > MAX_SCATTER_POINTS:
            sample_indices = [
                index * (len(valid) - 1) // (MAX_SCATTER_POINTS - 1)
                for index in range(MAX_SCATTER_POINTS)
            ]
            valid = valid.iloc[sample_indices]
        title = f"{y_column} over {x_column}"
        fig = px.line(valid, x=x_column, y=y_column, markers=True, title=title)
        fig.update_layout(xaxis_title=x_column, yaxis_title=y_column)
        return _chart_spec(title, chart_type, fig, x_column, y_column)

    if chart_type == "scatter":
        if len(valid) < 2 or valid[x_column].nunique() < 2 or valid[y_column].nunique() < 2:
            raise UnsuitableChartError("A scatter plot needs at least two valid rows and variation in both columns.")
        if len(valid) > MAX_SCATTER_POINTS:
            valid = valid.sample(MAX_SCATTER_POINTS, random_state=0)
        fig = px.scatter(valid, x=x_column, y=y_column, opacity=0.7, title=f"{y_column} vs {x_column}")
        fig.update_layout(xaxis_title=x_column, yaxis_title=y_column)
        return _chart_spec(f"{y_column} vs {x_column}", chart_type, fig, x_column, y_column)

    if chart_type == "box":
        if valid[x_column].nunique() < 2:
            raise UnsuitableChartError("A box plot needs at least two non-missing categories.")
        counts = valid[x_column].value_counts().head(MAX_CATEGORIES)
        valid = valid[valid[x_column].isin(counts.index)]
        if len(valid) > MAX_BOX_POINTS:
            valid = valid.sample(MAX_BOX_POINTS, random_state=0)
        fig = px.box(valid, x=x_column, y=y_column, title=f"{y_column} by {x_column}")
        fig.update_layout(xaxis_title=x_column, yaxis_title=y_column)
        return _chart_spec(f"{y_column} by {x_column}", chart_type, fig, x_column, y_column)

    raise UnsuitableChartError(f"Unsupported chart type: {chart_type}")


def _auto_charts(
    df: pd.DataFrame,
) -> tuple[list[ChartSpec], list[str], list[UnsupportedChart]]:
    numeric = _numeric_columns(df)
    categorical = _categorical_columns(df)
    dates = _datetime_columns(df)
    charts: list[ChartSpec] = []
    diagnostics: list[str] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    failures: dict[str, list[str]] = {}

    def add(chart_type: ChartType, x: str | None = None, y: str | None = None) -> bool:
        signature = (chart_type, x, y)
        if signature in seen or len(charts) >= MAX_CHARTS:
            return False
        seen.add(signature)
        try:
            charts.append(_build_chart(df, chart_type, x, y))
            return True
        except UnsuitableChartError as error:
            failures.setdefault(chart_type, []).append(str(error))
            return False

    for column in numeric:
        if add("histogram", column):
            break

    for category, measure in product(categorical, numeric):
        if add("bar", category, measure):
            break
        if len(charts) >= MAX_CHARTS:
            break

    for date_column, measure in product(dates, numeric):
        if add("line", date_column, measure):
            break
        if len(charts) >= MAX_CHARTS:
            break

    for x_column, y_column in combinations(numeric, 2):
        if add("scatter", x_column, y_column):
            break
        if len(charts) >= MAX_CHARTS:
            break

    box_measures = numeric[1:2] or numeric[:1]
    for category, measure in product(categorical, box_measures):
        if add("box", category, measure):
            break
        if len(charts) >= MAX_CHARTS:
            break
    if not any(chart.type == "box" for chart in charts):
        for measure in numeric:
            if add("box", None, measure):
                break
            if len(charts) >= MAX_CHARTS:
                break

    if len(numeric) >= 2:
        add("heatmap")

    if len(charts) < MAX_CHARTS and not any(chart.type == "pie" for chart in charts):
        for category in categorical:
            if add("pie", category):
                break

    requirements = (
        (
            "bar",
            "Bar chart",
            bool(categorical and numeric),
            "Cannot generate this chart because "
            + " and ".join(
                label
                for available, label in (
                    (categorical, "no suitable categorical columns were detected"),
                    (numeric, "no suitable numerical measurement columns were detected"),
                )
                if not available
            )
            + ".",
        ),
        (
            "pie",
            "Pie / donut chart",
            bool(categorical),
            "Cannot generate this chart because no suitable categorical columns were detected.",
        ),
        (
            "histogram",
            "Histogram",
            bool(numeric),
            "Cannot generate this chart because the dataset has no suitable numerical columns.",
        ),
        (
            "line",
            "Line chart",
            bool(dates and numeric),
            "Cannot generate this chart because "
            + " and ".join(
                label
                for available, label in (
                    (dates, "no valid date/time columns were detected"),
                    (numeric, "no suitable numerical measurement columns were detected"),
                )
                if not available
            )
            + ".",
        ),
        (
            "scatter",
            "Scatter plot",
            len(numeric) >= 2,
            f"Cannot generate this chart because fewer than two suitable numerical measurement columns are available (detected {len(numeric)}).",
        ),
        (
            "box",
            "Box plot",
            bool(numeric),
            "Cannot generate this chart because the dataset has no suitable numerical measurement columns.",
        ),
        (
            "heatmap",
            "Correlation heatmap",
            len(numeric) >= 2,
            f"Cannot generate this chart because at least two suitable numerical measurement columns are required (detected {len(numeric)}).",
        ),
    )
    generated_types = {chart.type for chart in charts}
    unsupported = [
        UnsupportedChart(
            type=chart_label,
            reason=failures[chart_type][0] if chart_type in failures else unavailable_reason,
        )
        for chart_type, chart_label, columns_available, unavailable_reason in requirements
        if chart_type not in generated_types
        and (not columns_available or chart_type in failures)
    ]

    if len(charts) >= MAX_CHARTS and categorical:
        diagnostics.append(
            f"The default chart limit of {MAX_CHARTS} was reached; additional suitable charts are not shown."
        )
    if len(numeric) > MAX_HEATMAP_COLUMNS and any(
        chart.type == "heatmap" for chart in charts
    ):
        diagnostics.append(
            f"The correlation heatmap is limited to the first {MAX_HEATMAP_COLUMNS} eligible numerical columns."
        )

    if not charts:
        detected_types = ", ".join(
            f"{column}: {semantic_type(column, df[column])[0]} ({df[column].dtype})"
            for column in df.columns
        )
        diagnostics.append(
            "This dataset has no valid column combination for automatic charts. "
            f"Eligible numeric measurement columns: {numeric}; "
            f"categorical/boolean columns: {categorical}; datetime columns: {dates}. "
            f"Detected columns: {detected_types or 'none'}."
        )
    return charts, list(dict.fromkeys(diagnostics)), unsupported


def generate_charts(
    dataset_id: str,
    chart_type: ChartType | None = None,
    x_column: str | None = None,
    y_column: str | None = None,
) -> ChartsResponse:
    df = load_dataframe(dataset_id)
    options = _column_options(df)

    if chart_type:
        charts = [_build_chart(df, chart_type, x_column, y_column)]
        diagnostics = []
        unsupported = []
    else:
        charts, diagnostics, unsupported = _auto_charts(df)

    return ChartsResponse(
        id=dataset_id,
        charts=charts,
        diagnostics=diagnostics,
        unsupported_charts=unsupported,
        available_columns=options,
    )
