from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd

from .embeddings import EmbeddingIndex
from .normalize import normalize_unit
from .rules import apply_keyword_boosts, has_exclusion


@dataclass
class MatchResult:
    score: float
    base_index: int
    base_description: str
    base_unit: str
    base_price: float
    unit_compatible: bool


def units_compatible(project_unit: str, base_unit: str) -> bool:
    if not project_unit or not base_unit:
        return True
    return normalize_unit(project_unit) == normalize_unit(base_unit)


def penalize_unit_mismatch(score: float, compatible: bool) -> float:
    if compatible:
        return score
    return score * 0.75


def build_index(base_df: pd.DataFrame, model_name: str) -> EmbeddingIndex:
    index = EmbeddingIndex(model_name=model_name)
    index.build(base_df["descripcion_norm"].tolist())
    return index


def match_project_items(
    project_df: pd.DataFrame,
    base_df: pd.DataFrame,
    model_name: str,
    top_k: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    index = build_index(base_df, model_name)
    project_vectors = index.encode(project_df["descripcion_norm"].tolist())
    distances, indices = index.search(project_vectors, top_k=top_k)

    results: List[MatchResult] = []
    candidates: List[List[MatchResult]] = []

    for row_idx, base_indices in enumerate(indices):
        row_candidates: List[MatchResult] = []
        for rank, base_idx in enumerate(base_indices):
            base_row = base_df.iloc[int(base_idx)]
            score = float(distances[row_idx][rank])
            compatible = units_compatible(
                project_df.iloc[row_idx]["unidad_norm"],
                base_row["unidad_norm"],
            )
            score = penalize_unit_mismatch(score, compatible)
            score = apply_keyword_boosts(
                project_df.iloc[row_idx]["descripcion_proyecto"],
                base_row["descripcion"],
                score,
            )
            row_candidates.append(
                MatchResult(
                    score=score,
                    base_index=int(base_idx),
                    base_description=base_row["descripcion"],
                    base_unit=base_row["unidad"],
                    base_price=float(base_row["precio_unitario"] or 0.0),
                    unit_compatible=compatible,
                )
            )
        row_candidates.sort(key=lambda item: item.score, reverse=True)
        candidates.append(row_candidates)
        results.append(row_candidates[0])

    project_df = project_df.copy()
    project_df["match_score"] = [result.score for result in results]
    project_df["descripcion_base_asignada"] = [result.base_description for result in results]
    project_df["precio_unitario_asignado"] = [result.base_price for result in results]
    project_df["unidad_base"] = [result.base_unit for result in results]
    project_df["unidad_compatible"] = [result.unit_compatible for result in results]

    auto_mask = (project_df["match_score"] >= 0.85) & project_df["unidad_compatible"]
    review_mask = (project_df["match_score"] >= 0.75) & (~auto_mask)

    project_df["decision"] = np.select(
        [auto_mask, review_mask],
        ["auto", "revision"],
        default="sin_match",
    )

    project_df["importe"] = (
        project_df["precio_unitario_asignado"] * project_df["cantidad"]
    )

    candidates_df_rows = []
    for idx, row_candidates in enumerate(candidates):
        if has_exclusion(project_df.iloc[idx]["descripcion_proyecto"]):
            project_df.loc[idx, "decision"] = "sin_match"
            continue
        if project_df.loc[idx, "decision"] == "revision":
            for candidate in row_candidates[:3]:
                candidates_df_rows.append(
                    {
                        "fila_proyecto": idx,
                        "descripcion_proyecto": project_df.iloc[idx][
                            "descripcion_proyecto"
                        ],
                        "descripcion_base": candidate.base_description,
                        "unidad_base": candidate.base_unit,
                        "precio_unitario": candidate.base_price,
                        "score": candidate.score,
                        "unidad_compatible": candidate.unit_compatible,
                    }
                )

    candidates_df = pd.DataFrame(candidates_df_rows)
    return project_df, candidates_df
