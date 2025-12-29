from functools import cached_property
from typing import (Any, Callable, Dict, Generic, List, Optional, Type,
                    TypeVar, Union)

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.query import QuerySet
from django.http import FileResponse
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, views, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.fields import empty
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from idtinc.core.message import Msg
from idtinc.core.status import HttpStatus

from .helpers import get_client_ip
from .paginator import Paginator
from .response import APIResponse

T = TypeVar("T")
S = TypeVar("S", bound=Serializer)
R = TypeVar("R")


class EmptySerializer(Serializer):
    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        return instance

    def create(self, validated_data: Dict[str, Any]) -> Any:
        return validated_data


class SerializerMixin(Generic[S]):
    serializer_class: Optional[Type[S]] = None
    request_serializer_class: Optional[Type[S]] = None
    response_serializer_class: Optional[Type[S]] = None
    action_serializers: Dict[str, Type[S]] = {}

    def get_serializer_for_action(self, action: str, for_request: bool = True) -> Optional[Type[S]]:
        suffix = "_request" if for_request else "_response"
        action_key = action + suffix

        if action_key in self.action_serializers:
            return self.action_serializers.get(action_key)

        if action in self.action_serializers:
            return self.action_serializers.get(action)

        if for_request and self.request_serializer_class:
            return self.request_serializer_class
        elif not for_request and self.response_serializer_class:
            return self.response_serializer_class

        return self.serializer_class

    def get_request_serializer_class(self) -> Optional[Type[S]]:
        return self.get_serializer_for_action(self.action, for_request=True) if hasattr(self, "action") else None

    def get_response_serializer_class(self) -> Optional[Type[S]]:
        if hasattr(self, "action"):
            return self.get_serializer_for_action(self.action, for_request=False)
        elif hasattr(self, "request") and hasattr(self.request, "method"):
            return self.get_serializer_for_action(self.request.method.lower(), for_request=False)
        return None


class GenericViewSetMixin(viewsets.GenericViewSet, Generic[T]):
    action_filtering: Dict[str, Callable[[QuerySet, Request], QuerySet]] = {}
    action_query_sets: Dict[str, QuerySet] = {}
    default_error_messages: Dict[str, str] = {
        "not_found": Msg.NOT_FOUND,
        "no_queryset": Msg.NO_CONTENT,
    }

    def get_queryset(self) -> QuerySet[T]:
        if getattr(self, "swagger_fake_view", False):
            return QuerySet()

        if self.action in self.action_query_sets:
            queryset = self.action_query_sets.get(self.action)

            if self.action in self.action_filtering:
                filter_func = self.action_filtering[self.action]
                queryset = filter_func(queryset, self.request)

            return queryset

        if getattr(self, "queryset", None) is not None:
            queryset = super().get_queryset()

            if "*" in self.action_filtering:
                filter_func = self.action_filtering["*"]
                queryset = filter_func(queryset, self.request)

            return queryset

        raise NotFound(Msg.NOT_FOUND)

    def filter_queryset(self, queryset: QuerySet[T]) -> QuerySet[T]:
        return super().filter_queryset(queryset)


