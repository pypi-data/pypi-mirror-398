import inspect

from pydantic_settings import BaseSettings, SettingsConfigDict

from .utils import alias_generator


class DjangoSettings(BaseSettings):
    """
    Базовый класс для настроек django-проекта
    """

    model_config = SettingsConfigDict(alias_generator=alias_generator)

    def __init__(self, **values):
        super().__init__(**values)
        self._set_globals()

    def _set_globals(self, offset=2) -> None:
        """
        Заполняет содержимым модели глобальные переменные модуля, в котором вызван

        offset по умолчанию 2, потому что при предполагаемом использовании метода стэк выглядит так:
            0. DjangoSettings._set_globals
            1. DjangoSettings.__init__
            2. <settings module>
        """
        stack = inspect.stack()
        settings_module_frame = stack[offset].frame
        settings_module_frame.f_locals.update(self.model_dump(by_alias=True))
