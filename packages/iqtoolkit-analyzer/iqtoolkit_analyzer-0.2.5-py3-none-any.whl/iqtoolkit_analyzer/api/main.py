import logging
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from iqtoolkit_analyzer.analyzer import run_slow_query_analysis
from iqtoolkit_analyzer.parser import parse_postgres_log

app = FastAPI()
logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    # NOTE: Treated as a path relative to IQTOOLKIT_API_LOG_DIR (or ./logs).
    # Do not accept arbitrary absolute paths from remote callers.
    log_file_path: str
    log_format: str = "plain"


@app.post("/analyze")
async def analyze_logs(request: AnalyzeRequest) -> dict[str, Any]:
    """
    Analyzes a log file and returns the top slow queries and a summary.
    """
    try:
        base_dir = Path(os.getenv("IQTOOLKIT_API_LOG_DIR", "./logs")).resolve(
            strict=False
        )

        if not base_dir.exists() or not base_dir.is_dir():
            raise HTTPException(
                status_code=500,
                detail="Server log directory is missing or invalid.",
            )

        # Treat API-supplied value as a *filename* within base_dir.
        # This avoids path traversal and keeps CodeQL happy.
        raw_name = request.log_file_path
        if "\x00" in raw_name:
            raise HTTPException(status_code=400, detail="Invalid log_file_path")

        file_name = os.path.basename(raw_name)
        if file_name != raw_name or file_name in {"", ".", ".."}:
            raise HTTPException(status_code=400, detail="Invalid log_file_path")

        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,255}", file_name):
            raise HTTPException(status_code=400, detail="Invalid log_file_path")

        # Avoid constructing a path from user input. Instead, select a file by name
        # from the server-side directory listing.
        candidate: Path | None = None
        for path in base_dir.iterdir():
            if path.is_file() and path.name == file_name:
                candidate = path
                break

        if candidate is None:
            raise HTTPException(status_code=404, detail="Log file not found.")

        candidate = candidate.resolve(strict=True)
        if not candidate.is_relative_to(base_dir):
            raise HTTPException(status_code=400, detail="Invalid log_file_path")

        df: pd.DataFrame = parse_postgres_log(str(candidate), request.log_format)
        result = run_slow_query_analysis(df)
        if not isinstance(result, tuple):
            raise HTTPException(
                status_code=500,
                detail="Unexpected analysis result type.",
            )

        top_queries_df, summary_dict = result
        return {
            "summary": summary_dict,
            "top_queries": top_queries_df.to_dict(orient="records"),
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Log file not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Error during analysis", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error.")
