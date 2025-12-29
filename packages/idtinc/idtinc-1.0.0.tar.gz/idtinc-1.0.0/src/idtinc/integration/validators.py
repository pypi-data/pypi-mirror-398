from typing import Union

from rest_framework.exceptions import APIException, ValidationError

from idtinc.core.message import Msg
from idtinc.core.status import HttpStatus


class MessageError(APIException):

    status_code = HttpStatus.BAD_REQUEST.value
    default_code = HttpStatus.BAD_REQUEST.name
    default_detail = Msg.BAD_REQUEST

    def __init__(self, detail: Union[Msg, str] = None, status_code: int = None):
        _detail_tmp = detail

        if status_code is not None:
            self.status_code = status_code

        if isinstance(_detail_tmp, str):
            message_field = _detail_tmp.upper()
            if hasattr(Msg, message_field):
                _detail_tmp = Msg(message_field)

        if isinstance(_detail_tmp, Msg):
            _detail_tmp = _detail_tmp.value

        self.detail = _detail_tmp


class ValidationDetailError(ValidationError):

    def __init__(self, detail=None, field=None, code=None):
        super().__init__(detail=detail, code=code)
        self.field = field
