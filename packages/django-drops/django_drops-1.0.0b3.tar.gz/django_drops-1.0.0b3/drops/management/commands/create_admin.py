from __future__ import annotations

from traceback import format_exception_only
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.db import models


class Command(BaseCommand):
    help = "Create admin user"

    def get_model(self) -> models.Model:
        return get_user_model()

    def get_fields(self) -> Iterable[str]:
        model = self.get_model()
        # result = []
        # for field_name in (model.USERNAME_FIELD, getattr(model, "PASSWORD_FIELD", "password"), *model.REQUIRED_FIELDS):
        #     field = model._meta.get_field(field_name)
        #     if not field.null and not field.default:
        #         result.append(field_name)
        # return result
        return {model.USERNAME_FIELD, getattr(model, "PASSWORD_FIELD", "password"), *model.REQUIRED_FIELDS}

    def add_arguments(self, parser: CommandParser) -> None:
        defaults = {"email": "admin@localhost", "username": "admin", "password": "admin"}

        for field in self.get_fields():
            kwargs = {
                "type": str,
                "required": not settings.DEBUG,
                "default": defaults.get(field, "admin") if settings.DEBUG else None,
            }
            parser.add_argument(f"-{field[0]}", f"--{field}", **kwargs)

    def handle(self, *args, **options) -> None:
        params = {k: v for k, v in options.items() if k in self.get_fields()}

        try:
            user = get_user_model().objects.create_superuser(**params)
            self.stdout.write(
                self.style.SUCCESS("Successfully created user [")
                + self.style.WARNING(f"pk={user.pk}")
                + self.style.SUCCESS("]")
            )
        except Exception as e:  # noqa: BLE001
            self.stdout.write(self.style.WARNING("".join(format_exception_only(e))))
