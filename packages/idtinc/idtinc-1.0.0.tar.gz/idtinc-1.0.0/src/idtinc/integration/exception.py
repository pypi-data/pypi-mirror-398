import json
import logging

from django.core.exceptions import (EmptyResultSet, FieldDoesNotExist,
                                    FieldError, ImproperlyConfigured,
                                    MultipleObjectsReturned,
                                    ObjectDoesNotExist, PermissionDenied,
                                    SuspiciousOperation)
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import (DatabaseError, DataError, IntegrityError,
                       OperationalError, ProgrammingError)
from django.http import Http404
from rest_framework.exceptions import (APIException, AuthenticationFailed,
                                       MethodNotAllowed, NotAcceptable,
                                       NotAuthenticated, NotFound, ParseError)
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import Throttled, UnsupportedMediaType
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler

from idtinc.core.message import Msg
from idtinc.core.status import HttpStatus

from .response import APIResponse
from .validators import MessageError, ValidationDetailError

logger = logging.getLogger("exception")

_STATUS_MESSAGES = {
    HttpStatus.BAD_REQUEST.value: Msg.BAD_REQUEST,
    HttpStatus.UNAUTHORIZED.value: Msg.UNAUTHORIZED,
    HttpStatus.FORBIDDEN.value: Msg.FORBIDDEN,
    HttpStatus.NOT_FOUND.value: Msg.NOT_FOUND,
    HttpStatus.METHOD_NOT_ALLOWED.value: Msg.BAD_REQUEST,
    HttpStatus.NOT_ACCEPTABLE.value: Msg.BAD_REQUEST,
    HttpStatus.UNSUPPORTED_MEDIA_TYPE.value: Msg.BAD_REQUEST,
    HttpStatus.CONFLICT.value: Msg.CONFLICT,
    HttpStatus.TOO_MANY_REQUESTS.value: Msg.TOO_MANY_REQUESTS,
    HttpStatus.INTERNAL_SERVER_ERROR.value: Msg.INTERNAL_SERVER_ERROR,
    HttpStatus.BAD_GATEWAY.value: Msg.BAD_GATEWAY,
    HttpStatus.SERVICE_UNAVAILABLE.value: Msg.BAD_GATEWAY,
}


def get_error_message(status_code):
    return _STATUS_MESSAGES.get(status_code, Msg.BAD_REQUEST)


def flatten_validation_errors(errors):
    flattened = {}
    first_message = None

    def extract_errors(data, parent_key="", depth=0):
        nonlocal first_message

        if depth > 5:
            return str(data)

        if isinstance(data, str):
            if not first_message:
                first_message = data
            return data

        elif isinstance(data, list):
            messages = []
            for i, item in enumerate(data):
                if isinstance(item, str):
                    messages.append(item)
                    if not first_message:
                        first_message = item
                elif isinstance(item, dict):
                    nested_key = f"{parent_key}[{i}]" if parent_key else f"[{i}]"
                    extract_errors(item, nested_key, depth + 1)
                elif isinstance(item, list):
                    nested_key = f"{parent_key}[{i}]" if parent_key else f"[{i}]"
                    extract_errors(item, nested_key, depth + 1)
                else:
                    messages.append(str(item))
                    if not first_message:
                        first_message = str(item)
            return messages

        elif isinstance(data, dict):
            for key, value in data.items():
                if "__" in key and parent_key:
                    current_key = f"{parent_key}.{key}"
                elif parent_key:
                    current_key = f"{parent_key}.{key}"
                else:
                    current_key = key

                if isinstance(value, str):
                    flattened[current_key] = value
                    if not first_message:
                        first_message = value
                elif isinstance(value, list):
                    has_dicts = any(isinstance(item, dict) for item in value)
                    has_lists = any(isinstance(item, list) for item in value)
                    if has_dicts or has_lists:
                        extract_errors(value, current_key, depth + 1)
                    else:
                        if len(value) == 1 and isinstance(value[0], str):
                            flattened[current_key] = value[0]
                            if not first_message:
                                first_message = value[0]
                        else:
                            flattened[current_key] = value
                            if not first_message and value:
                                first_message = value[0] if isinstance(value[0], str) else str(value[0])
                elif isinstance(value, dict):
                    extract_errors(value, current_key, depth + 1)
                else:
                    flattened[current_key] = str(value)
                    if not first_message:
                        first_message = str(value)
            return flattened

        else:
            result = str(data)
            if not first_message:
                first_message = result
            return result

    if hasattr(errors, "detail"):
        result = extract_errors(errors.detail)
    elif hasattr(errors, "message_dict"):
        result = extract_errors(errors.message_dict)
    else:
        result = extract_errors(errors)

    if not isinstance(result, dict):
        flattened["detail"] = result

    return flattened, first_message


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    view = context.get("view")

    exception_info = {
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "request_path": request.path if request else "Unknown",
        "request_method": request.method if request else "Unknown",
        "view_name": view.__class__.__name__ if view else "Unknown",
        "error": True,
    }

    logger.error(
        f"{exception_info['request_path']} [{exception_info['request_method']}]",
        exc_info=True,
        extra=exception_info,
    )

    status, message = _get_status_and_message(exc, response)
    should_flatten = _should_flatten_errors(exc)

    if should_flatten and response:
        _flattened_errors, first_message = flatten_validation_errors(response.data)
        if first_message:
            message = first_message

    return APIResponse(data=None, message=message, success=False, status=status)


