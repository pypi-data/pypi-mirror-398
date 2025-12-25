from __future__ import annotations

import json
from pathlib import Path

import latticeflow.go.cli.utils.printing as cli_print


def get_configuration_file() -> tuple[dict, Path]:
    config_dir = Path.home() / ".latticeflow"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"

    try:
        with open(config_file, "r") as f:
            config: dict = json.load(f)
    except Exception:
        config = {}
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        cli_print.log_info(
            f"Contents of the configuration file at path '{config_file}' could not be "
            "loaded. The file was created anew."
        )

    return config, config_file


def upsert_configuration_file(config_file: Path, config: dict) -> None:
    with open(config_file, "w") as file:
        json.dump(config, file, indent=2)
