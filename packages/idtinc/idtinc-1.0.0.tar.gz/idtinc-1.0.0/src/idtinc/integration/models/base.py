import random
import string
import time
import uuid

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_currentuser.middleware import get_current_user


class BaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name=_("Ngày tạo"))
    updated_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name=_("Ngày cập nhật"))

    objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class TrackableModel(BaseModel):
    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created_by",
        verbose_name=_("Người tạo"),
    )
    updated_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated_by",
        verbose_name=_("Người cập nhật"),
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_user = get_current_user()
        if current_user and not isinstance(current_user, AnonymousUser):
            setattr(self, "updated_by" if self.pk else "created_by", current_user)

        super().save(*args, **kwargs)


class SoftDeleteManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(TrackableModel):
    is_deleted = models.BooleanField(default=False, editable=False, verbose_name=_("Is deleted"))
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name=_("Ngày xoá"))
    deleted_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted_by",
        verbose_name=_("Người xoá"),
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["-deleted_at"]
        abstract = True

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.is_deleted = True

        current_user = get_current_user()
        if current_user and not isinstance(current_user, AnonymousUser):
            setattr(self, "deleted_by", current_user)

        super().save(*args, **kwargs)

    def force_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class Generator:

    @staticmethod
    def uuid():
        return uuid.uuid4().hex

    @staticmethod
    def device_id():
        return f"DID.{time.time()}.{uuid.uuid4().hex}"

    class Random:
        def __init__(self, length: int = 6, prefix: str | None = None):
            self.length = length
            self.prefix = prefix
            self.code = self.__generate_code()

        def __generate_code(self):
            alpha_part = "".join(random.choices(string.ascii_uppercase, k=2))
            digit_part = "".join(random.choices(string.digits, k=max(self.length - 2, 1)))
            return f"{self.prefix or alpha_part}{digit_part}"

        def __str__(self):
            return str(self.code)

    class Code:
        def __init__(self, pk: int, length: int = 6):
            self.pk = pk
            self.length = length
            self.code = self.__generate_code()

        def __generate_code(self):
            year = timezone.now().strftime("%y")
            return f"{year}{self.pk:0{self.length}d}"

        def __str__(self):
            return str(self.code)

    class Ref:
        def __init__(self, pk: int):
            self.sequence = 0
            self.last_timestamp = -1
            self.pk_bits = pk & 0x3FF
            self.code = self.__generate_code()

        def __current_timestamp(self):
            return int(time.time() * 1000)

        def __generate_code(self):
            timestamp = self.__current_timestamp()

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF
                if self.sequence == 0:
                    while timestamp <= self.last_timestamp:
                        timestamp = self.__current_timestamp()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            return (timestamp << 22) | (self.pk_bits << 12) | self.sequence

        def __int__(self):
            return self.code

        def __str__(self):
            return str(self.code)
