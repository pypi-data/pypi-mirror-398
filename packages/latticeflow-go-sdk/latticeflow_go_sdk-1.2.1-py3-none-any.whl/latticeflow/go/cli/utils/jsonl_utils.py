from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from latticeflow.go.client import Client


def parse_jsonl(
    jsonl_data: str, max_num_rows: int | None = None
) -> tuple[list[str], list[tuple[Any | None, ...]]]:
    samples: list[dict[str, Any]] = [
        json.loads(line) for line in jsonl_data.splitlines()[:max_num_rows]
    ]
    # Consider all samples, as they might have a different set of keys.
    # Keep the order unchanged.
    column_names = list(dict.fromkeys(k for sample in samples for k in sample))
    rows = [tuple(sample.get(k) for k in column_names) for sample in samples]
    return column_names, rows


def download_jsonl_data_from_client(client: Client, download_url: str) -> str:
    url = download_url
    if url.startswith("/api"):
        url_without_api_prefix = url[4:]
    else:
        url_without_api_prefix = url

    response = client.get_client().get_httpx_client().get(url_without_api_prefix)
    response.raise_for_status()
    return response.text


def save_jsonl_data_as_csv_or_jsonl(data_output: Path, jsonl_data: str) -> None:
    _, ext = os.path.splitext(data_output.name)
    if ext.lower() == ".jsonl":
        data_output.write_text(jsonl_data)
    elif ext.lower() == ".csv":
        column_names, samples = parse_jsonl(jsonl_data)
        with data_output.open("w") as f:
            writer = csv.writer(f)
            writer.writerow(column_names)
            for sample in samples:
                writer.writerow(sample)
