from __future__ import annotations

from typing import Union

from pydantic import Field

from latticeflow.go._generated.models.base_model import LFBaseModel

from .. import types
from ..models.model import Dataset
from ..models.model import TaskResult
from ..types import File
from ..types import UNSET
from ..types import Unset


# ---- from create_dataset_body.py ----
class CreateDatasetBody(LFBaseModel):
    request: Dataset = Field(
        ...,
        description="All properties required for the creation of a Dataset, except the binary file.",
    )
    " All properties required for the creation of a Dataset, except the binary file. "
    file: File = Field(..., description="The CSV or JSONL file to upload.")
    " The CSV or JSONL file to upload. "

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []
        request = self.request
        files.append(("request", (None, request.model_dump_json(), "application/json")))
        file = self.file
        if isinstance(file, File):
            files.append(
                (
                    "file",
                    (
                        file.file_name or "file",
                        file.payload,
                        file.mime_type or "application/octet-stream",
                    ),
                )
            )
        return files


# ---- from create_task_result_body.py ----
class CreateTaskResultBody(LFBaseModel):
    request: TaskResult = Field(..., description="")
    files: list[File] = Field(..., description="")

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []
        request = self.request
        files.append(("request", (None, request.model_dump_json(), "application/json")))
        files_value = self.files
        for f in files_value:
            files.append(
                (
                    "files",
                    (
                        f.file_name or "file",
                        f.payload,
                        f.mime_type or "application/octet-stream",
                    ),
                )
            )
        return files


# ---- from update_dataset_data_body.py ----
class UpdateDatasetDataBody(LFBaseModel):
    file: File = Field(..., description="The updated CSV or JSONL file.")
    " The updated CSV or JSONL file. "

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []
        file = self.file
        if isinstance(file, File):
            files.append(
                (
                    "file",
                    (
                        file.file_name or "file",
                        file.payload,
                        file.mime_type or "application/octet-stream",
                    ),
                )
            )
        return files


# ---- from upload_ai_app_artifact_body.py ----
class UploadAIAppArtifactBody(LFBaseModel):
    artifact: Union[Unset, File] = Field(default=UNSET, description="")

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []
        artifact = self.artifact
        if isinstance(artifact, File):
            files.append(
                (
                    "artifact",
                    (
                        artifact.file_name or "file",
                        artifact.payload,
                        artifact.mime_type or "application/octet-stream",
                    ),
                )
            )
        return files
