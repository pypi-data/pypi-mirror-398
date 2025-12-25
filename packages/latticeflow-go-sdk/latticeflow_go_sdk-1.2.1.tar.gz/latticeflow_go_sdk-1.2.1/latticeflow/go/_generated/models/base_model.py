from __future__ import annotations

import json
from copy import deepcopy
from typing import Any
from typing import Callable
from typing import cast
from typing import ClassVar
from typing import Literal
from typing import TypeVar

import pydantic
from pydantic.main import IncEx


LFBaseModelT = TypeVar("LFBaseModelT", bound="LFBaseModel")


class LFBaseModel(pydantic.BaseModel):  # noqa: TID251
    """A ``BaseModel`` which excludes unset fields by default when serialising."""

    # NOTE: When updating this, also update
    # `assessment/latticeflow/assessment/utils/pydantic.py::LFBaseModel`

    model_config = pydantic.ConfigDict(extra="forbid")
    nullable_fields: ClassVar[list[str]] = []

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize subclass and collect names of fields that are marked as nullable.

        This method inspects the model's fields and builds a list of field names
        where the field's `json_schema_extra` contains `nullable=True`. The list is
        stored as `cls.nullable_fields` for use in other methods (e.g., to control
        serialization or validation behavior for nullable fields).

        Args:
            **kwargs: Additional keyword arguments passed to the superclass initializer.
        """
        new_nullable_fields: list[str] = []
        for field_name, field in cls.model_fields.items():
            if isinstance(
                field.json_schema_extra, dict
            ) and field.json_schema_extra.get("nullable"):
                new_nullable_fields.append(field_name)

        cls.nullable_fields = new_nullable_fields
        super().__pydantic_init_subclass__(**kwargs)

    def model_post_init(self, context: Any) -> None:
        """
        Post-initialization hook to treat non-nullable fields set to None as UNSET.

        After model initialization, this method iterates over all annotated fields.
        If a field's value is None and it is not in the list of nullable fields,
        the field is removed from the set of fields considered "set" on the model.
        This ensures that only nullable fields will be returned when their value is None
        by the export methods  `model_validate` and `model_validate_json`.

        Args:
            context: Additional context passed by Pydantic during model initialization.

        Returns:
            The result of the superclass's `model_post_init` method.
        """
        field_annotations: set[str] = set()
        for cls in self.__class__.__mro__:
            if cls != LFBaseModel and issubclass(cls, LFBaseModel):
                field_annotations.update(cls.__annotations__)

        for field_name in field_annotations:
            value = getattr(self, field_name, None)
            if value is None and field_name not in self.nullable_fields:
                self.model_fields_set.discard(field_name)

        return super().model_post_init(context)

    @classmethod
    def model_validate(
        cls: type[LFBaseModelT],
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
        ignore_extra: bool = True,
    ) -> LFBaseModelT:
        # Reference: https://github.com/pydantic/pydantic/discussions/7951#discussioncomment-11036526
        try:
            return super().model_validate(
                obj,
                strict=strict,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except pydantic.ValidationError as exc:
            if not ignore_extra:
                raise
            obj = deepcopy(obj)
            for err in exc.errors():
                if err["type"] != "extra_forbidden":
                    continue
                # Example:
                # ('nested_list', 0, 'nested_nested', 'nested_nested_extra_attr')
                *path, attr_name = err["loc"]
                item = obj
                for key in path:
                    # Key can be an integer index for lists, or a string for dicts.
                    item = item[key]
                item.pop(attr_name, None)

            return super().model_validate(
                obj,
                strict=strict,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )

    @classmethod
    def model_validate_json(
        cls: type[LFBaseModelT],
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
        ignore_extra: bool = True,
    ) -> LFBaseModelT:
        return cls.model_validate(
            json.loads(json_data),
            strict=strict,
            context=context,
            by_alias=by_alias,
            by_name=by_name,
            ignore_extra=ignore_extra,
        )

    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: (bool | Literal["none", "warn", "error"]) = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        """Same as the super method but has ``exclude_unset=True`` by default."""
        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: (bool | Literal["none", "warn", "error"]) = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
    ) -> str:
        """Same as the super method but has ``exclude_unset=True`` by default."""
        return super().model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    @pydantic.model_serializer(mode="wrap", when_used="json")
    def _serialize(self, nxt: pydantic.SerializerFunctionWrapHandler) -> dict[str, Any]:
        """A custom serializer that uses the actual value of ``SecretStr`` fields."""
        result = cast(dict[str, Any], nxt(self))
        for field_name in result.keys():
            value = getattr(self, field_name)
            if isinstance(value, pydantic.SecretStr):
                result[field_name] = value.get_secret_value()
        return result
