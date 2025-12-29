from typing import Any, Callable, Generic, List, Optional, Type, TypeVar

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import Model, Q, QuerySet
from django_currentuser.middleware import get_current_user

from .helpers.query import UnaccentVN

T = TypeVar("T", bound=Model)


class BaseService(Generic[T]):
    model: Type[T] = None

    def __init__(self, model: Type[T] = None):
        if not self.model:
            self.model = model

    def get_queryset(self):
        if not self.model:
            raise ValueError("Model không được định nghĩa cho service này")

        return self.model.objects.all()

    def get_objects(
        self,
        search: Optional[str] = None,
        prefetch_related: List[Any] = None,
        select_related: List[Any] = None,
        **kwargs,
    ) -> QuerySet[T]:
        q_filters = Q()

        exclude_kwargs = [
            "order_by",
            "search_fields",
            "page",
            "limit",
            "prefetch_related",
            "select_related",
            "unaccent_fields",
        ]

        for key, value in kwargs.items():
            if key in exclude_kwargs:
                continue

            if value is not None:
                q_filters &= Q(**{key: value})

        objects = self.get_queryset()

        unaccent_field_annotate = {}

        if unaccent_fields := kwargs.get("unaccent_fields", []):
            unaccent_fields = list(set(unaccent_fields))
            for field in unaccent_fields:
                unaccent_field_annotate[f"{field}_ascii"] = UnaccentVN(field)
            objects = objects.annotate(**unaccent_field_annotate)

        if search and search.strip():
            search = search.strip()

            search_fields = kwargs.get("search_fields", [])
            if not search_fields:
                raise ValueError("Cần chỉ định search_fields khi sử dụng search")

            search_query = Q()
            for field in search_fields:
                search_query |= Q(**{f"{field}__icontains": search})

            for field in unaccent_field_annotate.keys():
                search_query |= Q(**{f"{field}__icontains": search})

            q_filters &= search_query

        if prefetch_related:
            objects = objects.prefetch_related(*prefetch_related)

        if select_related:
            objects = objects.select_related(*select_related)

        objects = objects.filter(q_filters)

        order_by = str(kwargs.get("order_by") or "desc").lower()
        if order_by == "asc":
            objects = objects.order_by("id")
        else:
            objects = objects.order_by("-id")

        return objects

    def get_by_id(
        self,
        id: Any,
        prefetch_related: List[Any] = None,
        select_related: List[Any] = None,
        **kwargs,
    ) -> T:
        objects = self.get_queryset()

        if prefetch_related:
            objects = objects.prefetch_related(*prefetch_related)

        if select_related:
            objects = objects.select_related(*select_related)

        return objects.get(pk=id, **kwargs)

    def get_by_filters(
        self,
        prefetch_related: List[Any] = None,
        select_related: List[Any] = None,
        **kwargs,
    ) -> T:
        objects = self.get_queryset()

        if prefetch_related:
            objects = objects.prefetch_related(*prefetch_related)

        if select_related:
            objects = objects.select_related(*select_related)

        return objects.get(**kwargs)

    def first_by_filters(
        self,
        prefetch_related: List[Any] = None,
        select_related: List[Any] = None,
        func: Callable = None,
        **kwargs,
    ) -> T:
        objects = self.get_queryset().filter(**kwargs)

        if prefetch_related:
            objects = objects.prefetch_related(*prefetch_related)

        if select_related:
            objects = objects.select_related(*select_related)

        if func:
            objects = func(objects)

        return objects.first()

    def exists(self, **kwargs) -> bool:
        return self.get_queryset().filter(**kwargs).exists()

    def create(self, **kwargs) -> T:
        instance = self.get_queryset().create(**kwargs)
        return instance

    def update(self, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        instance.save()
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()

    def delete_by_id(self, id: Any) -> None:
        instance = self.get_by_id(id)
        self.delete(instance)

    @property
    def current_user(self) -> Optional[Any]:
        return get_current_user()

    @property
    def is_authenticated(self) -> bool:
        return self.current_user and not isinstance(self.current_user, AnonymousUser)

    def mapping_search(self, filter_keys: list[str], value: str):
        if not value or not filter_keys:
            return None

        value = value.strip()
        Q_filter_search = models.Q()
        for key in filter_keys:
            Q_filter_search |= models.Q(**{f"{key}__icontains": value})

        return Q_filter_search

    def get_full_select_related(self, model: Type[T] = None) -> List[Any]:
        class_model = model or self.model
        return [field.name for field in class_model._meta.get_fields() if isinstance(field, models.ForeignKey)]

    def get_full_prefetch_related(self, model: Type[T] = None) -> List[Any]:
        class_model = model or self.model
        return [field.name for field in class_model._meta.get_fields() if isinstance(field, models.ManyToManyField)]

    def get_ordering(self, ordering: str, orderings: list[str]) -> str:
        result_fields = []
        if not ordering:
            return result_fields

        ordering_fields = [field.strip() for field in ordering.split(",")]
        for field in ordering_fields:
            field_no_dash = field.lstrip("-")
            if field_no_dash in orderings:
                result_fields.append(field)

        return result_fields

    def try_pass(self, func: Callable, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pass
