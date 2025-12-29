import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Annotated, Any, ClassVar, Generic, TypedDict, TypeVar, Union, cast

from msgspec import Meta, Struct, ValidationError, convert, defstruct
from msgspec import field as msgspec_field
from msgspec import json, msgpack


__all__ = (
    "Model",
    "ModelSchemaType",
    "ModelResponse",
    "MetaData",
    "Field",
    "FormProperties",
    "ModelFormProperties",
    "ModelValidationError",
    "create_model_type",
    "BaseTypeT",
    "TYPES",
    "ErrorCode",
    "ErrorData",
    "repr_",
    "from_repr",
    "FieldRepr",
    "ModelRepr",
    "encode_model",
    "decode_model",
)

TYPES: dict[str, type[Union["Field", "Model"]]] = {}  #: registry of all model and field types


@dataclass(slots=True, kw_only=True)
class FormProperties:
    """UI form properties."""

    has_feedback: bool = False
    placeholder: str | None = None
    disable_label: bool = False
    mark_required: bool = False
    disabled: bool = False
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class ModelFormProperties(FormProperties):
    """UI form properties for nested models."""

    display_frame: bool = True


@dataclass(slots=True, kw_only=True)
class MetaData:
    """Additional model / field meta-attributes."""

    form_properties: FormProperties = field(default_factory=FormProperties)


class ModelSchemaType(TypedDict):
    """Model UI schema for form objects."""

    _type: str
    type: str
    title: str
    schema: list[dict[str, Any]]
    ordering: list[str]
    meta: dict[str, Any]


@dataclass
class ModelResponse:
    """UI model schema data."""

    model: ModelSchemaType
    data: dict[str, Any] | None = field(default_factory=dict)


class FieldRepr(Struct, tag="field", tag_field="_type"):
    """Dictionary representation of a field.

    Can be used to reconstruct models and fields using :py:func:`~kaiju_models.bases.create_from_repr` function.
    """

    type: str
    properties: dict[str, Union["FieldRepr", "ModelRepr", Any]]


class _ModelField(Struct):
    id: str
    obj: Union["FieldRepr", "ModelRepr"]


class ModelRepr(Struct, tag="model", tag_field="_type"):
    """Dictionary representation of a model.

    Can be used to reconstruct models and fields using :py:func:`~kaiju_models.bases.create_from_repr` function.
    """

    type: str
    properties: dict[str, Union["FieldRepr", "ModelRepr", Any]]
    fields: list[_ModelField]


_encode: Callable[[...], bytes] = json.Encoder().encode
_encode_msgpack: Callable[[...], bytes] = msgpack.Encoder(uuid_format="bytes").encode
_model_decode: Callable[[bytes], ModelRepr] = msgpack.Decoder(type=ModelRepr).decode
_model_encode: Callable[[ModelRepr], bytes] = _encode_msgpack
_Fields = TypeVar("_Fields", bound="Model.Fields")


class ErrorCode(Enum):
    """Standard validation error codes."""

    UNKNOWN = "UNKNOWN"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_ENUM_VALUE = "INVALID_ENUM_VALUE"
    NUMBER_CONSTRAINT = "NUMBER_CONSTRAINT"
    LENGTH_CONSTRAINT = "LENGTH_CONSTRAINT"
    PATTERN_MISMATCH = "PATTERN_MISMATCH"


class ErrorData(TypedDict, total=False):
    """Error data object."""

    model: str
    """Model class name where error happened."""

    code: ErrorCode
    """Error type code."""

    field: str
    """Field name."""

    expected_type: str | None
    """Expected data type in this field."""

    provided_type: str | None
    """Provided data type."""

    operator: str | None
    """Comparison operator for constraint-related errors."""

    constraint: int | None
    """Constraint value for constraint-related errors."""

    pattern: str | None
    """Matching pattern for pattern-match errors."""

    value: str | None
    """Provided value."""


