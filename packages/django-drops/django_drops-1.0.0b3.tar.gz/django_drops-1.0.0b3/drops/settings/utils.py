from pydantic import AliasGenerator, BaseModel, ConfigDict

alias_generator = AliasGenerator(serialization_alias=str.upper)


class DjangoModel(BaseModel):
    """
    Базовая модель для настроек. Так как в django конфигурация осуществляется путём определения констант
    в модуле settings, удобно иметь модель, которая сама переводит ключи в верхний регистр. Также это удобно для
    словарей TEMPLATES, REST_FRAMEWORK и т.п.
    """

    model_config = ConfigDict(alias_generator=alias_generator)
