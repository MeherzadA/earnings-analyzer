import os
from pathlib import Path

import duckdb
import requests


TRANSCRIPTS_URL = (
    "https://huggingface.co/datasets/defeatbeta/yahoo-finance-data/resolve/main/"
    "data/stock_earning_call_transcripts.parquet"
)
CACHE_DIR = Path(__file__).resolve().parent / ".cache"
TRANSCRIPTS_CACHE_PATH = CACHE_DIR / "stock_earning_call_transcripts.parquet"
PROXY_ENV_VARS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "GIT_HTTP_PROXY",
    "GIT_HTTPS_PROXY",
]


def _clear_bad_proxy_env() -> None:
    for key in PROXY_ENV_VARS:
        os.environ.pop(key, None)


def _ensure_transcripts_cache() -> Path:
    if TRANSCRIPTS_CACHE_PATH.exists():
        return TRANSCRIPTS_CACHE_PATH

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = TRANSCRIPTS_CACHE_PATH.with_suffix(".tmp")

    try:
        with requests.get(TRANSCRIPTS_URL, stream=True, timeout=60) as response:
            response.raise_for_status()

            with open(temp_path, "wb") as file_handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file_handle.write(chunk)

        temp_path.replace(TRANSCRIPTS_CACHE_PATH)
        return TRANSCRIPTS_CACHE_PATH
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def fetch_transcript(ticker: str, year: int, quarter: int) -> dict | None:
    try:
        _clear_bad_proxy_env()
        parquet_path = _ensure_transcripts_cache()
        connection = duckdb.connect(":memory:")
        try:
            row = connection.execute(
                """
                SELECT transcripts
                FROM read_parquet(?)
                WHERE symbol = ? AND fiscal_year = ? AND fiscal_quarter = ?
                LIMIT 1
                """,
                [str(parquet_path), ticker.upper(), year, quarter],
            ).fetchone()
        finally:
            connection.close()

        if not row:
            return None

        paragraphs = row[0] or []
        full_text = " ".join(
            paragraph["content"].strip()
            for paragraph in paragraphs
            if paragraph.get("content")
        ).strip()

        if not full_text:
            return None

        return {
            "ticker": ticker.upper(),
            "quarter": quarter,
            "year": year,
            "content": full_text,
        }
    except Exception as e:
        raise RuntimeError(
            f"Transcript provider failed for {ticker.upper()} Q{quarter} {year}: {e}"
        ) from e
    


# result = fetch_transcript("AAPL", 2024, 1)