@dataclass(slots=True)
class ModelValidationError(ValidationError):
    """Model data validation error."""

    message: str = ""
    """Error message."""

    data: dict[str, Any] | ErrorData = field(default_factory=dict)
    """Additional error data such as field name, object name etc."""

    _operators = {">": "gt", "<": "lt", ">=": "ge", "<=": "le", "!=": "ne", "==": "eq"}

    # fmt: off
    _regex = re.compile(
        "^("
        "Invalid ("
        r"enum value '(?P<enum_value>.+)'|"  # enum
        r"(?P<fmt>[\w\s]+)"  # format
        ")|"
        r"Expected `(?P<expected_type>[\w\s|]+)`("  # expected type
        r", got `(?P<provided_type>[\w\s]+)`|"  # provided type
        r" (?P<op>[<>=!]+) (?P<constraint>\d+)|"  # num op and constraint
        r" of length (?P<l_op>[<>=!]+) (?P<l_constraint>\d+)|"  # length op and constraint
        r" matching regex '(?P<pattern>.+)'"  # regex constraint
        ")"
        ")"
        r" - at `\$\.(?P<field>[\w\[\]]+)`$"  # field and index
    )

    # fmt: on

    @classmethod
    def from_error_message(cls, model: type["Model"], msg: str, /) -> "ModelValidationError":
        """Create an error object from a msgspec error message."""
        error_data = ErrorData(code=ErrorCode.UNKNOWN, model=model.__name__)
        match = cls._regex.fullmatch(msg)
        if not match:
            return cls(msg, data=error_data)

        match_data = match.groupdict()
        error_data["field"] = match_data["field"]

        if match_data.get("enum_value") is not None:
            error_data["code"] = ErrorCode.INVALID_ENUM_VALUE
            error_data["value"] = match_data["enum_value"]
        elif match_data.get("fmt") is not None:
            error_data["code"] = ErrorCode.INVALID_FORMAT
        elif match_data.get("provided_type") is not None:
            error_data["code"] = ErrorCode.TYPE_MISMATCH
            error_data["expected_type"] = match_data["expected_type"]
            error_data["provided_type"] = match_data["provided_type"]
        elif match_data.get("pattern") is not None:
            error_data["code"] = ErrorCode.PATTERN_MISMATCH
            error_data["expected_type"] = match_data["expected_type"]
            error_data["pattern"] = match_data["pattern"]
        elif match_data.get("constraint") is not None:
            error_data["code"] = ErrorCode.NUMBER_CONSTRAINT
            error_data["expected_type"] = match_data["expected_type"]
            error_data["operator"] = cls._operators.get(match_data["op"])
            error_data["constraint"] = int(match_data["constraint"])
        elif match_data.get("l_constraint") is not None:
            error_data["code"] = ErrorCode.LENGTH_CONSTRAINT
            error_data["expected_type"] = match_data["expected_type"]
            error_data["operator"] = cls._operators.get(match_data["l_op"])
            error_data["constraint"] = int(match_data["l_constraint"])

        return cls(msg, data=error_data)


BaseTypeT = TypeVar("BaseTypeT", bound=Any)


class _Field(Generic[BaseTypeT]):
    __base_type__: type[BaseTypeT] = Any
    """Base type for this field.

    Class variable.
    """

    validate: Callable[[Any], BaseTypeT]
    """Optional validator function for this field to be called by its parent."""


