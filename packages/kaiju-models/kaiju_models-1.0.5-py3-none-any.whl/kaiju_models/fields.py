from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Literal, Union
from uuid import UUID

from msgspec import Meta

from kaiju_models.bases import BaseTypeT, Field, FormProperties, MetaData

__all__ = [
    "TextField",
    "StringField",
    "EnumField",
    "EnumFormProperties",
    "PasswordField",
    "ListField",
    "JsonMapField",
    "JsonListField",
    "IntegerField",
    "IntegerFormProperties",
    "EmailField",
    "DecimalField",
    "DecimalFormProperties",
    "DateTimeField",
    "DateField",
    "MixedListField",
    "BooleanField",
    "AnyOfField",
    "UUIDField",
    "ByteField",
    "SetField",
]


class BooleanField(Field[bool]):
    """Boolean value."""

    __base_type__ = bool
    __ui_type__ = "bool"


class DateField(Field[date]):
    """Date."""

    __base_type__ = date
    __ui_type__ = "date"


@dataclass(slots=True)
class DateTimeField(Field[datetime]):
    """Date and time."""

    __base_type__ = datetime
    __ui_type__ = "datetime"

    tz: bool = False

    def _get_annotation_meta(self):
        return Meta(title=self.title, description=self.description, tz=self.tz)

    def _validation_schema(self) -> dict[str, Any]:
        return {
            "tz": self.tz,
        }


@dataclass(slots=True, kw_only=True)
class IntegerFormProperties(FormProperties):
    """Integer field UI properties."""

    step: int = 1


@dataclass(slots=True)
class IntegerField(Field[int]):
    """Integer number."""

    __base_type__ = int
    __ui_type__ = "int"

    gt: int = None
    """Validation constraint: provided value must be greater than this number."""

    ge: int = None
    """Validation constraint: provided value must be greater or equal to this number."""

    lt: int = None
    """Validation constraint: provided value must be less than this number."""

    le: int = None
    """Validation constraint: provided value must be less or equal to this number."""

    multiple_of: int = None
    """Validation constraint: provided value must be divisible by this number."""

    meta: MetaData = field(default_factory=lambda: MetaData(form_properties=IntegerFormProperties()))
    """Additional field metadata."""

    def _get_annotation_meta(self):
        return Meta(
            gt=self.gt,
            ge=self.ge,
            lt=self.lt,
            le=self.le,
            multiple_of=self.multiple_of,
            description=self.description,
            title=self.title,
        )

    def _validation_schema(self) -> dict[str, Any]:
        return {
            "gt": self.gt,
            "ge": self.ge,
            "lt": self.lt,
            "le": self.le,
            "multiple_of": self.multiple_of,
        }


@dataclass(slots=True, kw_only=True)
class DecimalFormProperties(IntegerFormProperties):
    """Decimal field UI properties."""

    step: Decimal = Decimal("0.1")


@dataclass(slots=True)
class DecimalField(IntegerField[Decimal]):
    """Decimal number."""

    __base_type__ = Decimal
    __ui_type__ = "decimal"

    multiple_of: Decimal = None
    meta: MetaData = field(default_factory=lambda: MetaData(form_properties=DecimalFormProperties()))


@dataclass(slots=True)
class JsonMapField(Field[dict[str, Any]]):
    """Dictionary field."""

    __base_type__ = dict[str, Any]
    __ui_type__ = "json_map"

    min_length: int = None
    """Validation constraint: provided number of properties must be larger or equal to this number."""

    max_length: int = None
    """Validation constraint: provided number of properties must be smaller or equal to this number."""

    default: dict[str, Any] = field(default_factory=dict, init=False)

    def _get_annotation_meta(self):
        return Meta(
            min_length=self.min_length,
            max_length=self.max_length,
            title=self.title,
            description=self.description,
        )

    def _validation_schema(self):
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
        }


@dataclass(slots=True)
class JsonListField(Field[tuple]):
    """Unstructured list field."""

    __base_type__ = tuple
    __ui_type__ = "json_list"

    min_length: int = None
    """Validation constraint: provided list length must be larger or equal to this number."""

    max_length: int = None
    """Validation constraint: provided list length must be smaller or equal to this number."""

    default: list = field(default_factory=tuple, init=False)

    def _get_annotation_meta(self):
        return Meta(
            min_length=self.min_length,
            max_length=self.max_length,
            title=self.title,
            description=self.description,
        )

    def _validation_schema(self):
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
        }


class ListField(Field[tuple]):
    """List of fixed type values."""

    __base_type__ = tuple
    __ui_type__ = "list"
    __slots__ = ("field", "min_length", "max_length")

    min_length: int
    """Validation constraint: provided list length must be larger or equal to this number."""

    max_length: int
    """Validation constraint: provided list length must be smaller or equal to this number."""

    def __init__(self, model: Field, *args, min_length: int = None, max_length: int = None, **kws: Any) -> None:
        self.model = model
        self.min_length = min_length
        self.max_length = max_length
        super().__init__(*args, default=tuple(), **kws)

    def _get_annotation(self) -> type:
        return Annotated[self.__base_type__[self.model.__annotation__, ...], self._get_annotation_meta()]

    def _get_annotation_meta(self):
        return Meta(
            min_length=self.min_length, max_length=self.max_length, title=self.title, description=self.description
        )

    def _validation_schema(self):
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
        }

    def get_schema(self) -> dict[str, Any]:
        return {
            **Field.get_schema(self),
            "field": self.model.get_schema(),
        }


