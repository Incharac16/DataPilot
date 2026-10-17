from app.services.ai.factory import get_ai_provider
from app.services.data_loader import load_dataframe

from app.services.factual_analytics import (
    calculate_dataset_facts,
    factual_context,
    verified_facts_for_answer,
)

SYSTEM_PROMPT = (
    "You are a careful data analyst. Explain the supplied deterministic facts. "
    "Never invent or estimate dataset statistics, columns, records, categories, "
    "trends, or correlations. If the supplied facts do not answer the question, "
    "say so clearly. Separate computed facts from interpretations and recommendations. "
    "For general questions unrelated to the dataset, make clear that the answer is general."
)

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


def _build_context(dataset_id: str, question: str | None = None) -> tuple[dict, list[str]]:
    df = load_dataframe(dataset_id)
    facts = calculate_dataset_facts(df, question)
    return facts, verified_facts_for_answer(facts)


def _generate_with_verified_facts(
    dataset_id: str,
    question: str | None,
) -> tuple[str, list[str]]:
    facts, _ = _build_context(dataset_id, question)
    verified_facts = verified_facts_for_answer(facts)
    prompt = question or DEFAULT_ANALYSIS_PROMPT

    final_prompt = f"""
The following JSON contains deterministic facts calculated from the uploaded dataset with Pandas.
Treat it as the only source for exact dataset statistics. Do not derive or guess additional values.

Computed facts:
{factual_context(facts)}

User Request

{prompt}
"""

    try:
        provider = get_ai_provider()
    except ValueError:
        raise
    except Exception as error:
        raise RuntimeError("The configured AI provider could not complete the request.") from error
    try:
        response = provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=final_prompt,
        )
    except Exception as error:
        raise RuntimeError("The configured AI provider could not complete the request.") from error
    if not isinstance(response, str) or not response.strip():
        raise RuntimeError("The configured AI provider returned an empty response.")
    return response.strip(), verified_facts


def generate_insights(dataset_id: str, question: str | None = None) -> str:
    """Return an LLM explanation grounded in Pandas-computed dataset facts."""
    response, _ = _generate_with_verified_facts(dataset_id, question)
    return response


def generate_grounded_insights(
    dataset_id: str,
    question: str | None = None,
) -> tuple[str, list[str]]:
    return _generate_with_verified_facts(dataset_id, question)
