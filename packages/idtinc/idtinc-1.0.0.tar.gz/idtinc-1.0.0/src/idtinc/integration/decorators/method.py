from typing import Callable, List, Optional

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action, parser_classes


class APIMethod:
    def __registry__(
        self,
        method: str,
        url_path: Optional[str] = None,
        detail: bool = False,
        parsers: Optional[List] = None,
        permission_classes: Optional[List] = None,
        authentication_classes: Optional[List] = None,
        **kwargs,
    ) -> Callable:
        if authentication_classes is not None:
            kwargs["authentication_classes"] = authentication_classes
        if permission_classes is not None:
            kwargs["permission_classes"] = permission_classes
        if parsers:
            kwargs["parser_classes"] = parsers

        return action(
            detail=detail,
            methods=[method],
            url_path=url_path,
            **kwargs,
        )

    def post(
        self,
        url_path: Optional[str] = None,
        authentication_classes: Optional[List] = None,
        permission_classes: Optional[List] = None,
        parsers: Optional[List] = None,
        **kwargs,
    ) -> Callable:
        return self.__registry__(
            detail=False,
            method="post",
            parsers=parsers,
            url_path=url_path,
            permission_classes=permission_classes,
            authentication_classes=authentication_classes,
            **kwargs,
        )

    def put(
        self,
        url_path: Optional[str] = None,
        authentication_classes: Optional[List] = None,
        permission_classes: Optional[List] = None,
        parsers: Optional[List] = None,
        **kwargs,
    ) -> Callable:
        return self.__registry__(
            detail=True,
            method="put",
            parsers=parsers,
            url_path=url_path,
            permission_classes=permission_classes,
            authentication_classes=authentication_classes,
            **kwargs,
        )

    def get(
        self,
        url_path: Optional[str] = None,
        detail: bool = False,
        authentication_classes: Optional[List] = None,
        permission_classes: Optional[List] = None,
        **kwargs,
    ) -> Callable:
        return self.__registry__(
            parsers=None,
            method="get",
            detail=detail,
            url_path=url_path,
            permission_classes=permission_classes,
            authentication_classes=authentication_classes,
            **kwargs,
        )

    def delete(
        self,
        url_path: Optional[str] = None,
        permission_classes: Optional[List] = None,
        authentication_classes: Optional[List] = None,
        **kwargs,
    ) -> Callable:
        return self.__registry__(
            detail=True,
            parsers=None,
            method="delete",
            url_path=url_path,
            permission_classes=permission_classes,
            authentication_classes=authentication_classes,
            **kwargs,
        )

    def patch(
        self,
        url_path: Optional[str] = None,
        parsers: Optional[List] = None,
        permission_classes: Optional[List] = None,
        authentication_classes: Optional[List] = None,
        **kwargs,
    ) -> Callable:
        return self.__registry__(
            detail=True,
            method="patch",
            parsers=parsers,
            url_path=url_path,
            permission_classes=permission_classes,
            authentication_classes=authentication_classes,
            **kwargs,
        )

    def options(
        self, url_path: Optional[str] = None, detail: bool = False, **kwargs
    ) -> Callable:
        return self.__registry__(
            method="options",
            detail=detail,
            url_path=url_path,
            **kwargs,
        )

    def head(
        self, url_path: Optional[str] = None, detail: bool = False, **kwargs
    ) -> Callable:
        return self.__registry__(
            method="head",
            detail=detail,
            url_path=url_path,
            **kwargs,
        )

    @property
    def swagger(self):
        return swagger_auto_schema

    @property
    def parser_classes(self):
        return parser_classes

    @property
    def atomic(self):
        return transaction.atomic


api_method = APIMethod()
