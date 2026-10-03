"""Deterministic and atomic JSON output helpers."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any

from src.models import BookRecord


def deduplicate_records(records: list[BookRecord]) -> list[BookRecord]:
    unique: dict[str, BookRecord] = {}
    for record in records:
        unique.setdefault(str(record.product_url), record)
    return list(unique.values())


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(value, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_name = temporary.name
        Path(temporary_name).replace(path)
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
