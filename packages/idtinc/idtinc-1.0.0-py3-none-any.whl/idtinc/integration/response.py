from typing import Any, Dict, List, Tuple, Union

from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response

from idtinc.core.message import Msg
from idtinc.core.status import HttpStatus

_STATUS_CODE_MAP = {
    200: 0,
    201: 11,
    204: 24,
    400: 40,
    401: 41,
    403: 43,
    404: 44,
    405: 45,
    406: 46,
    409: 49,
    500: 50,
    501: 51,
    502: 52,
    503: 53,
    504: 54,
    509: 59,
}


def map_status_code(status_code: int) -> int:
    return _STATUS_CODE_MAP.get(status_code, 40)


class BaseAPIResponse:
    _message_cache = {}
    _max_cache_size = 1000

    def build_response(
        self,
        data: Any = None,
        message: str = None,
        success: bool = None,
        status: Union[HttpStatus, int] = HttpStatus.OK,
        errors: Union[List, Tuple, Dict, None] = None,
        metadata: Dict = None,
    ) -> Dict:
        if isinstance(status, int):
            status = HttpStatus(status)

        if success is None:
            success = HttpStatus.is_success(status.value)

        if not message:
            cache_key = status.name.upper()
            if cache_key not in self._message_cache:
                if len(self._message_cache) >= self._max_cache_size:
                    self._message_cache.clear()
                try:
                    self._message_cache[cache_key] = getattr(Msg, cache_key, "")
                except AttributeError:
                    self._message_cache[cache_key] = Msg.OK if success else Msg.BAD_REQUEST

            message = self._message_cache[cache_key]

        response_structure = {
            "code": map_status_code(status.value),
            "status": status.value,
            "success": success,
            "status_text": status.name,
            "message": message,
            "data": data,
            "metadata": metadata,
        }
        
        from django.conf import settings
        if errors is not None and getattr(settings, 'DEBUG', True):
            response_structure["errors"] = errors

        return response_structure


class APIResponse(Response, BaseAPIResponse):
    def __init__(
        self,
        data: Any = None,
        message: str = None,
        success: bool = None,
        http_status: Union[HttpStatus, int] = None,
        status: Union[HttpStatus, int] = HttpStatus.OK,
        errors: Union[List, Tuple, Dict, None] = None,
        metadata: Dict = None,
        **kwargs,
    ):
        response_data = self.build_response(data, message, success, status, errors, metadata)

        if not http_status:
            http_status = response_data["status"]

        if isinstance(http_status, int):
            http_status = HttpStatus(http_status)

        super().__init__(data=response_data, status=http_status.value, **kwargs)


class JsonAPIResponse(JsonResponse, BaseAPIResponse):
    def __init__(
        self,
        data: Any = None,
        message: str = None,
        success: bool = None,
        status: Union[HttpStatus, int] = HttpStatus.OK,
        errors: Union[List, Tuple, Dict, None] = None,
        metadata: Dict = None,
        **kwargs,
    ):
        if not message:
            status_name = status.name if isinstance(status, HttpStatus) else "ok"
            message = getattr(Msg, status_name.upper(), "")

        response_data = self.build_response(data, message, success, status, errors, metadata)
        super().__init__(data=response_data, status=response_data["status"], **kwargs)