def _get_status_and_message(exc, response):
    status_code = (
        response.status_code
        if response
        else exc.status_code if hasattr(exc, "status_code") else HttpStatus.INTERNAL_SERVER_ERROR.value
    )

    if isinstance(exc, Http404):
        status = HttpStatus.NOT_FOUND
        message = _get_exception_message(exc, Msg.NOT_FOUND)

    elif isinstance(exc, (PermissionDenied, DRFPermissionDenied)):
        status = HttpStatus.FORBIDDEN
        message = _get_exception_message(exc, Msg.FORBIDDEN)

    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        status = HttpStatus.UNAUTHORIZED
        message = _get_exception_message(exc, Msg.UNAUTHORIZED)

    elif isinstance(exc, (DRFValidationError, DjangoValidationError, ValidationDetailError)):
        status = HttpStatus.BAD_REQUEST
        message = _get_exception_message(exc, Msg.VALUE_INVALID)

    elif isinstance(exc, ParseError):
        status = HttpStatus.BAD_REQUEST
        message = _get_exception_message(exc, Msg.BAD_REQUEST)

    elif isinstance(exc, NotFound):
        status = HttpStatus.NOT_FOUND
        message = _get_exception_message(exc, Msg.NOT_FOUND)

    elif isinstance(exc, MethodNotAllowed):
        status = HttpStatus.METHOD_NOT_ALLOWED
        message = Msg.BAD_REQUEST

    elif isinstance(exc, NotAcceptable):
        status = HttpStatus.NOT_ACCEPTABLE
        message = Msg.BAD_REQUEST

    elif isinstance(exc, UnsupportedMediaType):
        status = HttpStatus.UNSUPPORTED_MEDIA_TYPE
        message = Msg.BAD_REQUEST

    elif isinstance(exc, Throttled):
        status = HttpStatus.TOO_MANY_REQUESTS
        message = Msg.TOO_MANY_REQUESTS

    elif isinstance(exc, IntegrityError):
        status = HttpStatus.CONFLICT
        message = Msg.CONFLICT

    elif isinstance(exc, (DatabaseError, OperationalError, ProgrammingError, DataError)):
        status = HttpStatus.INTERNAL_SERVER_ERROR
        message = Msg.INTERNAL_SERVER_ERROR

    elif isinstance(exc, (ObjectDoesNotExist, FieldDoesNotExist, EmptyResultSet)):
        status = HttpStatus.NOT_FOUND
        message = _get_exception_message(exc, Msg.BAD_REQUEST)

    elif isinstance(exc, (MultipleObjectsReturned, FieldError)):
        status = HttpStatus.CONFLICT
        message = Msg.CONFLICT

    elif isinstance(exc, (SuspiciousOperation, ImproperlyConfigured)):
        status = HttpStatus.BAD_REQUEST
        message = _get_exception_message(exc, Msg.BAD_REQUEST)

    elif isinstance(exc, MessageError):
        status = HttpStatus(exc.status_code)
        message = _get_exception_message(exc, exc.detail)

    elif isinstance(exc, (json.JSONDecodeError, ValueError)):
        status = HttpStatus.BAD_REQUEST
        message = _get_exception_message(exc, Msg.BAD_REQUEST)

    elif isinstance(exc, APIException):
        status = HttpStatus(status_code)
        message = _get_exception_message(exc, get_error_message(status_code))

    else:
        status = HttpStatus(status_code)
        message = _get_exception_message(exc, get_error_message(status_code))

    return status, message


def _get_exception_message(exc, default_message):
    if hasattr(exc, "detail"):
        if isinstance(exc.detail, str) and exc.detail.strip():
            return exc.detail
        elif isinstance(exc.detail, (list, dict)) and exc.detail:
            try:
                _flattened, first_message = flatten_validation_errors(exc.detail)
                if first_message and first_message.strip():
                    return first_message
            except:
                pass
            if exc.detail:
                return str(exc.detail)

    if hasattr(exc, "message_dict"):
        if exc.message_dict:
            try:
                _flattened, first_message = flatten_validation_errors(exc.message_dict)
                if first_message and first_message.strip():
                    return first_message
            except:
                pass
            if exc.message_dict:
                return str(exc.message_dict)

    if hasattr(exc, "messages"):
        if exc.messages:
            message = str(exc.messages[0]) if exc.messages else None
            if message and message.strip():
                return message

    exc_str = str(exc)
    if exc_str and exc_str.strip():
        return exc_str

    return default_message


def _should_flatten_errors(exc):
    if isinstance(
        exc,
        (
            DRFValidationError,
            DjangoValidationError,
            ValidationDetailError,
            ParseError,
            AuthenticationFailed,
            NotAuthenticated,
            NotFound,
            MethodNotAllowed,
            NotAcceptable,
            UnsupportedMediaType,
            Throttled,
            MessageError,
        ),
    ):
        return True

    if hasattr(exc, "detail") and isinstance(exc.detail, (dict, list)):
        return True

    if hasattr(exc, "message_dict") and isinstance(exc.message_dict, dict):
        return True

    return False
