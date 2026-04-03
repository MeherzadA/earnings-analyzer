# AGENTS.md

## Project overview
- Purpose: Analyze earnings call transcripts for a given ticker/quarter/year and return a structured, LLM-generated assessment.
- Primary workflow: API receives `ticker`, `year`, `quarter` -> fetch transcript -> run Gemini analysis -> persist transcript + analysis in Postgres -> return JSON response.
- Main components:
- `backend\main.py`: FastAPI app and `/analyze` endpoint orchestration.
- `backend\transcript.py`: Transcript fetcher using `defeatbeta-api`.
- `backend\analysis.py`: LLM prompt + response parsing using `google-genai`.
- `backend\models.py`: SQLAlchemy ORM models (`User`, `SavedTicker`, `Transcript`, `Analysis`).
- `backend\database.py`: DB engine/session setup from `DATABASE_URL`.
- Data storage: Postgres tables defined in `backend\schema.sql` and mirrored by ORM.

## Setup commands
- Create virtualenv: `python -m venv venv`  <!-- TODO: confirm python version -->
- Activate venv (Windows PowerShell): `.\venv\Scripts\Activate.ps1`
- Install deps: `pip install -r backend\requirements.txt`
- Set env vars: `DATABASE_URL=...` and `GEMINI_API_KEY=...` in `backend\.env`
- Start API (from `backend`): `uvicorn main:app --reload`

## Testing instructions
- No test runner found in repo.  <!-- TODO: add test/lint commands if you have them -->

## Code style
- Python FastAPI app with SQLAlchemy ORM models.
- No formatter/linter config found.  <!-- TODO: add formatting/lint rules (black/ruff/flake8/etc) -->
- API returns JSON and expects `ticker`, `year`, `quarter` in POST `/analyze`.

## Dev environment tips
- Repo currently contains only `backend` sources; `frontend` directory is empty.
- `backend\schema.sql` documents the Postgres schema; `models.py` mirrors it.
- `transcript.py` uses `defeatbeta-api` to fetch earnings call transcripts.
- `analysis.py` calls `google-genai` (Gemini) and expects valid JSON output.