@dataclass(slots=True)
class Field(_Field[BaseTypeT]):
    """Base field type."""

    __ui_type__: ClassVar[str] = "field"
    """UI object type."""

    title: str = None
    """Field short title."""

    description: str = None
    """Field description."""

    required: bool = None
    """Field is required."""

    default: BaseTypeT = None
    """Default value for this field."""

    ui_visible: bool = True
    """Is this field visible in UI schema."""

    meta: MetaData = field(default_factory=MetaData)
    """Additional field metadata."""

    __annotation__: type = field(init=False)
    """Field annotation (auto-generated)."""

    def __post_init__(self):
        self.__annotation__ = self._get_annotation()

    def __init_subclass__(cls, **kws) -> None:
        TYPES[cls.__name__] = cls

    def _get_annotation(self):
        annotation = Annotated[self.__class__.__base_type__, self._get_annotation_meta()]
        if self.required:
            return annotation
        return annotation | None

    def _get_annotation_meta(self):
        return Meta(title=self.title, description=self.description)

    def _validation_schema(self) -> dict[str, Any]:
        return {}

    def get_schema(self) -> dict[str, Any]:
        """Get UI schema for this object."""
        return {
            "_type": self.__class__.__name__,
            "type": self.__ui_type__,
            "required": self.required,
            "default": self.default,
            "title": self.title,
            "description": self.description,
            "meta": asdict(self.meta),  # noqa: ???
            "validation": self._validation_schema(),
        }