class BaseAPIViewMixin(SerializerMixin[S], Generic[T, S]):
    response_serializer_class: Optional[Type[S]] = None
    serializer_class: Optional[Type[S]] = None
    request: Optional[Request] = None
    pagination_class: Optional[Any] = None
    page_size: int = 20

    @cached_property
    def response(self) -> Type[APIResponse]:
        return APIResponse

    def file_response(
        self,
        content: Any,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        return Response(content_type=content_type, headers=headers, data=content, **kwargs)

    def get_serializer_context(self) -> Dict[str, Any]:
        context = {"request": self.request, "format": self.format_kwarg, "view": self}

        if hasattr(self.request, "user"):
            context["user"] = self.request.user

        context["ip_address"] = get_client_ip(self.request)
        context["auth"] = self.request.auth

        return context

    def get_request_serializer(self, *args: Any, **kwargs: Any) -> S:
        serializer_class = self.get_request_serializer_class() or self.serializer_class or EmptySerializer

        if "context" not in kwargs:
            kwargs.setdefault("context", {})

        kwargs["context"].update(self.get_serializer_context() or {})

        return serializer_class(*args, **kwargs)

    def get_response_serializer(self, *args: Any, **kwargs: Any) -> S:
        serializer_class = (
            self.get_response_serializer_class()
            or self.response_serializer_class
            or self.serializer_class
            or EmptySerializer
        )

        if "context" not in kwargs:
            kwargs.setdefault("context", {})

        kwargs["context"].update(self.get_serializer_context() or {})

        return serializer_class(*args, **kwargs)

    def get_serializer(self, *args: Any, **kwargs: Any) -> S:
        is_request = kwargs.pop("is_request", True)
        return (
            self.get_request_serializer(*args, **kwargs)
            if is_request
            else self.get_response_serializer(*args, **kwargs)
        )

    def get_serializer_class(self) -> Type[S]:
        serializer_class = self.get_request_serializer_class() or self.serializer_class

        if serializer_class is None:
            setattr(self, "swagger_fake_view", True)
            return EmptySerializer

        return serializer_class

    def initialize_request(self, request: Request, *args: Any, **kwargs: Any) -> Request:
        return super().initialize_request(request, *args, **kwargs)

    def finalize_response(
        self,
        request: Request,
        response: Union[Response, FileResponse, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        if isinstance(response, FileResponse):
            return response

        if not isinstance(response, Response):
            response = self.response(data=response)

        return super().finalize_response(request, response, *args, **kwargs)

    def dispatch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().dispatch(request, *args, **kwargs)

    def handle_exception(self, exc: Exception) -> Response:
        return super().handle_exception(exc)

    def paginator(
        self,
        object_list: Union[List[T], QuerySet[T]],
        per_page: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        page: Optional[int] = None,
        metadata_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        with_serializer_class: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        page = page or Paginator.from_request(self.request, "page")
        per_page = per_page or Paginator.from_request(self.request, "limit") or self.page_size

        paginator = Paginator(object_list, per_page).page(page)

        if with_serializer_class:
            paginator = paginator.set_results_classes(self.get_response_serializer, option=kwargs)

        output_results = paginator.output_results

        if metadata_fn:
            metadata.update(metadata_fn(output_results))

        return self.response(
            data=output_results.pop("results", []),
            metadata={"pagination": output_results, **metadata},
        )

    def validate_serializer(self, instance: T = None, data=empty, *args, **kwargs):
        serializer = self.get_request_serializer(instance=instance, data=data, *args, **kwargs)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def valid_serializer(self, instance: T = None, data=empty, *args, **kwargs):
        serializer = self.get_request_serializer(instance=instance, data=data, *args, **kwargs)
        serializer.is_valid(raise_exception=True)
        return serializer

    def valid_and_save_serializer(self, instance: T = None, data=empty, *args, **kwargs):
        serializer = self.get_request_serializer(instance=instance, data=data, *args, **kwargs)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


class BaseViewSet(GenericViewSetMixin[T], BaseAPIViewMixin[T, S], viewsets.ModelViewSet):
    pass


class ReadOnlyViewSet(GenericViewSetMixin[T], BaseAPIViewMixin[T, S], viewsets.ReadOnlyModelViewSet):
    pass


AUTO_SCHEMA_NONE = swagger_auto_schema(auto_schema=None)


@method_decorator(name="list", decorator=AUTO_SCHEMA_NONE)
@method_decorator(name="update", decorator=AUTO_SCHEMA_NONE)
@method_decorator(name="create", decorator=AUTO_SCHEMA_NONE)
@method_decorator(name="destroy", decorator=AUTO_SCHEMA_NONE)
@method_decorator(name="retrieve", decorator=AUTO_SCHEMA_NONE)
@method_decorator(name="partial_update", decorator=AUTO_SCHEMA_NONE)
class GenericAPIView(
    BaseAPIViewMixin[T, S],
    GenericViewSetMixin[T],
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
):
    permission_classes: List[Any] = [IsAuthenticated]
    action_parser_classes: Dict[str, List[Any]] = {}
    permission_action_classes: Dict[str, List[Any]] = {}
    renderer_classes = [JSONRenderer]

    def get_parsers(self) -> List[Any]:
        return (
            self.action_parser_classes[self.action]
            if hasattr(self, "action") and self.action in self.action_parser_classes
            else super().get_parsers()
        )

    def get_permissions(self) -> List[Any]:
        return (
            [permission() for permission in self.permission_action_classes[self.action]]
            if hasattr(self, "action") and self.action in self.permission_action_classes
            else [permission() for permission in self.permission_classes]
        )

    @transaction.atomic
    def perform_create(self, serializer: S) -> T:
        return serializer.save()

    @transaction.atomic
    def perform_update(self, serializer: S) -> T:
        return serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance: T) -> None:
        if hasattr(instance, "is_deleted"):
            instance.delete()
        else:
            super().perform_destroy(instance)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.response(data=serializer.data)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return self.response(data=serializer.data, headers=headers)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.response(data=serializer.data)
        except ObjectDoesNotExist:
            return self.response(status=HttpStatus.NOT_FOUND)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return self.response(data=serializer.data)
        except ObjectDoesNotExist:
            return self.response(status=HttpStatus.NOT_FOUND)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return self.response(status=HttpStatus.NO_CONTENT)
        except ObjectDoesNotExist:
            return self.response(status=HttpStatus.NOT_FOUND)


class APIView(BaseAPIViewMixin[T, S], views.APIView):
    renderer_classes = [JSONRenderer]
    permission_classes: List[Any] = []

    def initial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        super().initial(request, *args, **kwargs)

    def handle_exception(self, exc: Exception) -> Response:
        return super().handle_exception(exc)
