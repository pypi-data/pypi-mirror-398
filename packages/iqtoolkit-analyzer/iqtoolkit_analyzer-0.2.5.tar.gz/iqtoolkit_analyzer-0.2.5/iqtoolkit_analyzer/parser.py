import csv
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from tqdm import tqdm

logger = logging.getLogger(__name__)


_ALLOWED_PATH_ROOTS_ENV = "IQTOOLKIT_ALLOWED_PATH_ROOTS"


def _default_allowed_path_roots() -> list[Path]:
    roots: list[Path] = []
    for candidate in (Path.cwd(), Path.home()):
        try:
            roots.append(candidate.resolve(strict=False))
        except Exception:
            # Best-effort only; resolution failures should not crash import.
            continue

    extra = os.getenv(_ALLOWED_PATH_ROOTS_ENV)
    if extra:
        for raw_root in extra.split(os.pathsep):
            raw_root = raw_root.strip()
            if not raw_root:
                continue
            root_path = Path(raw_root).expanduser()
            if not root_path.is_absolute():
                root_path = Path.cwd() / root_path
            try:
                roots.append(root_path.resolve(strict=False))
            except Exception:
                continue

    # Deduplicate while preserving order.
    seen: set[Path] = set()
    unique_roots: list[Path] = []
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        unique_roots.append(root)
    return unique_roots


def _resolve_existing_file(user_path: str, *, purpose: str) -> Path:
    """Resolve a user-provided filesystem path to an existing file.

    This function is used by the CLI and internal tooling where reading local files
    is expected. It applies validation and constrains access to allowed roots
    (see `IQTOOLKIT_ALLOWED_PATH_ROOTS`) to mitigate path traversal.
    """
    if "\x00" in user_path:
        raise ValueError(f"Invalid {purpose.lower()} path")

    candidate = Path(user_path).expanduser()  # lgtm[py/path-injection]
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate

    resolved = candidate.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"{purpose} is not a file: {resolved}")

    allowed_roots = _default_allowed_path_roots()
    if allowed_roots and not any(
        resolved.is_relative_to(root) for root in allowed_roots
    ):
        roots_display = ", ".join(str(r) for r in allowed_roots)
        raise ValueError(
            f"{purpose} path is outside allowed roots. "
            f"Set {_ALLOWED_PATH_ROOTS_ENV} (os.pathsep-separated) to add roots. "
            f"Allowed roots: {roots_display}"
        )

    return resolved


def load_config(config_path: str = ".iqtoolkit-analyzer.yml") -> dict[str, Any]:
    """Load YAML config file if present."""
    path = Path(config_path)
    if path.exists():
        resolved = _resolve_existing_file(str(path), purpose="Config file")
        with resolved.open("r", encoding="utf-8", errors="ignore") as f:
            return yaml.safe_load(f) or {}
    return {}


