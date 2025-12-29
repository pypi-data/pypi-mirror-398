from typing import Any, Dict, Optional, Type, TypeVar, Union, overload

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .model_errors import ModelError

T = TypeVar("T", bound=Union[models.Field, serializers.Field])


class BaseFieldParams:
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    max_value: Optional[Union[int, float]] = None
    min_value: Optional[Union[int, float]] = None
    required: Optional[bool] = None
    default: Any = None
    help_text: Optional[str] = None
    error_messages: Optional[Dict[str, str]] = None


class ModelFieldParams(BaseFieldParams):
    verbose_name: Optional[str] = None
    null: Optional[bool] = None
    blank: Optional[bool] = None
    unique: Optional[bool] = None
    db_index: Optional[bool] = None
    choices: Optional[list] = None


class SerializerFieldParams(BaseFieldParams):
    label: Optional[str] = None
    allow_blank: Optional[bool] = None
    allow_null: Optional[bool] = None
    read_only: Optional[bool] = None
    write_only: Optional[bool] = None
    source: Optional[str] = None


FIELD_TYPE_MAPPING = {
    models.CharField: "char",
    models.TextField: "text",
    models.EmailField: "email",
    models.URLField: "url",
    models.IntegerField: "integer",
    models.BigIntegerField: "big_integer",
    models.SmallIntegerField: "small_integer",
    models.PositiveIntegerField: "positive_integer",
    models.PositiveSmallIntegerField: "positive_small_integer",
    models.FloatField: "float",
    models.DecimalField: "decimal",
    models.BooleanField: "boolean",
    models.DateField: "date",
    models.TimeField: "time",
    models.DateTimeField: "datetime",
    models.JSONField: "json",
    models.BinaryField: "binary",
    models.ForeignKey: "foreign_key",
    models.OneToOneField: "one_to_one",
    models.ManyToManyField: "many_to_many",
    serializers.CharField: "char",
    serializers.EmailField: "email",
    serializers.URLField: "url",
    serializers.IntegerField: "integer",
    serializers.FloatField: "float",
    serializers.DecimalField: "decimal",
    serializers.BooleanField: "boolean",
    serializers.DateField: "date",
    serializers.TimeField: "time",
    serializers.DateTimeField: "datetime",
    serializers.JSONField: "json",
    serializers.ChoiceField: "choice",
    serializers.MultipleChoiceField: "multiple_choice",
    serializers.FileField: "file",
    serializers.ImageField: "image",
    serializers.HyperlinkedIdentityField: "url",
    serializers.HyperlinkedRelatedField: "url",
    serializers.SlugRelatedField: "char",
    serializers.StringRelatedField: "char",
    serializers.PrimaryKeyRelatedField: "foreign_key",
    serializers.ManyRelatedField: "many_to_many",
}

FIELD_ERROR_MESSAGES = {
    "char": ["required", "blank", "null", "invalid", "unique", "invalid_choice"],
    "text": ["required", "blank", "null", "invalid", "unique", "invalid_choice"],
    "email": ["required", "blank", "null", "invalid", "unique"],
    "url": ["required", "blank", "null", "invalid", "unique"],
    "integer": ["required", "blank", "null", "invalid"],
    "big_integer": ["required", "blank", "null", "invalid"],
    "small_integer": ["required", "blank", "null", "invalid"],
    "positive_integer": ["required", "blank", "null", "invalid"],
    "positive_small_integer": ["required", "blank", "null", "invalid"],
    "float": ["required", "blank", "null", "invalid"],
    "decimal": ["required", "blank", "null", "invalid"],
    "boolean": ["required", "null", "invalid"],
    "date": ["required", "blank", "null", "invalid"],
    "time": ["required", "blank", "null", "invalid"],
    "datetime": ["required", "blank", "null", "invalid"],
    "json": ["required", "blank", "null", "invalid"],
    "binary": ["required", "blank", "null", "invalid"],
    "foreign_key": ["required", "null", "invalid", "does_not_exist"],
    "one_to_one": ["required", "null", "invalid", "does_not_exist", "unique"],
    "many_to_many": ["required", "blank", "null", "invalid", "invalid_choice"],
    "choice": ["required", "invalid_choice"],
    "multiple_choice": ["required", "invalid_choice"],
    "file": ["required", "invalid"],
    "image": ["required", "invalid"],
}


