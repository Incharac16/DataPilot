from app.services.ai.factory import get_ai_provider
from app.services.data_loader import load_dataframe
from app.services.data_summary import build_dataset_summary

SYSTEM_PROMPT = "You are an expert AI Data Analyst."

DEFAULT_ANALYSIS_PROMPT = """
Act as a Senior Business Data Analyst.

Analyze this dataset.

Generate a professional report containing:

1. Executive Summary

2. Dataset Quality

3. Missing Values

4. Interesting Trends

5. Outliers

6. Correlations

7. Business Insights

8. Risks

9. Opportunities

10. Five Actionable Recommendations

Use headings and bullet points.
"""


def _build_context(dataset_id: str) -> str:

    summary = build_dataset_summary(dataset_id)
    df = load_dataframe(dataset_id)

    lines = [
        f"Dataset Name: {summary.filename}",
        f"Rows: {summary.rows}",
        f"Columns: {summary.columns}",
        f"Duplicate Rows: {summary.duplicate_rows}",
        f"Total Missing Values: {summary.missing_values_total}",
        "",
        "Columns:"
    ]

    for col in summary.column_summaries:

        lines.append(
            f"- {col.name}"
        )

        lines.append(
            f"  Type: {col.dtype}"
        )

        lines.append(
            f"  Missing: {col.missing_count} ({col.missing_pct}%)"
        )

        lines.append(
            f"  Unique: {col.unique_count}"
        )

        if col.mean is not None:
            lines.append(
                f"  Min={col.min}, Max={col.max}, Mean={col.mean:.2f}, Std={col.std:.2f}"
            )

        if col.top_value is not None:
            lines.append(
                f"  Most common value: {col.top_value}"
            )

        try:
            sample_values = df[col.name].dropna().unique()[:5].tolist()
            if sample_values:
                lines.append(
                    f"  Samples: {sample_values}"
                )
        except Exception:
            pass

    lines.append("")
    lines.append("Dataset Statistics")
    lines.append(df.describe(include="all").to_string())

    return "\n".join(lines)


def generate_insights(dataset_id: str, question: str | None = None) -> str:
    """
    Build a text summary of the dataset and hand it, along with the
    question (or the default analysis prompt), to whichever AI provider
    is configured via AI_PROVIDER (Groq by default).

    Raises ValueError if the configured provider isn't available (e.g. no
    API key set) — routers/insights.py turns that into a 503. Any other
    exception (network/provider error) propagates and becomes a 500.
    """

    # Resolve the provider first so a missing/invalid configuration fails
    # fast, before doing any dataframe work.
    provider = get_ai_provider()

    context = _build_context(dataset_id)
    prompt = question or DEFAULT_ANALYSIS_PROMPT

    final_prompt = f"""
Dataset Information

{context}

User Request

{prompt}
"""

    return provider.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=final_prompt,
    )
