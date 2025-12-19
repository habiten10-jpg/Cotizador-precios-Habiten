import re
from typing import List, Tuple

from .normalize import normalize_text

EXCLUDE_PATTERNS = [
    r"sin match",
]

KEYWORD_BOOSTS: List[Tuple[str, float]] = [
    (r"hormigon|hormig[oó]n", 0.03),
    (r"demolic", 0.02),
    (r"pintura", 0.02),
]


def has_exclusion(description: str) -> bool:
    normalized = normalize_text(description)
    return any(re.search(pattern, normalized) for pattern in EXCLUDE_PATTERNS)


def apply_keyword_boosts(
    project_description: str,
    base_description: str,
    score: float,
) -> float:
    project_normalized = normalize_text(project_description)
    base_normalized = normalize_text(base_description)
    for pattern, boost in KEYWORD_BOOSTS:
        if re.search(pattern, project_normalized) and re.search(pattern, base_normalized):
            score += boost
    return min(score, 1.0)
