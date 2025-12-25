from __future__ import annotations

import inspect
import os
import shutil
import subprocess  # nosec
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.metadata.plugin.interface import MetadataHookInterface


LOG_FILE_PATH = Path("build.log")
DROP_FOLDER_PATH = Path("_drop_folder")


def build_log(messages: list[str], nesting_level: int = 1) -> None:
    frame = inspect.currentframe()
    if nesting_level == 1:
        caller_name = (
            frame.f_back.f_code.co_name if frame and frame.f_back else "unknown"
        )
    elif nesting_level == 2:
        caller_name = (
            frame.f_back.f_back.f_code.co_name
            if frame and frame.f_back and frame.f_back.f_back
            else "unknown"
        )
    else:
        raise ValueError(
            f"Invalid nesting level for build_log (provided {nesting_level})"
        )
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE_PATH.open("a", encoding="utf-8") as log:
        log.write("*" * 100 + "\n")
        for message in messages:
            log.write(f"[build] [{caller_name}]: {message}\n")
        log.write("*" * 100 + "\n\n")


def lowercase_first_letter(string: str) -> str:
    return string[0].lower() + string[1:] if string else string


def run_subprocess_with_log_and_error_handling(
    subprocess_descriptive_message: str,
    commands: list[str],
    cwd: str | None = None,
    env: subprocess._ENV | None = None,
) -> None:
    build_log([subprocess_descriptive_message], nesting_level=2)
    result = subprocess.run(
        commands,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        env=env,  # nosec B603
    )

    if result.returncode == 0:
        build_log(
            [
                f"Finished {lowercase_first_letter(subprocess_descriptive_message)}:",
                f"[stdout] = {result.stdout}",
            ],
            nesting_level=2,
        )
    else:
        build_log(
            [
                f"Failed while {lowercase_first_letter(subprocess_descriptive_message)}:",
                f"[status code] = {result.returncode}",
                f"[stdout] = {result.stdout}",
                f"[stderr] = {result.stderr}",
            ],
            nesting_level=2,
        )
        raise RuntimeError(
            f"Build failed! See {LOG_FILE_PATH.absolute()} for more information."
        )


class JSONMetaDataHook(MetadataHookInterface):
    def update(self, metadata: dict[str, Any]) -> None:
        metadata["version"] = os.environ.get("LF_VERSION", "0.0.0dev")


def create_git_version_file(cwd: str, version: str) -> None:
    build_log(["Creating git version file..."])
    try:
        # Safe usage of `subprocess`, read-only and no user input.
        sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd)  # nosec
            .decode("ascii")
            .strip()
        )
    except Exception:  # nosec: B110 # noqa
        sha = "unknown"

    version_path = Path(cwd) / "latticeflow" / "go" / "version.py"
    with open(version_path, "w") as f:
        f.write(f"__version__ = '{version}'\n")
        f.write(f"git_version = {repr(sha)}\n")


def create_py_typed_file(cwd: str) -> None:
    build_log(["Creating py.typed marker file..."])
    # Marker file for PEP 561
    py_typed_path = Path(cwd) / "latticeflow" / "go" / "py.typed"
    open(py_typed_path, "w")


def clean_files_before_generation() -> None:
    for path in [
        Path("latticeflow/go/base.py"),
        Path("latticeflow/go/client.py"),
        Path("latticeflow/go/version.py"),
        Path("latticeflow/go/py.typed"),
    ]:
        build_log([f"Deleting file at {path}..."])
        path.unlink(missing_ok=True)

    for folder in ["latticeflow/go/models", "latticeflow/go/_generated"]:
        build_log([f"Deleting folder at {folder}..."])
        shutil.rmtree(folder, ignore_errors=True)


def bundle_openapi_spec() -> None:
    run_subprocess_with_log_and_error_handling(
        "Bundling OpenAPI spec",
        ["./bundle_public_openapi_spec.sh"],
        cwd="../openapi/assessment",
    )


def generate_sdk() -> None:
    # NOTE: This requires redocly to be installed (npm i -g @redocly/cli@latest)
    # NOTE: The code is generated in a `_drop_folder`` because openapi-python-client
    # otherwise touches our handwritten files if we generate directly into
    # `assessment_sdk/latticeflow/go`. After that, we immediately move it from
    # `assessment_sdk/latticeflow/go/_drop_folder` to `assessment_sdk/latticeflow/go`
    # and delete `_drop_folder`
    base = Path("latticeflow/go")
    drop_folder = base / DROP_FOLDER_PATH
    drop_folder.mkdir(parents=True, exist_ok=True)
    run_subprocess_with_log_and_error_handling(
        "Generating the SDK with openapi-python-client",
        [
            "openapi-python-client",
            "generate",
            "--path",
            "openapi/assessment/openapi-merged.yaml",
            "--output-path",
            f"assessment_sdk/latticeflow/go/{str(DROP_FOLDER_PATH)}",
            "--overwrite",
            "--config",
            "assessment_sdk/config.yaml",
            "--custom-template-path",
            "assessment_sdk/templates/overrides",
        ],
        cwd="..",
    )

    build_log(
        [
            (
                f"Move generated SDK from `assessment_sdk/latticeflow/go/{str(DROP_FOLDER_PATH)}` "
                "to `assessment_sdk/latticeflow/go`..."
            )
        ]
    )
    for item in drop_folder.iterdir():
        target = base / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(item), str(base))

    build_log([f"Delete `assessment_sdk/latticeflow/go/{str(DROP_FOLDER_PATH)}`."])
    shutil.rmtree(drop_folder, ignore_errors=True)

    project_root = Path(__file__).resolve().parent.parent  # top-level project dir
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    run_subprocess_with_log_and_error_handling(
        "Running the custom_generator_pipeline",
        ["python", "-m", "assessment_sdk.utils.custom_sdk_generator_pipeline"],
        env=env,
    )


def cleanup_after_generation() -> None:
    build_log(["Removing unnecessary generated files..."])
    for path in [
        Path("latticeflow/go/.gitignore"),
        Path("latticeflow/go/pyproject.toml"),
        Path("latticeflow/go/README.md"),
    ]:
        build_log([f"Deleting file at {path}..."])
        path.unlink(missing_ok=True)
    run_subprocess_with_log_and_error_handling(
        "Formatting with Ruff",
        ["ruff", "format", "latticeflow", "--config", "./ruff.toml"],
    )
    run_subprocess_with_log_and_error_handling(
        "Checking with Ruff",
        ["ruff", "check", "latticeflow", "--fix", "--config", "./ruff.toml"],
    )


class CustomHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if self.target_name not in ["wheel", "sdist"]:
            return

        clean_files_before_generation()
        create_git_version_file(self.root, version)
        create_py_typed_file(self.root)
        bundle_openapi_spec()
        generate_sdk()
        cleanup_after_generation()

    def finalize(
        self, version: str, build_data: dict[str, Any], artifact_path: str
    ) -> None:
        LOG_FILE_PATH.unlink(missing_ok=True)