class Model(Field, Generic[_Fields]):
    """Base model class."""

    class Fields(Struct):
        """Description of model fields."""

        __validators__: ClassVar[list[tuple[str, Callable[[Any], Any]]]] = []
        __fields__: ClassVar[list[tuple[str, Field]]] = []

    __base_type__: type[_Fields]
    """Base type contains the actual structure type to use in validation / conversion.

    This parameter is auto-generated on class init.
    """

    __base_type_compact__ = type[_Fields]
    """Compact representation of the structure type for msgpack serializer."""

    __ui_type__: ClassVar[str] = "model"
    """UI object type."""

    __decode__: Callable[[bytes], _Fields]
    """JSON decode function for this model.

    This function is auto-generated on class init.
    """

    __decode_msgpack__: Callable[[bytes], _Fields]
    """Msgpack decode function for this model.

    This function is auto-generated on class init.
    """

    __annotation_compact__: type
    """Compact annotation for this model."""

    def __init__(self, *args, default=..., **kws) -> None:
        super().__init__(*args, default=msgspec_field(default_factory=self.__class__.__base_type__), **kws)
        self.__annotation_compact__ = self._get_annotation_compact()

    def _get_annotation_compact(self):
        annotation = Annotated[self.__class__.__base_type_compact__, self._get_annotation_meta()]
        if self.required:
            return annotation
        return annotation | None

    @classmethod
    def encode(cls, data, /) -> bytes:
        """Encode object to JSON using this model."""
        if type(data) is not cls.__base_type__:
            data = convert(data, type=cls.__base_type__, from_attributes=True)
        return _encode(data)

    @classmethod
    def decode(cls, data: bytes, /) -> _Fields:
        """Decode JSON data to a struct using this model."""
        try:
            data = cls.__decode__(data)
            if cls.Fields.__validators__:
                for key, validator in cls.Fields.__validators__:
                    setattr(data, key, validator(getattr(data, key)))
            return data
        except ModelValidationError as e:
            e.data['model'] = cls.__name__
            e.data['field'] = key  # noqa
            raise
        except ValidationError as e:
            raise ModelValidationError.from_error_message(cls, str(e)) from None

    @classmethod
    def encode_msgpack(cls, data, /) -> bytes:
        """Encode object to msgpack using this model."""
        if type(data) is not cls.__base_type_compact__:
            data = convert(data, type=cls.__base_type_compact__, from_attributes=True)
        return _encode_msgpack(data)

    @classmethod
    def decode_msgpack(cls, data: bytes, /) -> _Fields:
        """Decode msgpack data to a struct using this model."""
        try:
            data = cls.__decode_msgpack__(data)
            if cls.Fields.__validators__:
                for key, validator in cls.Fields.__validators__:
                    setattr(data, key, validator(getattr(data, key)))
            return data
        except ModelValidationError as e:
            e.data['model'] = cls.__name__
            e.data['field'] = key  # noqa
            raise
        except ValidationError as e:
            raise ModelValidationError.from_error_message(cls, str(e)) from None

    @classmethod
    def get_struct(cls, data: dict[str, Any] | object, /) -> _Fields:
        """Validate structured data and return a new `msgspec.Struct` object.

        :raises ModelValidationError: on invalid struct
        """
        from_attributes = not isinstance(data, dict)
        try:
            data = convert(data, cls.__base_type__, from_attributes=from_attributes, strict=False)
            if cls.Fields.__validators__:
                for key, validator in cls.Fields.__validators__:
                    setattr(data, key, validator(getattr(data, key)))
            return data
        except ModelValidationError as e:
            e.data['model'] = cls.__name__
            e.data['field'] = key  # noqa
            raise
        except ValidationError as e:
            raise ModelValidationError.from_error_message(cls, str(e)) from None

    def get_schema(self) -> ModelSchemaType:
        _schema = []
        for key, field_ in self.Fields.__fields__:
            if field_.ui_visible:
                _schema.append({"id": key, **field_.get_schema()})
        return ModelSchemaType(
            _type=self.__class__.__name__,
            type=self.__ui_type__,
            title=self.title,
            schema=_schema,
            meta=asdict(self.meta),  # noqa
            ordering=self.__base_type_compact__.__struct_fields__,
        )

    def __init_subclass__(cls, **kws) -> None:
        fields_, struct_fields, struct_compact_fields, validators = [], [], [], []

        for key in dir(cls.Fields):
            if not key.startswith('_'):
                if key not in cls.Fields.__struct_fields__:
                    raise TypeError(f'No field annotation specified for field `{key}` in model `{cls.__name__}`')

        for key, attr in zip(
            reversed(getattr(cls.Fields, "__struct_fields__", [])),
            reversed(getattr(cls.Fields, "__struct_defaults__", [])),
        ):
            if not isinstance(attr, Field):
                continue

            fields_.append((key, attr))
            if hasattr(attr, "validate"):
                validators.append((key, attr.validate))
            annotation_compact = attr.__annotation_compact__ if isinstance(attr, Model) else attr.__annotation__
            if attr.required:
                struct_fields.append((key, attr.__annotation__))
                struct_compact_fields.append((key, annotation_compact))
            else:
                struct_fields.insert(0, (key, attr.__annotation__, attr.default))
                struct_compact_fields.insert(0, (key, annotation_compact, attr.default))

        fields_.reverse()
        validators.reverse()
        struct_fields.reverse()
        struct_compact_fields.reverse()
        config = cls.Fields.__struct_config__
        struct = defstruct(
            f"{cls.__name__}Struct",
            tag=cls.__name__,
            tag_field="_type",
            fields=struct_fields,
            array_like=False,
            dict=False,
            gc=config.gc,
            frozen=config.frozen,
            cache_hash=config.cache_hash,
            order=config.order,
            omit_defaults=config.omit_defaults,
            eq=config.eq,
            forbid_unknown_fields=config.forbid_unknown_fields,
        )
        struct_compact = defstruct(
            f"{cls.__name__}StructCompact",
            tag=cls.__name__,
            tag_field="_type",
            fields=struct_compact_fields,
            array_like=True,
            omit_defaults=True,
            dict=False,
            gc=config.gc,
            frozen=config.frozen,
            cache_hash=config.cache_hash,
            order=config.order,
            eq=config.eq,
            forbid_unknown_fields=config.forbid_unknown_fields,
        )
        cls.Fields.__validators__ = validators
        setattr(cls.Fields, "__fields__", fields_)
        setattr(cls.Fields, "__validators__", validators)
        setattr(cls, "__base_type__", struct)
        setattr(cls, "__base_type_compact__", struct_compact)
        setattr(cls, "__decode__", json.Decoder(type=struct).decode)
        setattr(cls, "__decode_msgpack__", msgpack.Decoder(type=struct_compact).decode)
        TYPES[cls.__name__] = cls


