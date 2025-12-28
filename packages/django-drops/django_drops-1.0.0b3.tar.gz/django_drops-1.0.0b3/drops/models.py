from __future__ import annotations

import contextlib
import json
from collections.abc import Callable

import pydantic
from django.core.exceptions import ValidationError
from django.db import models
from pydantic import BaseModel

from .serializers.json import JSONEncoder


class PydanticField(models.JSONField):
    def __init__(  # noqa: PLR0913
        self,
        model: type[BaseModel],
        verbose_name: str | None = None,
        name: str | None = None,
        encoder: type[json.JSONEncoder] | None = None,
        decoder: type[json.JSONDecoder] | None = None,
        default: Callable | None = models.NOT_PROVIDED,
        **kwargs,
    ) -> None:
        if encoder is None:
            encoder = JSONEncoder
        if default is models.NOT_PROVIDED:
            with contextlib.suppress(pydantic.ValidationError):
                model()  # модель может быть без дефолтных значений
                default = model

        super().__init__(verbose_name, name, encoder, decoder, default=default, **kwargs)
        self._pydantic_model = model

    def from_db_value(self, value, expression, connection):  # noqa: ANN001, ANN201
        v = super().from_db_value(value, expression, connection)
        if self.null and v is None:
            return None
        return self._pydantic_model.model_validate(v)

    def get_db_prep_value(self, value, connection, prepared=False):  # noqa: ANN001, ANN201, PLR0911
        if self.null and value is None:
            return None

        # нормальная pydantic модель
        if hasattr(value, "model_dump"):
            return super().get_db_prep_value(value.model_dump(), connection, prepared)

        # обёртка в виде models.Value
        if isinstance(value, models.Value):
            return self.get_db_prep_value(value.value, connection, prepared)

        # Cast и иже с ним
        if hasattr(value, "get_source_expressions"):
            if expressions := value.get_source_expressions():
                expr = expressions[0]

                # При null=True django говорит "смотри как могу" и оборачивает
                # всё в Case-When-Else, а внутри всё в Value. Прикольно, чё.
                if isinstance(expr, models.Case):
                    for when in expr.cases:
                        if isinstance(when, models.When):
                            return self.get_db_prep_value(when.result, connection, prepared)
                    if hasattr(expr, "default"):
                        return self.get_db_prep_value(expr.default, connection, prepared)

                return self.get_db_prep_value(expr.value, connection, prepared)
            return None

        return super().get_db_prep_value(value, connection, prepared)

    def to_python(self, value):  # noqa: ANN001, ANN201
        if self.null and value is None:
            return None
        try:
            return self._pydantic_model.model_validate(super().to_python(value))
        except pydantic.ValidationError as e:
            raise ValidationError(str(e)) from e

    def deconstruct(self):  # noqa: ANN201
        name, path, args, kwargs = super().deconstruct()
        return name, path, (self._pydantic_model, *args), kwargs

    def value_to_string(self, obj):  # noqa: ANN001, ANN201
        if self.null and obj is None:
            return None

        # easyaudit прокидывает сюда значение, из которого достанется словарь
        value = self.value_from_object(obj)
        if isinstance(value, dict):
            return value
        return value.model_dump()
