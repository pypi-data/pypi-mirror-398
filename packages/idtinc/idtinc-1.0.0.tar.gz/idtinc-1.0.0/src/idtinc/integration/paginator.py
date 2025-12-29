import inspect
import math
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

from django.db.models.query import QuerySet
from django.utils.functional import cached_property
from django.utils.inspect import method_has_no_args
from rest_framework.request import Request

from .exception import MessageError

T = TypeVar("T")
R = TypeVar("R")


class Paginator(Generic[T]):
    DEFAULT_PAGE = 1
    DEFAULT_PER_PAGE = 10
    MIN_PAGE = 1
    MAX_PER_PAGE = 100

    def __init__(self, object_list: Union[List[T], QuerySet], per_page: int = 10):
        if per_page < 1:
            raise ValueError("per_page phải ít nhất là 1")

        if per_page > self.MAX_PER_PAGE:
            per_page = self.MAX_PER_PAGE

        self._object_list = object_list
        self.per_page = per_page
        self.current_page = 1
        self.bottom = 0
        self.top = 0
        self.classes: Optional[Callable] = None
        self.option_classes: Dict[str, Any] = {}

    @staticmethod
    def from_request(request: Request, key: str = "page") -> int:
        page_value = request.query_params.get(key)

        if page_value is None and hasattr(request, "data"):
            try:
                page_value = request.data.get(key)
            except (AttributeError, TypeError):
                page_value = None

        if not page_value:
            if key == "page":
                page_value = Paginator.DEFAULT_PAGE
            elif key == "limit":
                page_value = Paginator.DEFAULT_PER_PAGE

        try:
            return int(page_value)
        except (ValueError, TypeError):
            if key == "page":
                return Paginator.DEFAULT_PAGE
            elif key == "limit":
                return Paginator.DEFAULT_PER_PAGE
            return 0

    def page(self, page_number: int = 1) -> "Paginator[T]":
        if not isinstance(page_number, int):
            try:
                page_number = int(page_number)
            except (ValueError, TypeError):
                page_number = 1

        if page_number < 1:
            page_number = 1

        self.current_page = page_number
        current_page_index = page_number - 1

        self.bottom = current_page_index * self.per_page
        self.top = min(self.per_page + self.bottom, self.count)

        if page_number > self.num_pages and self.num_pages > 0:
            message = f"Trang {page_number} vượt quá số trang tối đa {self.num_pages}"
            raise MessageError(message)

        return self

    def set_results_classes(self, classes: Callable[[List[T]], Any], option: Dict[str, Any] = {}) -> "Paginator[T]":
        self.option_classes = option
        self.classes = classes
        return self

    @cached_property
    def num_pages(self) -> int:
        if self.count == 0:
            return 0
        return math.ceil(self.count / self.per_page)

    @cached_property
    def count(self) -> int:
        try:
            count_method = getattr(self._object_list, "count", None)
            if callable(count_method) and not inspect.isbuiltin(count_method) and method_has_no_args(count_method):
                return count_method()

            return len(self._object_list)
        except (TypeError, AttributeError) as e:
            return 0

    @cached_property
    def object_results(self) -> List[T]:
        try:
            if isinstance(self._object_list, QuerySet):
                return list(self._object_list[self.bottom : self.top])
            else:
                return self._object_list[self.bottom : self.top]
        except Exception as e:
            return []

    @cached_property
    def results(self) -> Any:
        try:
            if not self.object_results:
                return []

            if hasattr(self, "classes") and self.classes is not None:
                kwargs = {"many": True}
                if hasattr(self, "option_classes"):
                    kwargs.update(self.option_classes)
                return self.classes(self.object_results, **kwargs).data

            if hasattr(self.object_results, "values"):
                return list(self.object_results.values())

            return self.object_results
        except Exception as e:
            return []

    @cached_property
    def output_results(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "num_pages": self.num_pages,
            "current_page": self.current_page,
            "previous_page": self.previous_page,
            "next_page": self.next_page,
            "per_page": self.per_page,
            "results": self.results,
        }

    def get_output_results(self, results: List[Any]) -> Dict[str, Any]:
        return {
            "count": self.count,
            "num_pages": self.num_pages,
            "current_page": self.current_page,
            "previous_page": self.previous_page,
            "next_page": self.next_page,
            "per_page": self.per_page,
            "results": results,
        }

    @cached_property
    def previous_page(self) -> Optional[int]:
        return self.current_page - 1 if self.current_page > 1 else None

    @cached_property
    def next_page(self) -> Optional[int]:
        return self.current_page + 1 if self.current_page < self.num_pages else None

    def has_next(self) -> bool:
        return self.current_page < self.num_pages

    def has_previous(self) -> bool:
        return self.current_page > 1
