import dj_database_url
from pydantic import BaseModel, model_serializer


class Database(BaseModel):
    """
    Параметры подключения к базе данных. Основано на параметрах функции dj_database_url.parse
    """

    url: str
    engine: str | None = None
    conn_max_age: int | None = 0
    conn_health_checks: bool = False
    disable_server_side_cursors: bool = False
    ssl_require: bool = False
    test_options: dict | None = None

    @model_serializer
    def serialize(self) -> dj_database_url.DBConfig:
        return dj_database_url.parse(**{field: value for field, value in self})