@overload
def extra_fields(
    field_class: Type[models.CharField],
    verbose_name: str,
    *,
    max_length: Optional[int] = None,
    min_length: Optional[int] = None,
    null: Optional[bool] = None,
    blank: Optional[bool] = None,
    unique: Optional[bool] = None,
    db_index: Optional[bool] = None,
    choices: Optional[list] = None,
    default: Any = None,
    help_text: Optional[str] = None,
    error_messages: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> models.CharField: ...


@overload
def extra_fields(
    field_class: Type[models.EmailField],
    verbose_name: str,
    *,
    max_length: Optional[int] = None,
    null: Optional[bool] = None,
    blank: Optional[bool] = None,
    unique: Optional[bool] = None,
    db_index: Optional[bool] = None,
    default: Any = None,
    help_text: Optional[str] = None,
    error_messages: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> models.EmailField: ...


@overload
def extra_fields(
    field_class: Type[models.IntegerField],
    verbose_name: str,
    *,
    max_value: Optional[int] = None,
    min_value: Optional[int] = None,
    null: Optional[bool] = None,
    blank: Optional[bool] = None,
    unique: Optional[bool] = None,
    db_index: Optional[bool] = None,
    default: Any = None,
    help_text: Optional[str] = None,
    error_messages: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> models.IntegerField: ...


@overload
def extra_fields(
    field_class: Type[serializers.CharField],
    verbose_name: str,
    *,
    max_length: Optional[int] = None,
    min_length: Optional[int] = None,
    allow_blank: Optional[bool] = None,
    allow_null: Optional[bool] = None,
    required: Optional[bool] = None,
    read_only: Optional[bool] = None,
    write_only: Optional[bool] = None,
    default: Any = None,
    source: Optional[str] = None,
    error_messages: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> serializers.CharField: ...


@overload
def extra_fields(
    field_class: Type[serializers.EmailField],
    verbose_name: str,
    *,
    max_length: Optional[int] = None,
    allow_blank: Optional[bool] = None,
    allow_null: Optional[bool] = None,
    required: Optional[bool] = None,
    read_only: Optional[bool] = None,
    write_only: Optional[bool] = None,
    default: Any = None,
    source: Optional[str] = None,
    error_messages: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> serializers.EmailField: ...


@overload
def extra_fields(
    field_class: Type[serializers.IntegerField],
    verbose_name: str,
    *,
    max_value: Optional[int] = None,
    min_value: Optional[int] = None,
    allow_null: Optional[bool] = None,
    required: Optional[bool] = None,
    read_only: Optional[bool] = None,
    write_only: Optional[bool] = None,
    default: Any = None,
    source: Optional[str] = None,
    error_messages: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> serializers.IntegerField: ...


@overload
def extra_fields(field_class: Type[T], verbose_name: str, **kwargs: Any) -> T: ...


def extra_fields(field_class: Type[T], verbose_name: str, **kwargs: Any) -> T:
    field_type = FIELD_TYPE_MAPPING.get(field_class, "char")
    match_field_error_messages = FIELD_ERROR_MESSAGES.get(field_type, ["required", "blank", "null", "invalid"])

    is_model_field = hasattr(field_class, "_meta") or "django.db.models" in str(field_class.__module__)

    field_class_value = {**kwargs}
    if is_model_field:
        field_class_value["verbose_name"] = verbose_name
    else:
        field_class_value["label"] = verbose_name

    verbose_name_lower = verbose_name.lower()

    error_messages = {
        ModelError.REQUIRED: _(f"Please enter {verbose_name_lower}"),
        ModelError.BLANK: _(f"Please enter {verbose_name_lower}"),
        ModelError.NULL: _(f"Please enter {verbose_name_lower}"),
        ModelError.INVALID: _(f"The {verbose_name_lower} information is invalid"),
        ModelError.UNIQUE: _(f"The {verbose_name_lower} information already exists in the system"),
        ModelError.INVALID_CHOICE: _(f"The {verbose_name_lower} choice is invalid"),
        ModelError.DOES_NOT_EXIST: _(f"The {verbose_name_lower} information does not exist in the system"),
        ModelError.INVALID_FORMAT: _(f"The {verbose_name_lower} format is invalid"),
        ModelError.INVALID_EMAIL: _(f"Invalid email address"),
        ModelError.INVALID_URL: _(f"Invalid URL address"),
        ModelError.INVALID_DECIMAL: _(f"{verbose_name} must be a decimal number"),
        ModelError.INVALID_INTEGER: _(f"{verbose_name} must be an integer"),
        ModelError.INVALID_FLOAT: _(f"{verbose_name} must be a real number"),
        ModelError.INVALID_BOOLEAN: _(f'{verbose_name} only allows "true" or "false"'),
        ModelError.INVALID_DATE: _(f"{verbose_name} has incorrect format"),
        ModelError.INVALID_TIME: _(f"{verbose_name} has incorrect format"),
        ModelError.INVALID_DATETIME: _(f"{verbose_name} has incorrect format"),
        ModelError.INVALID_JSON: _(f"{verbose_name} must be JSON"),
        ModelError.INVALID_BINARY: _(f"{verbose_name} must be binary data"),
    }

    if max_length := kwargs.get("max_length"):
        error_messages[ModelError.MAX_LENGTH] = _(f"{verbose_name} allows maximum {max_length} characters")

    if min_length := kwargs.get("min_length"):
        error_messages[ModelError.MIN_LENGTH] = _(f"{verbose_name} must have minimum {min_length} characters")

    if max_value := kwargs.get("max_value"):
        error_messages[ModelError.MAX_VALUE] = _(f"The value of {verbose_name_lower} cannot exceed {max_value}")

    if min_value := kwargs.get("min_value"):
        error_messages[ModelError.MIN_VALUE] = _(f"The value of {verbose_name_lower} must be at least {min_value}")

    field_class_value["error_messages"] = field_class_value.get("error_messages")

    if not field_class_value["error_messages"] or not isinstance(field_class_value["error_messages"], dict):
        field_class_value["error_messages"] = {}

    for field_key, field_message in error_messages.items():
        if field_key in match_field_error_messages:
            field_class_value["error_messages"][field_key] = field_message

    return field_class(**field_class_value)
