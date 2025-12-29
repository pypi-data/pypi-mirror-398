import json
import re

from django_currentuser.middleware import get_current_user
from rest_framework import exceptions, serializers

from .helpers.query import (get_choice_value, get_choices_dict,
                            get_choices_label, get_choices_value,
                            get_storage_url)


class ChoiceField(serializers.ChoiceField):
    def to_representation(self, value):
        if choice_value := get_choice_value(self.choices, value):
            return get_choices_dict(choice_value)
        return None


class ChoiceLabelField(serializers.ChoiceField):
    def to_representation(self, value):
        if choice_value := get_choice_value(self.choices, value):
            return get_choices_label(choice_value)
        return None


class ChoiceValueField(serializers.ChoiceField):
    def to_representation(self, value):
        if choice_value := get_choice_value(self.choices, value):
            return get_choices_value(choice_value)
        return None


class CoordinatesField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("error_messages", {})
        kwargs["error_messages"].update(
            {
                "invalid_format": 'Coordinates must be in format "lat,lng" or "lat,lng;lat,lng;..."',
                "invalid_coords": "Invalid coordinate format. Latitude(-90, 90), Longitude(-180, 180)",
                "invalid_latitude": "Invalid latitude format (-90, 90)",
                "invalid_longitude": "Invalid longitude format (-180, 180)",
            }
        )
        super().__init__(**kwargs)

    def to_internal_value(self, value):
        value = super().to_internal_value(value)

        pattern = r"^(-?\d+(\.\d+)?),(-?\d+(\.\d+)?)(?:;(-?\d+(\.\d+)?),(-?\d+(\.\d+)?))*$"
        if not re.match(pattern, value):
            self.fail("invalid_format")

        coord_pairs = value.split(";")
        for pair in coord_pairs:
            try:
                lat, lng = map(float, pair.split(","))
            except ValueError:
                self.fail("invalid_format")

            if not (-90 <= lat <= 90):
                self.fail("invalid_latitude")

            if not (-180 <= lng <= 180):
                self.fail("invalid_longitude")

        return tuple(tuple(map(float, pair.split(","))) for pair in coord_pairs)

    def to_representation(self, value):
        return value


class BaseModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        model_class = self.Meta.model

        for field_name, field in self.fields.items():
            try:
                model_field = model_class._meta.get_field(field_name)

                if hasattr(model_field, "error_messages") and model_field.error_messages:
                    field.error_messages.update(model_field.error_messages)
            except Exception:
                continue

    @property
    def currentuser(self):
        return get_current_user()

    def to_internal_value(self, data):
        json_fields = getattr(self.Meta, "json_fields", None)

        if not json_fields:
            return super().to_internal_value(data)

        if not isinstance(json_fields, (list, tuple)):
            raise exceptions.APIException("json_fields must be a list or tuple")

        is_form_data = self.__is_form_data(data)

        if not is_form_data:
            return super().to_internal_value(data)

        cleaned_data = {}
        for key, val in data.items():
            field = self.fields.get(key)
            if key in json_fields:
                if isinstance(val, str):
                    try:
                        cleaned_data[key] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        raise exceptions.APIException(f"Field {key} is not a valid JSON")
                else:
                    cleaned_data[key] = val
            elif field is not None and isinstance(val, str):
                is_null = val.strip().lower() in ["null", "none", "undefined", ""]
                is_allow_null = getattr(field, "allow_null", False)
                is_allow_blank = getattr(field, "allow_blank", False)
                if is_null and (is_allow_null or is_allow_blank):
                    cleaned_data[key] = None
                else:
                    cleaned_data[key] = val
            else:
                cleaned_data[key] = val

        internal_value = super().to_internal_value(cleaned_data)

        for field_name in json_fields:
            if field_name in cleaned_data:
                try:
                    internal_value[field_name] = cleaned_data[field_name]
                    if isinstance(self.fields[field_name], serializers.BaseSerializer):
                        serializer = self.fields[field_name]
                        serializer.initial_data = internal_value[field_name]
                        serializer.is_valid(raise_exception=True)
                except serializers.ValidationError as e:
                    error_dict = {}
                    if isinstance(e.detail, list):
                        for index, detail in enumerate(e.detail):
                            for k, v in detail.items():
                                error_dict[f"{index}__{k}"] = v
                    elif isinstance(e.detail, dict):
                        error_dict = e.detail
                    raise serializers.ValidationError(error_dict)

        return internal_value

    def __is_form_data(self, data):
        if not data:
            return False

        for key, val in data.items():
            if isinstance(val, str):
                try:
                    json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    continue
                else:
                    return False
            elif isinstance(val, (dict, list)):
                return False

        return True

    def get_fields(self):
        fields = super().get_fields()
        exclude_defaults = ("is_deleted", "deleted_at", "deleted_by")
        exclude_fields = [*exclude_defaults, *getattr(self.Meta, "exclude_fields", [])]
        if getattr(self.Meta, "hidden_password", True):
            exclude_fields.append("password")

        for field in exclude_fields:
            if field in fields:
                fields.pop(field)

        return fields

    def get_storage_url(self, name):
        return get_storage_url(name)
