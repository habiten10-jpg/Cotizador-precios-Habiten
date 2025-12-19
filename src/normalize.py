import re
import unicodedata
from typing import Optional

UNIT_ALIASES = {
    "m2": {"m2", "m²", "m^2", "m.2", "m2.", "m2-"},
    "ml": {"ml", "m.l", "m.l.", "m lineal", "m. lineal", "metro lineal"},
    "ud": {"ud", "uds", "unidad", "unid", "u"},
}

UNIT_NORMALIZATION_MAP = {
    alias: canonical
    for canonical, aliases in UNIT_ALIASES.items()
    for alias in aliases
}


def normalize_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9\s\./-]", " ", text)
    text = re.sub(r"[\./-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_unit(unit: Optional[str]) -> str:
    if unit is None:
        return ""
    raw = normalize_text(unit)
    return UNIT_NORMALIZATION_MAP.get(raw, raw)
