import re

import pandas as pd

_IDENTIFIER_NAME_RULES = (
    (re.compile(r"\b(email|e-mail)\b", re.I), "email address"),
    (re.compile(r"\b(phone|mobile|contact\s*(no|number)?|telephone)\b", re.I), "phone number"),
    (re.compile(r"\b(zip|postal)\s*(code)?\b", re.I), "postal code"),
    (
        re.compile(
            r"\b(id|identifier|account|registration|transaction|candidate|customer|employee|"
            r"record|reference|ref|code)\b",
            re.I,
        ),
        "identifier",
    ),
)
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_PATTERN = re.compile(
    r"^(?!\d{4}-\d{2}-\d{2}$)(?=(?:\D*\d){7,15}\D*$)\+?[\d().\-\s]+$"
)
_DATE_NAME_PATTERN = re.compile(r"\b(date|datetime|timestamp|created at|updated at)\b", re.I)
_ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+\-Z]+)?$")


def _semantic_name(name: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return re.sub(r"[_\-]+", " ", spaced)


def named_identifier_category(name: str) -> tuple[str | None, str | None]:
    name = _semantic_name(name)
    for pattern, category in _IDENTIFIER_NAME_RULES:
        if pattern.search(name):
            return "identifier", f"Column name suggests a {category}."
    return None, None


def named_date_column(name: str) -> bool:
    return bool(_DATE_NAME_PATTERN.search(_semantic_name(name)))


def identifier_category(name: str, series: pd.Series) -> tuple[str | None, str | None]:
    identifier_type, reason = named_identifier_category(name)
    if identifier_type:
        return identifier_type, reason

    values = series.dropna().astype(str).str.strip()
    if values.empty:
        return None, None

    email_ratio = values.str.match(_EMAIL_PATTERN).mean()
    if email_ratio >= 0.8:
        return "identifier", "Most non-missing values match an email-address pattern."

    if not pd.api.types.is_numeric_dtype(series):
        phone_ratio = values.str.match(_PHONE_PATTERN).mean()
        formatted_phone_ratio = values.str.contains(r"[\s().+\-]").mean()
        if phone_ratio >= 0.8 and formatted_phone_ratio >= 0.8:
            return "identifier", "Most text values match a phone-number pattern."

    return None, None


def semantic_type(name: str, series: pd.Series) -> tuple[str, str | None]:
    identifier_type, reason = identifier_category(name, series)
    if identifier_type:
        return identifier_type, reason
    if series.dropna().empty:
        return "unknown", None
    if pd.api.types.is_bool_dtype(series):
        return "boolean", None
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime", None
    if pd.api.types.is_numeric_dtype(series):
        return "numeric", None
    return "categorical", None


def normalize_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        series = df[column]
        if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
            continue

        stripped = series.map(lambda value: value.strip() if isinstance(value, str) else value)
        stripped = stripped.replace("", pd.NA)
        identifier_type, _ = identifier_category(str(column), stripped)
        if identifier_type:
            df[column] = stripped
            continue

        non_missing = stripped.dropna()
        if non_missing.empty:
            df[column] = stripped
            continue

        normalized_values = non_missing.astype(str).str.casefold()
        if normalized_values.isin({"true", "false"}).all():
            df[column] = stripped.map(
                lambda value: pd.NA
                if pd.isna(value)
                else str(value).strip().casefold() == "true"
            ).astype("boolean")
            continue

        if named_date_column(str(column)):
            if non_missing.map(
                lambda value: bool(_ISO_DATE_PATTERN.fullmatch(str(value)))
            ).all():
                df[column] = pd.to_datetime(stripped, format="ISO8601", errors="coerce")
            else:
                df[column] = stripped
            continue

        numeric = pd.to_numeric(stripped, errors="coerce")
        if numeric.notna().sum() == len(non_missing):
            df[column] = numeric
        else:
            df[column] = stripped

    return df