class SetField(ListField[set]):
    """Unordered set of values."""

    __base_type__ = set
    __ui_type__ = "set"

    def _get_annotation(self) -> type:
        return Annotated[self.__base_type__[self.model.__annotation__], self._get_annotation_meta()]


class AnyOfField(Field[Any]):
    """Multi-type value."""

    __slots__ = ("models",)
    __ui_type__ = "any_of"

    def __init__(self, models: Collection[Field], *args, **kws) -> None:
        self.models = models
        super().__init__(*args, **kws)

    def _get_annotation(self) -> type:
        model_types = [type(m).__base_type__ for m in self.models]
        return Annotated[Union[*model_types], self._get_annotation_meta()]

    def get_schema(self) -> dict[str, Any]:
        schema = super().get_schema()
        return {**schema, "models": [_model.get_schema() for _model in self.models]}


class MixedListField(Field[tuple]):
    """List of multi-type values."""

    __slots__ = ("models", "min_length", "max_length")
    __base_type__ = tuple
    __ui_type__ = "mixed_list"

    min_length: int
    """Validation constraint: provided list length must be larger or equal to this number."""

    max_length: int
    """Validation constraint: provided list length must be smaller or equal to this number."""

    def __init__(
            self, models: Collection[Field], *args, min_length: int = None, max_length: int = None, **kws: Any
    ) -> None:
        self.models = models
        self.min_length = min_length
        self.max_length = max_length
        super().__init__(*args, default=tuple(), **kws)

    def _get_annotation(self) -> type:
        model_types = [type(m).__base_type__ for m in self.models]
        return Annotated[self.__base_type__[Union[*model_types], ...], self._get_annotation_meta()]

    def _get_annotation_meta(self):
        return Meta(
            min_length=self.min_length, max_length=self.max_length, title=self.title, description=self.description
        )

    def get_schema(self) -> dict[str, Any]:
        schema = super().get_schema()
        return {**schema, "models": [_model.get_schema() for _model in self.models]}


@dataclass(slots=True, kw_only=True)
class EnumFormProperties(FormProperties):
    """Select value options."""

    option_title: dict[str | int | float, str] = field(default_factory=dict)
    vertical: bool = False


class EnumField(Field[BaseTypeT]):
    """Select value."""

    __slots__ = ("options", '_options')
    __ui_type__ = "enum"

    options: list[BaseTypeT]
    """Validation constraint: list of possible values."""

    def __init__(self, options: list[BaseTypeT] | type[Enum], *args, meta=None, **kws: Any) -> None:
        if meta is None:
            meta = MetaData(form_properties=EnumFormProperties())
        if isinstance(options, list):
            self.options = self._options = options
        else:
            self.options = list(options.__members__.values())
            self._options = options
        super().__init__(*args, meta=meta, **kws)

    def _get_annotation(self) -> type:
        if isinstance(self._options, list):
            return Annotated[Literal[*self.options], self._get_annotation_meta()]  # noqa: python bug?
        return Annotated[self._options, self._get_annotation_meta()]

    def get_schema(self) -> dict[str, Any]:
        return {**Field.get_schema(self), "options": self.options}


class UUIDField(Field[UUID]):
    """UUID field."""

    __base_type__ = UUID
    __ui_type__ = "uuid"


class ByteField(Field[UUID]):
    """Byte field."""

    __base_type__ = bytes
    __ui_type__ = "bytes"


@dataclass(slots=True)
class StringField(Field[str]):
    """Normal string."""

    __base_type__ = str
    __ui_type__ = "str"

    min_length: int = None
    """Validation constraint: provided string length must be larger or equal to this number."""

    max_length: int = None
    """Validation constraint: provided string length must be smaller or equal to this number."""

    pattern: str = None
    """Validation constraint: provided string must match this regular expression."""

    pattern_error_text: str = None

    def _get_annotation_meta(self):
        return Meta(
            min_length=self.min_length,
            max_length=self.max_length,
            pattern=self.pattern,
            title=self.title,
            description=self.description,
        )

    def _validation_schema(self):
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
            "pattern": self.pattern,
            "pattern_error_text": self.pattern_error_text,
        }


@dataclass(slots=True)
class EmailField(StringField):
    """Email string."""

    __ui_type__ = "email"
    pattern: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    pattern_error_text = "Invalid email"


@dataclass(slots=True)
class PasswordField(StringField):
    """Password string."""

    __ui_type__ = "password"


@dataclass(slots=True)
class TextField(StringField):
    """Formatted text."""

    __ui_type__ = "text"
