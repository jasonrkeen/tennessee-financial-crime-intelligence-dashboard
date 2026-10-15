> This file mirrors `.github/copilot-instructions.md` and `CLAUDE.md`; keep all three in sync when any changes.

# AGENTS.md — tennessee-financial-crime-intelligence-dashboard

## Purpose
Python and Streamlit dashboard analyzing Tennessee SAR trends, financial crime context, OFAC sanctions geography, public-sector fraud indicators, and current monitoring signals.

## Tech stack
- Python; dependencies in `requirements.txt`
- Key libraries: `pandas`, `numpy`, `matplotlib`, `openpyxl`, `requests`, `reportlab`, `streamlit`

## Folder structure
- `src/` (20 files)
- `README.md`
- `app.py`
- `main.py`
- `requirements.txt`

## Setup, run, test
Commands documented in README.md (referenced files exist):
```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit>=1.35.0
python main.py
streamlit run app.py
```
- No automated tests exist yet; if adding them, use pytest under `tests/`.

## Conventions observed
- Functions use type hints; keep annotating new code.
- Config lives in: `src/config.py`; avoid hardcoding parameters elsewhere.
- Raw data (`data/raw/`) is gitignored; download/fetch it via the pipeline, do not commit it.
- Public data sources referenced: OFAC.
- Write paths relative to the repo root (no absolute local paths).

## Output artifacts
- A PDF report is produced with `reportlab`; keep it in sync with model changes.
- Streamlit dashboard: `app.py` (run with `streamlit run <file>`).
- Charts are generated with matplotlib.

## Guardrails
- Never commit secrets, API keys, tokens, or `.env` files.
- Do not commit large raw datasets or binaries; keep data fetched or documented with its source.
- Keep analysis source-backed: cite data sources and assumptions; label scenario/forecast outputs as model estimates, not facts.
- Preserve reproducibility: no unseeded randomness, no hidden manual steps.
