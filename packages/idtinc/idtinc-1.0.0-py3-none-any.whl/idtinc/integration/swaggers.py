from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi

import idtinc.integration.helpers.string as StringHelper


def get_params(
    field: str, openapi_type: str, format: str = None, required: bool = False, description: str = None, **kwargs
):
    description = description or StringHelper.capitalize_first_letter(" ".join(field.split("_")))

    mapping_openapi_type = {
        "object": openapi.TYPE_OBJECT,
        "string": openapi.TYPE_STRING,
        "number": openapi.TYPE_NUMBER,
        "integer": openapi.TYPE_INTEGER,
        "boolean": openapi.TYPE_BOOLEAN,
        "array": openapi.TYPE_ARRAY,
        "file": openapi.TYPE_FILE,
    }

    if openapi_type not in mapping_openapi_type.keys():
        raise ValueError(_(f"{openapi_type} not in {list(mapping_openapi_type.keys())}"))

    return openapi.Parameter(
        name=field,
        in_=openapi.IN_QUERY,
        type=mapping_openapi_type[openapi_type],
        description=description,
        required=required,
        format=format,
        **kwargs,
    )


class SwaggerType:
    TYPE_OBJECT = "object"
    TYPE_STRING = "string"
    TYPE_NUMBER = "number"
    TYPE_INTEGER = "integer"
    TYPE_BOOLEAN = "boolean"
    TYPE_ARRAY = "array"
    TYPE_FILE = "file"

    FORMAT_DATE = "date"
    FORMAT_DATETIME = "date-time"
    FORMAT_PASSWORD = "password"
    FORMAT_BINARY = "binary"
    FORMAT_BASE64 = "bytes"
    FORMAT_FLOAT = "float"
    FORMAT_DOUBLE = "double"
    FORMAT_INT32 = "int32"
    FORMAT_INT64 = "int64"

    FORMAT_EMAIL = "email"
    FORMAT_IPV4 = "ipv4"
    FORMAT_IPV6 = "ipv6"
    FORMAT_URI = "uri"

    FORMAT_UUID = "uuid"
    FORMAT_SLUG = "slug"
    FORMAT_DECIMAL = "decimal"

    IN_BODY = "body"
    IN_PATH = "path"
    IN_QUERY = "query"
    IN_FORM = "formData"
    IN_HEADER = "header"

    SCHEMA_DEFINITIONS = "definitions"


class QueryParam(SwaggerType):
    getParam = staticmethod(get_params)

    @staticmethod
    def getPage(required: bool = False, openapi_type: str = SwaggerType.TYPE_INTEGER, **kwargs):
        return get_params(field="page", description=_("Trang"), required=required, openapi_type=openapi_type, **kwargs)

    @staticmethod
    def getLimit(required: bool = False, openapi_type: str = SwaggerType.TYPE_INTEGER, **kwargs):
        return get_params(
            field="limit", description=_("Giới hạn"), required=required, openapi_type=openapi_type, **kwargs
        )

    @staticmethod
    def getSearch(required: bool = False, openapi_type: str = SwaggerType.TYPE_STRING, **kwargs):
        return get_params(
            field="search", description=_("Tìm kiếm"), required=required, openapi_type=openapi_type, **kwargs
        )

    @staticmethod
    def getId(required: bool = False, openapi_type: str = SwaggerType.TYPE_INTEGER, **kwargs):
        return get_params(field="id", description=_("ID"), required=required, openapi_type=openapi_type, **kwargs)

    @staticmethod
    def getStartDate(required: bool = False, openapi_type: str = SwaggerType.TYPE_STRING, **kwargs):
        return get_params(
            field="start_date",
            description=_("Ngày bắt đầu"),
            required=required,
            openapi_type=openapi_type,
            format=SwaggerType.FORMAT_DATE,
            **kwargs,
        )

    @staticmethod
    def getEndDate(required: bool = False, openapi_type: str = SwaggerType.TYPE_STRING, **kwargs):
        return get_params(
            field="end_date",
            description=_("Ngày kết thúc"),
            required=required,
            openapi_type=openapi_type,
            format=SwaggerType.FORMAT_DATE,
            **kwargs,
        )

    @staticmethod
    def getOrdering(required: bool = False, openapi_type: str = SwaggerType.TYPE_NUMBER, **kwargs):
        return get_params(
            field="ordering", description=_("Sắp xếp"), required=required, openapi_type=openapi_type, **kwargs
        )

    @staticmethod
    def getDate(required: bool = False, openapi_type: str = SwaggerType.TYPE_STRING, **kwargs):
        return get_params(
            field="date",
            description=_("Ngày"),
            required=required,
            openapi_type=openapi_type,
            format=SwaggerType.FORMAT_DATE,
            **kwargs,
        )

    @staticmethod
    def getAccessToken(required: bool = True, openapi_type: str = SwaggerType.TYPE_STRING, **kwargs):
        return get_params(
            field="access_token",
            description=_("Access token"),
            required=required,
            openapi_type=openapi_type,
            **kwargs,
        )

    @staticmethod
    def getRefreshToken(required: bool = True, openapi_type: str = SwaggerType.TYPE_STRING, **kwargs):
        return get_params(
            field="refresh_token",
            description=_("Refresh token"),
            required=required,
            openapi_type=openapi_type,
            **kwargs,
        )
