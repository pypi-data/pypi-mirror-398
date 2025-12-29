from typing import Any, Optional, TypeVar

from django.core.files.storage import default_storage
from django.db import models
from django.db.models import functions
from django.db.models.query import QuerySet

T = TypeVar("T")


def null_if_blank(field):
    return models.Case(
        models.When(**{field: ""}, then=models.Value(None)),
        default=field,
    )


class ExtractEpochAndDivide(models.Func):
    template = "(%(expressions)s::date - CURRENT_DATE::date + 1)"
    output_field = models.FloatField()

    def __init__(self, expression):
        super().__init__(expression)


class PostgresqlJsonField(models.JSONField):
    def from_db_value(self, value: Any, expression: Any, connection: Any) -> Any:
        return value

    def get_prep_value(self, value: Any) -> Any:
        return super().get_prep_value(value)


class SubqueryJson(models.Subquery):
    template = "(SELECT row_to_json(_subquery) FROM (%(subquery)s) _subquery)"
    output_field = PostgresqlJsonField()

    def __init__(self, queryset: QuerySet, **kwargs: Any) -> None:
        try:
            super().__init__(queryset, **kwargs)
        except Exception as e:
            print(f"Lỗi khi khởi tạo SubqueryJson: {e}")
            raise


class SubqueryJsonAgg(models.Subquery):
    template = "(SELECT array_to_json(coalesce(array_agg(row_to_json(_subquery)), array[]::json[])) FROM (%(subquery)s) _subquery)"
    template_return_none = "(SELECT CASE WHEN COUNT(*) = 0 THEN NULL ELSE array_to_json(array_agg(row_to_json(_subquery))) END FROM (%(subquery)s) _subquery)"

    output_field = PostgresqlJsonField()

    def __init__(
        self,
        queryset: QuerySet,
        alias: Optional[str] = None,
        flat: bool = False,
        return_none: bool = False,
        **kwargs: Any,
    ) -> None:
        self.return_none = return_none
        self.flat = flat

        try:
            if self.flat:
                if not alias:
                    raise ValueError("Khi flat=True, alias không được để trống")
                queryset = queryset.values_list(alias, flat=True)

            super().__init__(queryset, **kwargs)
        except Exception as e:
            raise

    def as_sql(
        self, compiler: Any, connection: Any, template: Optional[str] = None
    ) -> tuple:

        try:
            if self.flat:
                if (
                    hasattr(self.queryset, "query")
                    and hasattr(self.queryset.query, "values")
                    and self.queryset.query.values
                ):
                    self.extra["value"] = f"_subquery.{self.queryset.query.values[0]}"
                else:
                    raise ValueError("Không tìm thấy giá trị để tổng hợp")
            else:
                self.extra["value"] = "row_to_json(_subquery)"

            selected_template = (
                self.template_return_none
                if self.return_none
                else template or self.template
            )

            return super().as_sql(compiler, connection, selected_template)
        except Exception as e:
            raise


class UnaccentVN(models.Func):
    function = "unaccent_vn"
    template = "translate(%(expressions)s, 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựíìỉĩịýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÍÌỈĨỊÝỲỶỸỴĐ', 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeooooooooooooooooouuuuuuuuuuuiiiiiyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEOOOOOOOOOOOOOOOOOUUUUUUUUUUUIIIIIYYYYYD')"
    output_field = models.CharField()

    def __init__(self, expression: Any, **extra: Any) -> None:
        try:
            super().__init__(expression, **extra)
        except Exception as e:
            print(f"Lỗi khi khởi tạo UnaccentVN: {e}")
            raise


def json_build_object(**kwargs: Any) -> models.Func:
    args = []
    for key, value in kwargs.items():
        args.extend([models.Value(key), value])

    return models.Func(
        *args, function="json_build_object", output_field=PostgresqlJsonField()
    )


def json_agg(expression: Any) -> models.Func:
    return models.Func(
        expression, function="json_agg", output_field=PostgresqlJsonField()
    )


def lower_unaccent(expression: Any) -> models.Func:
    return models.Func(
        UnaccentVN(functions.Lower(expression)),
        function="TRIM",
        output_field=models.CharField(),
    )


class JsonbArrayElements(models.Func):
    function = "jsonb_array_elements"
    output_field = models.JSONField()


def get_choices_value(value):
    return getattr(value, "value", None)


def get_choices_label(value):
    return getattr(value, "label", None)


def get_choices_dict(value):
    return {
        "label": get_choices_label(value),
        "value": get_choices_value(value),
    }


def get_choice_value(choices, value):
    if value is None or not choices:
        return None

    if hasattr(choices, "choices"):
        choices = choices.choices

    choices_dict = dict(choices)
    return choices_dict.get(value)


def get_storage_url(name):
    return default_storage.url(name)