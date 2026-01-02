from urllib.parse import quote_plus


def generate_connection_url(
        *,
        scheme: str = "postgresql",  # общий случай: postgresql, sqlite, redis, amqp и т.п.
        user: str | None = None,
        password: str | None = None,
        host: str | None = "127.0.0.1",
        port: int | None = None,
        database: str | int | None = None,
        quote_query_params: bool = True,
        **query_params
) -> str:
    """
    Универсальная функция для генерации URL соединений (Postgres, Redis, AMQP, SQLite и др.)

    Примеры:
      postgresql://user:pass@localhost:5432/dbname
      sqlite:///path/to/db.sqlite3
      redis://:mypassword@redis:6379/0
      amqp://user:pass@rabbit:5672/myvhost
    """
    # Формируем часть авторизации
    auth_part = ""
    if user and password:
        auth_part = f"{quote_plus(user)}:{quote_plus(password)}@"
    elif password and not user:
        auth_part = f":{quote_plus(password)}@"
    elif user:
        auth_part = f"{quote_plus(user)}@"

    # Формируем хост и порт
    if scheme.startswith("sqlite"):
        host_part = ""
    else:
        host_part = host or ""
        if port:
            host_part += f":{port}"

    # Формируем "базу" (database / номер / путь)
    db_part = ""
    if database is not None:
        db_part = f"/{quote_plus(str(database))}"

    # Формируем query параметры
    query_part = ""
    if query_params:
        query_items = []
        for k, v in query_params.items():
            value = str(v)
            if quote_query_params:
                value = quote_plus(value)
            query_items.append(f"{k}={value}")
        query_part = f"?{'&'.join(query_items)}"

    return f"{scheme}://{auth_part}{host_part}{db_part}{query_part}"


def __example():
    pass


if __name__ == '__main__':
    __example()
