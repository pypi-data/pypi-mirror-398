# Based on our override (see README.md) of openapi-python-client's Jinja template
# (https://github.com/openapi-generators/openapi-python-client/blob/main/openapi_python_client/templates/errors.py.jinja)
from __future__ import annotations

from pydantic import ValidationError


class ErrorParsingException(Exception):
    """Raised by API functions when the API returns an object that cannot
    be parsed as the ``Error`` model.
    """

    def __init__(self, message: str, validation_error: ValidationError):
        self.validation_error = validation_error

        super().__init__(
            "\n\n".join(
                [message, "Validation details:", validation_error.json(indent=2)]
            )
        )


__all__ = ["ErrorParsingException"]