def create_model_type(
    name: str, fields: list[tuple[str, Field]], base: type[Model] = Model, **properties
) -> type[Model]:
    """Create a model class dynamically from a list of fields.

    :param name: class name
    :param fields: list of tuples of (field name, field)
    :param base: base class
    :param properties: msgspec model properties, see `msgspec.defstruct` for detail
    """
    struct_fields = [(key, field_.__base_type__, field_) for key, field_ in fields]
    model_fields = defstruct(f"{name}Fields", fields=struct_fields, bases=(base.Fields,), **properties)
    model_type = type(name, (base,), {"Fields": model_fields})
    return cast(type[Model], model_type)


def repr_(obj: Field | Model, /) -> FieldRepr | ModelRepr:
    """Create a serializable representation of a model or field.

    You can use :py:func:`~kaiju_models.bases.from_repr` to convert it back to a normal model / field.
    """

    def _normalize(v: Any, /) -> Any:
        if isinstance(v, (list, tuple, set, frozenset)):
            return [_normalize(item) for item in v]
        elif isinstance(v, dict):
            return {key: _normalize(item) for key, item in v.items()}
        elif isinstance(v, (Field, Model)):
            return repr_(v)
        else:
            return v

    props = {}

    for init_attr in getattr(obj.__init__, "__annotations__", []):
        if init_attr.startswith("_") or init_attr in {"return", "kws", "kwargs", "args", "self"}:
            continue
        props[init_attr] = _normalize(getattr(obj, init_attr))

    if isinstance(obj, Model):
        fields_ = [_ModelField(id=key, obj=repr_(field_)) for key, field_ in obj.Fields.__fields__]
        return ModelRepr(type=obj.__class__.__name__, properties=props, fields=fields_)

    return FieldRepr(type=obj.__class__.__name__, properties=props)


def from_repr(  # pylint: disable=W0102
    data: FieldRepr | ModelRepr,
    /,
    name: str = None,
    *,
    types: dict[str, type[Field | Model]] = TYPES,  # noqa
    fallback_model_type: type[Model] = Model,
) -> Field | Model:
    """Create a model or field from its serialized representation.

    :param data: The serialized representation.
    :param name: Class name which is only used for new model types, by default the model type name is used.
    :param types: optional custom mapping of model and field data types onto their names
    :param fallback_model_type: which base model type to use if types dict doesn't have an expected model type
    """

    def _denormalize(v: Any, /) -> Any:
        if isinstance(v, (FieldRepr, ModelRepr)):
            return from_repr(v)
        elif isinstance(v, dict):
            if v.get("_type") == "field":
                return from_repr(convert(v, type=FieldRepr))
            elif v.get("_type") == "model":
                return from_repr(convert(v, type=ModelRepr))
            return {k: _denormalize(item) for k, item in v.items()}
        elif isinstance(v, (list, tuple, set, frozenset)):
            return [_denormalize(item) for item in v]
        else:
            return v

    props = _denormalize(data.properties)

    if isinstance(data, ModelRepr):
        type_ = types.get(data.type)
        if type_ is None:
            type_ = fallback_model_type
        fields_ = [(model_field.id, from_repr(model_field.obj)) for model_field in data.fields]
        name = name if name else data.type
        type_ = create_model_type(name, fields=fields_, base=type_)
        return type_(**props)

    type_ = types[data.type]
    return type_(**props)


def encode_model(model: Model, /) -> bytes:
    """Encode a model schema to bytes.

    Shortcut for repr + msgpack.encode"""
    return _model_encode(repr_(model))


def decode_model(  # pylint: disable=W0102
    data: bytes,
    /,
    name: str = None,
    *,
    types: dict[str, type[Field | Model]] = TYPES,  # noqa
) -> Field | Model:
    """Decode a model schema from bytes.

    Shortcut for msgpack.decode + from_repr.
    """
    return from_repr(_model_decode(data), name=name, types=types)