def parse_postgres_log(log_file_path: str, log_format: str = "plain") -> pd.DataFrame:
    """
    Parses database log file and extracts slow queries (currently PostgreSQL format)

    Args:
        log_file_path: Path to the database log file
        log_format: 'plain', 'csv', or 'json'

    Returns:
        DataFrame with columns [timestamp, duration_ms, query]

    Raises:
        FileNotFoundError: If log file doesn't exist
        ValueError: If no slow query entries found
    """
    log_path = _resolve_existing_file(log_file_path, purpose="Log file")

    logger.info(f"Parsing log file: {log_path} (format: {log_format})")

    if log_format == "plain":
        with log_path.open("r", encoding="utf-8", errors="ignore") as f:
            log_text = f.read()
        # Regex to capture timestamp, duration, the statement, and an optional
        # EXPLAIN plan
        pattern = (
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}).*?"
            r"duration: "
            r"([\d.]+) ms.*?statement: "
            r"([\s\S]+?)(?=\n\d{4}-\d{2}-\d{2} |"
            r"\[\n  {\n    \"Plan|\Z)"
            r"(\[\n  {\n    \"Plan\"[\s\S]*?}\n\])?"
        )
        matches = re.findall(pattern, log_text, re.DOTALL)
        if not matches:
            warning_msg = (
                "No slow query entries matched the expected pattern. "
                "Check your log format and log_min_duration_statement setting."
            )
            logger.warning(warning_msg)
            print(warning_msg)
            raise ValueError(
                "No slow query entries found. "
                "Ensure log_min_duration_statement is configured."
            )
        log_entries = []
        # Always show progress bar, even for small files
        for idx, match in enumerate(
            tqdm(
                matches,
                desc="Parsing log entries",
                unit="entry",
                mininterval=0.1,
                miniters=1,
            )
        ):
            if idx > 0 and idx % 100 == 0:
                print(f"Examined {idx} log entries...")
                logger.info(f"Examined {idx} log entries...")
            try:
                query = match[2].strip()
                query = query.replace("\\'", "'")
                explain_plan = match[3].strip() if match[3] else None
                log_entries.append(
                    {
                        "timestamp": pd.to_datetime(match[0]),
                        "duration_ms": float(match[1]),
                        "query": query,
                        "explain_plan": explain_plan,
                    }
                )
            except Exception as e:
                logger.warning(f"Skipping malformed entry: {e}")
                continue
        df = pd.DataFrame(log_entries)
        # Ensure explain_plan column exists even if no plans were found
        if "explain_plan" not in df.columns:
            df["explain_plan"] = None

        logger.info(f"Parsed {len(df)} slow query entries (plain)")
        return df

    elif log_format == "csv":
        # Expecting CSV with columns: timestamp,duration_ms,query
        with log_path.open(newline="", encoding="utf-8", errors="ignore") as csvfile:
            reader = list(csv.DictReader(csvfile))
            total = len(reader)
            if total == 0:
                logger.warning("CSV log file is empty or missing required columns.")
                print("CSV log file is empty or missing required columns.")
                raise ValueError("No slow query entries found in CSV log.")
            rows = []
            for idx, row in enumerate(
                tqdm(
                    reader,
                    desc="Parsing CSV log entries",
                    unit="entry",
                    mininterval=0.1,
                    miniters=1,
                )
            ):
                if idx > 0 and idx % 100 == 0:
                    print(f"Examined {idx} CSV log entries...")
                    logger.info(f"Examined {idx} CSV log entries...")
                if "timestamp" in row and "duration_ms" in row and "query" in row:
                    rows.append(row)
        if not rows:
            logger.warning("No valid slow query entries found in CSV log.")
            print("No valid slow query entries found in CSV log.")
            raise ValueError("No slow query entries found in CSV log.")
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["duration_ms"] = df["duration_ms"].astype(float)
        logger.info(f"Parsed {len(df)} slow query entries (csv)")
        return df

    elif log_format == "json":
        # Expecting JSON lines: {"timestamp":..., "duration_ms":..., "query":...}
        log_entries = []
        with log_path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            total = len(lines)
            if total == 0:
                logger.warning("JSON log file is empty.")
                print("JSON log file is empty.")
                raise ValueError("No slow query entries found in JSON log.")
            for idx, line in enumerate(
                tqdm(
                    lines,
                    desc="Parsing JSON log entries",
                    unit="entry",
                    mininterval=0.1,
                    miniters=1,
                )
            ):
                if idx > 0 and idx % 100 == 0:
                    print(f"Examined {idx} JSON log entries...")
                    logger.info(f"Examined {idx} JSON log entries...")
                try:
                    entry = json.loads(line)
                    if (
                        "timestamp" in entry
                        and "duration_ms" in entry
                        and "query" in entry
                    ):
                        log_entries.append(entry)
                except Exception as e:
                    logger.warning(f"Skipping malformed JSON line: {e}")
        if not log_entries:
            logger.warning("No valid slow query entries found in JSON log.")
            print("No valid slow query entries found in JSON log.")
            raise ValueError("No slow query entries found in JSON log.")
        df = pd.DataFrame(log_entries)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["duration_ms"] = df["duration_ms"].astype(float)
        logger.info(f"Parsed {len(df)} slow query entries (json)")
        return df

    else:
        raise ValueError(f"Unsupported log format: {log_format}")
