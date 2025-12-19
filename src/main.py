import argparse
from pathlib import Path

import pandas as pd

from .io_utils import read_price_base, read_project_file
from .matcher import match_project_items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valoración automática de partidas de obra por similitud semántica.",
    )
    parser.add_argument("--base", required=True, help="Excel de base de precios")
    parser.add_argument("--proyecto", required=True, help="Archivo de proyecto (Excel o PDF)")
    parser.add_argument("--salida", required=True, help="Ruta del Excel de salida")
    parser.add_argument(
        "--modelo",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Modelo de sentence-transformers a usar",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Número de candidatos")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_path = Path(args.base)
    project_path = Path(args.proyecto)
    output_path = Path(args.salida)

    base_df = read_price_base(base_path)
    project_df = read_project_file(project_path)

    matched_df, candidates_df = match_project_items(
        project_df=project_df,
        base_df=base_df,
        model_name=args.modelo,
        top_k=args.top_k,
    )

    pendientes_df = matched_df[matched_df["decision"] != "auto"].copy()

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        matched_df.to_excel(writer, index=False, sheet_name="Valorado")
        pendientes_df.to_excel(writer, index=False, sheet_name="Pendientes")
        if not candidates_df.empty:
            candidates_df.to_excel(writer, index=False, sheet_name="Candidatos")


if __name__ == "__main__":
    main()
