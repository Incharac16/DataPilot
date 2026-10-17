import base64
import io
import logging
import math
import re
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String, Wedge
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.schemas import ChartSpec
from app.services.chart_generator import generate_charts
from app.services.data_loader import DatasetStore, load_dataframe
from app.services.data_summary import build_dataset_summary

logger = logging.getLogger(__name__)

INK = colors.HexColor("#20243A")
MUTED = colors.HexColor("#5D6478")
ACCENT = colors.HexColor("#5146D8")
PALE = colors.HexColor("#F0F0FC")
GRID = colors.HexColor("#D9DCE7")
PALETTE = [
    colors.HexColor("#5146D8"),
    colors.HexColor("#18A889"),
    colors.HexColor("#F19A38"),
    colors.HexColor("#D85C75"),
    colors.HexColor("#3988C8"),
    colors.HexColor("#8061B3"),
]
PAGE_WIDTH, PAGE_HEIGHT = letter
CONTENT_WIDTH = PAGE_WIDTH - 1.3 * inch


def _safe_filename(filename: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", filename.rsplit(".", 1)[0]).strip("-_")
    return stem[:80] or "dataset-report"


def _chart_label(chart_type: str) -> str:
    return {
        "bar": "Bar Chart",
        "pie": "Pie / Donut Chart",
        "histogram": "Histogram",
        "line": "Line Chart",
        "scatter": "Scatter Plot",
        "box": "Box Plot",
        "heatmap": "Correlation Heatmap",
    }.get(chart_type, chart_type.replace("_", " ").title())


def _number(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _series(value: object) -> list:
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, dict) and "bdata" in value and "dtype" in value:
        values = np.frombuffer(
            base64.b64decode(value["bdata"]),
            dtype=np.dtype(value["dtype"]),
        )
        shape = value.get("shape")
        if shape:
            dimensions = tuple(int(size.strip()) for size in shape.split(","))
            values = values.reshape(dimensions)
        return values.tolist()
    return []


def _text(value: object, limit: int = 20) -> str:
    text = str(value)
    return text if len(text) <= limit else f"{text[:limit - 1]}…"


def _plot_area(drawing: Drawing) -> tuple[float, float, float, float]:
    return 0.62 * inch, 0.62 * inch, drawing.width - 0.9 * inch, drawing.height - 1.05 * inch


def _add_axes(
    drawing: Drawing,
    x_label: str = "",
    y_label: str = "",
    y_min: float = 0,
    y_max: float = 1,
) -> tuple[float, float, float, float]:
    left, bottom, right, top = _plot_area(drawing)
    drawing.add(Line(left, bottom, right, bottom, strokeColor=MUTED, strokeWidth=0.7))
    drawing.add(Line(left, bottom, left, top, strokeColor=MUTED, strokeWidth=0.7))
    for tick in range(1, 5):
        y = bottom + (top - bottom) * tick / 5
        drawing.add(Line(left, y, right, y, strokeColor=GRID, strokeWidth=0.4))
        value = y_min + (y_max - y_min) * tick / 5
        drawing.add(
            String(
                left - 5,
                y - 2,
                f"{value:,.3g}",
                textAnchor="end",
                fontName="Helvetica",
                fontSize=6.5,
                fillColor=MUTED,
            )
        )
    if x_label:
        drawing.add(
            String(
                (left + right) / 2,
                0.12 * inch,
                _text(x_label, 64),
                textAnchor="middle",
                fontName="Helvetica",
                fontSize=8,
                fillColor=MUTED,
            )
        )
    if y_label:
        drawing.add(
            String(
                0.08 * inch,
                (bottom + top) / 2,
                _text(y_label, 34),
                fontName="Helvetica",
                fontSize=8,
                fillColor=MUTED,
                angle=90,
            )
        )
    return left, bottom, right, top


def _add_x_labels(drawing: Drawing, labels: list, left: float, right: float, y: float, rotate: bool = False) -> None:
    if not labels:
        return
    step = max(1, math.ceil(len(labels) / 10))
    for index, value in enumerate(labels):
        if index % step:
            continue
        x = left + (right - left) * (index + 0.5) / len(labels)
        label = String(
            x,
            y - (0.04 * inch if not rotate else 0.12 * inch),
            _text(value, 10 if rotate else 14),
            textAnchor="middle",
            fontName="Helvetica",
            fontSize=6.5,
            fillColor=MUTED,
        )
        drawing.add(label)


def _draw_categorical_bars(drawing: Drawing, trace: dict, color=PALETTE[0]) -> None:
    labels = _series(trace.get("x"))
    values = [_number(value) for value in _series(trace.get("y"))]
    pairs = [(str(label), value) for label, value in zip(labels, values) if value is not None]
    if not pairs:
        return
    labels, values = zip(*pairs)
    y_min = min(0, min(values))
    y_max = max(0, max(values))
    left, bottom, right, top = _add_axes(drawing, "Category", "Value", y_min, y_max or 1)
    baseline = bottom + (0 - y_min) / ((y_max or 1) - y_min or 1) * (top - bottom)
    slot = (right - left) / len(values)
    bar_width = slot * 0.72
    for index, value in enumerate(values):
        value_y = bottom + (value - y_min) / ((y_max or 1) - y_min or 1) * (top - bottom)
        x = left + index * slot + (slot - bar_width) / 2
        drawing.add(Rect(x, min(baseline, value_y), bar_width, max(0.6, abs(value_y - baseline)), fillColor=color, strokeColor=None))
    _add_x_labels(drawing, list(labels), left, right, bottom, rotate=True)


def _draw_histogram(drawing: Drawing, trace: dict) -> None:
    values = [_number(value) for value in _series(trace.get("y"))]
    labels = _series(trace.get("x"))
    pairs = [(label, value) for label, value in zip(labels, values) if value is not None]
    if not pairs:
        return
    labels, values = zip(*pairs)
    high = max(values) or 1
    left, bottom, right, top = _add_axes(drawing, "Value range", "Count", 0, high)
    slot = (right - left) / len(values)
    for index, value in enumerate(values):
        height = max(0, (top - bottom) * value / high)
        drawing.add(
            Rect(
                left + index * slot + 0.5,
                bottom,
                max(1, slot - 1),
                height,
                fillColor=PALETTE[1],
                strokeColor=colors.white,
                strokeWidth=0.25,
            )
        )
    _add_x_labels(drawing, list(labels), left, right, bottom, rotate=True)


def _draw_xy(drawing: Drawing, trace: dict, chart_type: str, x_label: str, y_label: str) -> None:
    raw_x, raw_y = _series(trace.get("x")), _series(trace.get("y"))
    pairs = [
        (index, _number(x), _number(y))
        for index, (x, y) in enumerate(zip(raw_x, raw_y))
        if _number(y) is not None
    ]
    if not pairs:
        return
    numeric_x = [_number(x) for _, x, _ in pairs]
    uses_numeric_x = all(value is not None for value in numeric_x)
    xs = [value if value is not None else index for index, value, _ in pairs]
    ys = [value for _, _, value in pairs]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span, y_span = x_max - x_min or 1, y_max - y_min or 1
    left, bottom, right, top = _add_axes(drawing, x_label, y_label, y_min, y_max or 1)
    points = [
        (left + (x - x_min) / x_span * (right - left), bottom + (y - y_min) / y_span * (top - bottom))
        for x, y in zip(xs, ys)
    ]
    if chart_type == "line":
        for first, second in zip(points, points[1:]):
            drawing.add(Line(*first, *second, strokeColor=PALETTE[0], strokeWidth=1.5))
    for x, y in points:
        drawing.add(Circle(x, y, 2.4, fillColor=PALETTE[0], strokeColor=colors.white, strokeWidth=0.4))
    if not uses_numeric_x:
        _add_x_labels(drawing, raw_x, left, right, bottom, rotate=True)


def _draw_box(drawing: Drawing, trace: dict) -> None:
    raw_y = _series(trace.get("y"))
    raw_x = _series(trace.get("x"))
    if not raw_y or len(raw_y) != len(raw_x):
        return
    groups: dict[str, list[float]] = {}
    for label, value in zip(raw_x, raw_y):
        number = _number(value)
        if number is not None:
            groups.setdefault(str(label), []).append(number)
    groups = dict(list(groups.items())[:12])
    if not groups:
        return
    all_values = [value for values in groups.values() for value in values]
    low, high = min(all_values), max(all_values)
    span = high - low or 1
    left, bottom, right, top = _add_axes(drawing, "Category", _text(trace.get("name", "Value"), 32), low, high or 1)
    slot = (right - left) / len(groups)
    for index, (label, values) in enumerate(groups.items()):
        ordered = sorted(values)
        q1, med, q3 = (float(pd.Series(ordered).quantile(fraction)) for fraction in (0.25, 0.5, 0.75))
        iqr = q3 - q1
        whisker_low = min(value for value in ordered if value >= q1 - 1.5 * iqr)
        whisker_high = max(value for value in ordered if value <= q3 + 1.5 * iqr)
        x = left + slot * (index + 0.5)
        to_y = lambda value: bottom + (value - low) / span * (top - bottom)
        box_width = min(slot * 0.55, 0.45 * inch)
        drawing.add(Line(x, to_y(whisker_low), x, to_y(whisker_high), strokeColor=ACCENT))
        drawing.add(Line(x - box_width / 3, to_y(whisker_low), x + box_width / 3, to_y(whisker_low), strokeColor=ACCENT))
        drawing.add(Line(x - box_width / 3, to_y(whisker_high), x + box_width / 3, to_y(whisker_high), strokeColor=ACCENT))
        drawing.add(Rect(x - box_width / 2, to_y(q1), box_width, max(1, to_y(q3) - to_y(q1)), fillColor=PALE, strokeColor=ACCENT))
        drawing.add(Line(x - box_width / 2, to_y(med), x + box_width / 2, to_y(med), strokeColor=PALETTE[3], strokeWidth=1.4))
    _add_x_labels(drawing, list(groups), left, right, bottom, rotate=True)


def _draw_pie(drawing: Drawing, trace: dict) -> None:
    labels, raw_values = _series(trace.get("labels")), _series(trace.get("values"))
    pairs = [(str(label), value) for label, value in zip(labels, raw_values) if _number(value) is not None and _number(value) >= 0]
    total = sum(_number(value) or 0 for _, value in pairs)
    if not pairs or total <= 0:
        return
    center_x, center_y = drawing.width * 0.38, drawing.height * 0.51
    radius = min(drawing.height * 0.34, drawing.width * 0.25)
    angle = 90
    legend_step = min(0.22 * inch, (drawing.height - 0.55 * inch) / len(pairs))
    for index, (label, value) in enumerate(pairs):
        sweep = (_number(value) or 0) / total * 360
        drawing.add(Wedge(center_x, center_y, radius, angle - sweep, angle, fillColor=PALETTE[index % len(PALETTE)], strokeColor=colors.white, strokeWidth=0.8))
        angle -= sweep
        legend_y = drawing.height - 0.35 * inch - index * legend_step
        drawing.add(Rect(drawing.width * 0.69, legend_y - 2, 8, 8, fillColor=PALETTE[index % len(PALETTE)], strokeColor=None))
        drawing.add(String(drawing.width * 0.69 + 13, legend_y, f"{_text(label, 20)} ({_number(value):,.3g})", fontName="Helvetica", fontSize=8, fillColor=INK))


def _draw_heatmap(drawing: Drawing, trace: dict) -> None:
    x_labels, y_labels, matrix = _series(trace.get("x")), _series(trace.get("y")), _series(trace.get("z"))
    if not matrix or not x_labels or not y_labels:
        return
    rows = [[_number(value) for value in _series(row)] for row in matrix]
    row_count = min(len(y_labels), len(rows))
    col_count = min(len(x_labels), *(len(row) for row in rows[:row_count]))
    if not row_count or not col_count:
        return
    left, bottom, right, top = _plot_area(drawing)
    cell_w, cell_h = (right - left) / col_count, (top - bottom) / row_count
    for row in range(row_count):
        for col in range(col_count):
            value = rows[row][col]
            if value is None:
                fill = GRID
            else:
                strength = min(1, abs(value))
                base = colors.HexColor("#C84F66") if value >= 0 else colors.HexColor("#3D72C9")
                fill = colors.Color(
                    1 + (base.red - 1) * strength,
                    1 + (base.green - 1) * strength,
                    1 + (base.blue - 1) * strength,
                )
            drawing.add(Rect(left + col * cell_w, top - (row + 1) * cell_h, cell_w, cell_h, fillColor=fill, strokeColor=colors.white, strokeWidth=0.5))
            if cell_w > 23 and cell_h > 13 and rows[row][col] is not None:
                drawing.add(String(left + (col + 0.5) * cell_w, top - (row + 0.62) * cell_h, f"{rows[row][col]:.2f}", textAnchor="middle", fontName="Helvetica", fontSize=6.5, fillColor=INK))
    for index, label in enumerate(x_labels[:col_count]):
        drawing.add(String(left + (index + 0.5) * cell_w, bottom - 0.12 * inch, _text(label, 14), textAnchor="middle", fontName="Helvetica", fontSize=6.5, fillColor=MUTED))
    for index, label in enumerate(y_labels[:row_count]):
        drawing.add(String(left - 0.07 * inch, top - (index + 0.58) * cell_h, _text(label, 14), textAnchor="end", fontName="Helvetica", fontSize=6.5, fillColor=MUTED))


def _chart_drawing(chart: ChartSpec) -> Drawing:
    drawing = Drawing(CONTENT_WIDTH, 4.8 * inch)
    trace_list = chart.figure.get("data", [])
    if not trace_list:
        raise ValueError(f"Chart {chart.title!r} has no plotted data.")
    trace = trace_list[0]
    kind = chart.type
    if kind == "pie":
        _draw_pie(drawing, trace)
    elif kind == "heatmap":
        _draw_heatmap(drawing, trace)
    elif kind == "histogram":
        _draw_histogram(drawing, trace)
    elif kind == "box":
        _draw_box(drawing, trace)
    elif kind in {"line", "scatter"}:
        _draw_xy(drawing, trace, kind, chart.x_column or "", chart.y_column or "")
    elif kind == "bar":
        _draw_categorical_bars(drawing, trace)
    else:
        raise ValueError(f"Unsupported report chart type: {kind}")
    return drawing


def _chart_drawings(dataset_id: str) -> list[ChartSpec]:
    response = generate_charts(dataset_id)
    return response.charts


def _paragraph(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(value)).replace("\n", "<br/>"), style)


