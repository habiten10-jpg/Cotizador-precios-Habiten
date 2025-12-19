# Cotizador-precios-Habiten

Sistema de valoración automática de partidas de obra mediante similitud semántica.

## Objetivo

Procesar partidas de obra desde un proyecto (Excel o PDF) y asignar precios desde una base interna en Excel usando embeddings semánticos, reglas de negocio y compatibilidad de unidades.

## Requisitos

- Python 3.10+
- Dependencias en `requirements.txt`

```bash
pip install -r requirements.txt
```

> Nota: `camelot-py` requiere Ghostscript. Si no está disponible, use PDFs con tablas detectables por `pdfplumber` o exporte el proyecto a Excel.

## Estructura de carpetas

```
.
├── README.md
├── requirements.txt
└── src
    ├── __init__.py
    ├── embeddings.py
    ├── io_utils.py
    ├── main.py
    ├── matcher.py
    ├── normalize.py
    └── rules.py
```

## Uso paso a paso

1. Prepare la base de precios en Excel con columnas:
   - `descripcion`
   - `unidad`
   - `precio_unitario`
   - (opcional) `familia`

2. Prepare el proyecto en Excel o PDF con columnas:
   - `descripcion_proyecto`
   - `unidad`
   - `cantidad` (si no existe se asume 1)

3. Ejecute el script:

```bash
python -m src.main --base ./data/base_precios.xlsx --proyecto ./data/proyecto.xlsx --salida ./salidas/valorado.xlsx
```

### Salida

- Hoja `Valorado`: partidas con `precio_unitario_asignado`, `importe`, `descripcion_base_asignada` y `match_score`.
- Hoja `Pendientes`: partidas sin match automático o con revisión.
- Hoja `Candidatos`: top 3 candidatos cuando la decisión es `revision`.

## Reglas de decisión

- Score ≥ 0.85 y unidad compatible → asignación automática.
- Score entre 0.75 y 0.85 → propuesta de top 3 candidatos.
- Score < 0.75 → sin match.

Las reglas de negocio (boosts y exclusiones) se encuentran en `src/rules.py`.

## Personalización rápida

- Normalización de texto y unidades: `src/normalize.py`
- Lectura de Excel/PDF: `src/io_utils.py`
- Lógica de matching: `src/matcher.py`
- Reglas de negocio: `src/rules.py`
- Parámetros de modelo y top-k: `src/main.py`