def _table(rows: list[list], widths: list[float], repeat_rows: int = 1) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=repeat_rows, hAlign="LEFT", splitByRow=1, splitInRow=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PALE),
                ("TEXTCOLOR", (0, 0), (-1, 0), INK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _finding_rows(summary, styles) -> list[list]:
    rows: list[list] = [[
        _paragraph("Issue", styles["TableHead"]),
        _paragraph("What was found", styles["TableHead"]),
        _paragraph("Why it matters", styles["TableHead"]),
        _paragraph("Suggested action", styles["TableHead"]),
    ]]
    recommendations = summary.data_quality.recommendations
    for finding in recommendations:
        if finding.issue == "missing_values":
            column_name = finding.message.split(":", 1)[0]
            rows.append([
                _paragraph("Missing values", styles["TableCell"]),
                _paragraph(f"{finding.affected_count:,} cells are missing in {column_name}.", styles["TableCell"]),
                _paragraph("Some summaries or charts may use fewer observations for this column.", styles["TableCell"]),
                _paragraph("Review the affected records and decide whether values should remain blank or be handled for a specific analysis.", styles["TableCell"]),
            ])
        elif finding.issue == "duplicate_rows":
            rows.append([
                _paragraph("Exact duplicate rows", styles["TableCell"]),
                _paragraph(f"{finding.affected_count:,} repeated row(s) match across all columns.", styles["TableCell"]),
                _paragraph("Repeated records can increase totals or counts if they are unintended.", styles["TableCell"]),
                _paragraph("Check whether the repeated records are legitimate; the source data has not been changed.", styles["TableCell"]),
            ])
        elif finding.issue == "format_consistency":
            column_name = finding.message.split(":", 1)[0]
            rows.append([
                _paragraph("Format consistency", styles["TableCell"]),
                _paragraph(f"{finding.affected_count:,} value(s) in {column_name} do not match the inferred format.", styles["TableCell"]),
                _paragraph("Inconsistent contact details may be harder to validate or use.", styles["TableCell"]),
                _paragraph("Review those values against the intended format before making edits.", styles["TableCell"]),
            ])
    for finding in summary.data_quality.potential_outliers:
        match = re.match(r"([^:]+):", finding.message)
        column_name = match.group(1) if match else "A numeric column"
        rows.append([
            _paragraph("Potential unusual values", styles["TableCell"]),
            _paragraph(f"{finding.affected_count:,} value(s) in {column_name} are unusually far from the middle of the observed values (1.5×IQR check).", styles["TableCell"]),
            _paragraph("These may be genuine unusual cases or data-entry issues; the check does not confirm an error.", styles["TableCell"]),
            _paragraph("Review the original records and context before deciding whether any change is appropriate.", styles["TableCell"]),
        ])
    return rows


def _executive_summary(summary) -> str:
    rows, columns = summary.total_rows, summary.columns
    score = summary.data_quality.overall_score
    if rows == 0:
        opening = f"This dataset has no data rows across {columns:,} column(s), so row-based checks could not assess observations."
    else:
        opening = f"This dataset contains {rows:,} rows across {columns:,} columns. "
        if summary.missing_values_total or summary.duplicate_rows:
            opening += "The checks found some data-quality items worth reviewing."
        else:
            opening += "The checks did not flag missing cells or exact duplicate rows."
    return f"{opening} Its data-quality score is {score:.1f} out of 100; this score summarizes the checks described in this report, not every possible data issue."


def _column_profile_rows(summary, styles) -> list[list]:
    rows = [[
        _paragraph("Column", styles["TableHead"]),
        _paragraph("Data type", styles["TableHead"]),
        _paragraph("Missing cells", styles["TableHead"]),
        _paragraph("Unique values", styles["TableHead"]),
        _paragraph("Relevant details", styles["TableHead"]),
    ]]
    for column in summary.column_summaries:
        if column.semantic_type == "numeric":
            details = []
            if column.mean is not None:
                details.append(f"Average {column.mean:,.4g}")
            if column.median is not None:
                details.append(f"Median {column.median:,.4g}")
            if column.min is not None and column.max is not None:
                details.append(f"Range {column.min:,.4g}–{column.max:,.4g}")
            relevant = "; ".join(details) or "No numeric values available"
        elif column.semantic_type in {"categorical", "boolean"}:
            if column.top_value_status == "repeated" and column.top_value is not None:
                relevant = f"Most common: {column.top_value} ({column.top_value_count:,})"
            elif column.top_value_status == "tie" and column.top_value_ties:
                relevant = "Most common (tie): " + ", ".join(column.top_value_ties[:3])
            elif column.top_value_status == "no_values":
                relevant = "No non-missing values"
            else:
                relevant = "No repeated value"
        elif column.semantic_type == "datetime":
            relevant = f"Observed dates: {column.earliest or '—'} to {column.latest or '—'}"
        else:
            relevant = "No additional summary for this type"
        missing = f"{column.missing_count:,} ({column.missing_pct:.1f}%)"
        rows.append([
            _paragraph(column.name, styles["TableCell"]),
            _paragraph(column.semantic_type.title(), styles["TableCell"]),
            _paragraph(missing, styles["TableCell"]),
            _paragraph(f"{column.unique_count:,}", styles["TableCell"]),
            _paragraph(relevant, styles["TableCell"]),
        ])
    return rows


def _interpretation(chart: ChartSpec) -> str:
    x = chart.x_column or ""
    y = chart.y_column or ""
    return {
        "bar": f"Compares the total {y} across values of {x}.",
        "pie": f"Shows how the values of {x} are divided across the displayed categories.",
        "histogram": f"Groups observed {x} values into ranges and shows how many observations fall in each range.",
        "line": f"Shows the summed {y} at each observed {x} value in time order.",
        "scatter": f"Places each observation by {x} and {y}; the points show the values without asserting a cause or relationship.",
        "box": f"Compares the middle and spread of {y} across {x} categories; unusual points are not necessarily errors.",
        "heatmap": "Shows pairwise correlation values for numeric columns. Correlation alone does not establish cause and effect.",
    }.get(chart.type, "")


def generate_pdf_report(dataset_id: str) -> tuple[bytes, str]:
    metadata = DatasetStore.get(dataset_id)
    df = load_dataframe(dataset_id)
    summary = build_dataset_summary(dataset_id)
    filename = _safe_filename(metadata["filename"])
    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=INK, alignment=TA_LEFT, spaceAfter=8))
    styles.add(ParagraphStyle(name="ReportSubtitle", parent=styles["BodyText"], fontSize=10, leading=14, textColor=MUTED, spaceAfter=4))
    styles.add(ParagraphStyle(name="SectionHeading", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=INK, spaceBefore=14, spaceAfter=8, keepWithNext=True))
    styles.add(ParagraphStyle(name="SubHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=ACCENT, spaceBefore=8, spaceAfter=5, keepWithNext=True))
    styles.add(ParagraphStyle(name="BodyReadable", parent=styles["BodyText"], fontSize=9.5, leading=14, textColor=INK, spaceAfter=6))
    styles.add(ParagraphStyle(name="BulletReadable", parent=styles["BodyReadable"], leftIndent=14, firstLineIndent=-9, bulletIndent=0, spaceAfter=5))
    styles.add(ParagraphStyle(name="TableHead", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.5, leading=10, textColor=INK))
    styles.add(ParagraphStyle(name="TableCell", parent=styles["BodyText"], fontSize=8, leading=10.5, textColor=INK, wordWrap="CJK"))
    styles.add(ParagraphStyle(name="ChartTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=INK, spaceAfter=5))
    styles.add(ParagraphStyle(name="ChartType", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=ACCENT, spaceBefore=8, spaceAfter=3))

    story = [
        Spacer(1, 0.18 * inch),
        _paragraph("DataPilot — Dataset Analysis Report", styles["ReportTitle"]),
        _paragraph(f"Dataset: {metadata['filename']}", styles["ReportSubtitle"]),
        _paragraph(f"Generated: {generated_at}", styles["ReportSubtitle"]),
        Spacer(1, 0.12 * inch),
        _paragraph("Report overview", styles["SectionHeading"]),
        _paragraph(f"Rows: {summary.total_rows:,}    Columns: {summary.columns:,}", styles["SubHeading"]),
        _paragraph(_executive_summary(summary), styles["BodyReadable"]),
    ]

    findings = _finding_rows(summary, styles)
    key_findings = []
    if summary.missing_values_total:
        key_findings.append(f"{summary.missing_values_total:,} missing cell(s) were found across the dataset.")
    if summary.duplicate_rows:
        key_findings.append(f"{summary.duplicate_rows:,} exact duplicate row(s) were detected.")
    if summary.data_quality.potential_outliers:
        total_outliers = sum(item.affected_count for item in summary.data_quality.potential_outliers)
        key_findings.append(f"{total_outliers:,} potential unusual numeric value(s) merit review; they are not confirmed errors.")
    if not key_findings:
        key_findings.append("The checks performed found no missing cells, exact duplicate rows, or potential outliers.")
    story.append(_paragraph("Key findings", styles["SubHeading"]))
    story.extend(
        KeepTogether([_paragraph(f"• {item}", styles["BulletReadable"])])
        for item in key_findings[:4]
    )

    summary_table = _table(
        [
            [
                _paragraph("Missing cells", styles["TableHead"]),
                _paragraph("Exact duplicate rows", styles["TableHead"]),
                _paragraph("Data-quality score", styles["TableHead"]),
            ],
            [
                _paragraph(f"{summary.missing_values_total:,}", styles["BodyReadable"]),
                _paragraph(f"{summary.duplicate_rows:,}", styles["BodyReadable"]),
                _paragraph(f"{summary.data_quality.overall_score:.1f} / 100", styles["BodyReadable"]),
            ],
        ],
        [CONTENT_WIDTH / 3] * 3,
    )
    story.extend([Spacer(1, 5), summary_table])

    story.append(PageBreak())
    story.append(_paragraph("Data quality and reliability", styles["SectionHeading"]))
    if len(findings) > 1:
        story.append(_table(findings, [0.95 * inch, 1.55 * inch, 1.72 * inch, CONTENT_WIDTH - 4.22 * inch]))
    else:
        story.append(_paragraph("No issues were detected by the missing-value, exact-duplicate, email/phone-format, or potential-outlier checks performed. This does not rule out every possible data problem.", styles["BodyReadable"]))
    story.append(_paragraph("How the score is calculated", styles["SubHeading"]))
    story.append(_paragraph(
        "The score is the average of three checks: the share of cells that are present, the share of rows that are not exact duplicates, and the consistency of checked email or phone formats. When no email or phone fields are available to check, that component receives 100. The score does not assess every possible quality concern.",
        styles["BodyReadable"],
    ))

    story.append(_paragraph("Dataset profile and column statistics", styles["SectionHeading"]))
    story.append(_paragraph("Missing counts refer to cells in each column. Unique values exclude blanks. Numeric summaries are shown only for numeric columns; other columns show a common value or observed date range where relevant.", styles["BodyReadable"]))
    story.append(_table(_column_profile_rows(summary, styles), [1.28 * inch, 0.88 * inch, 0.88 * inch, 0.88 * inch, CONTENT_WIDTH - 4.0 * inch]))

    story.append(_paragraph("Visual analytics", styles["SectionHeading"]))
    try:
        charts = _chart_drawings(dataset_id)
    except Exception:
        logger.exception("Optional PDF chart retrieval failed for dataset %s", dataset_id)
        charts = []
    if not charts:
        story.append(_paragraph("No charts were available for this dataset. The report's overview and statistics are still included.", styles["BodyReadable"]))
    else:
        for index, chart in enumerate(charts):
            try:
                drawing = _chart_drawing(chart)
            except Exception:
                logger.exception("Optional PDF chart rendering failed for dataset %s (%s)", dataset_id, chart.type)
                continue
            story.append(KeepTogether([
                _paragraph(_chart_label(chart.type), styles["ChartType"]),
                _paragraph(chart.title, styles["ChartTitle"]),
                drawing,
                _paragraph(_interpretation(chart), styles["BodyReadable"]),
            ]))
            if index < len(charts) - 1:
                story.append(Spacer(1, 0.14 * inch))

    story.append(_paragraph("AI-generated insights", styles["SectionHeading"]))
    story.append(_paragraph("No saved AI-generated insight is available for this dataset. The report uses computed dataset facts and does not invent AI observations.", styles["BodyReadable"]))

    story.append(_paragraph("Recommended next steps", styles["SectionHeading"]))
    next_steps = []
    if summary.missing_values_total:
        next_steps.append("Review records with missing cells and choose how to handle them for the analysis at hand; the report does not fill values.")
    if summary.duplicate_rows:
        next_steps.append("Check whether exact repeated rows are intentional before using totals; no rows were removed.")
    if any(item.issue == "format_consistency" for item in summary.data_quality.recommendations):
        next_steps.append("Review email or phone values flagged for format consistency against the format expected by your workflow.")
    if summary.data_quality.potential_outliers:
        next_steps.append("Investigate potential unusual numeric values in their original context; an outlier is not automatically an error.")
    if not next_steps:
        next_steps.append("No action was suggested by the checks performed. Consider any domain-specific validation needed for your use case.")
    for step in next_steps:
        story.append(KeepTogether([_paragraph(f"• {step}", styles["BulletReadable"])]))

    def draw_footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.5)
        canvas.line(0.65 * inch, 0.52 * inch, PAGE_WIDTH - 0.65 * inch, 0.52 * inch)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.65 * inch, 0.33 * inch, "Generated by DataPilot")
        canvas.drawRightString(PAGE_WIDTH - 0.65 * inch, 0.33 * inch, f"Page {document.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.58 * inch,
        bottomMargin=0.72 * inch,
        title=f"DataPilot — Dataset Analysis Report — {metadata['filename']}",
        author="DataPilot",
        pageCompression=0,
    )
    document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return buffer.getvalue(), f"{filename}-report.pdf"
