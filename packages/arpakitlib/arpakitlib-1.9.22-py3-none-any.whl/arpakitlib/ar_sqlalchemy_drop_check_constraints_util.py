from __future__ import annotations

from typing import Optional

import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase


def _quote_ident_pg(ident: str) -> str:
    # простое кавычирование для PG (экранируем двойные кавычки)
    return '"' + ident.replace('"', '""') + '"'


def _quote_ident_mysql(ident: str) -> str:
    # простое кавычирование для MySQL/MariaDB (экранируем обратные апострофы)
    return '`' + ident.replace('`', '``') + '`'


def _qualified_name(
        schema: Optional[str], table: str, dialect_name: str
) -> str:
    if dialect_name == "postgresql":
        q = _quote_ident_pg
    elif dialect_name in {"mysql", "mariadb"}:
        q = _quote_ident_mysql
    else:
        # по умолчанию без кавычек — но мы не должны сюда попасть,
        # поскольку ниже ограничиваем поддержанные диалекты.
        q = lambda x: x

    if schema:
        return f"{q(schema)}.{q(table)}"
    return q(table)


def drop_sqlalchemy_check_constraints(*, base_: type[DeclarativeBase], engine: Engine) -> None:
    """
    Удаляет ВСЕ существующие в БД CHECK-ограничения для таблиц из base_.metadata,
    выполняя прямые SQL-запросы (без SQLAlchemy DDL-объектов).

    Поддерживаемые диалекты:
      - PostgreSQL: ALTER TABLE <sch>.<tbl> DROP CONSTRAINT <name>
      - MySQL 8.0.16+/MariaDB 10.2+: ALTER TABLE <sch>.<tbl> DROP CHECK <name>

    Для SQLite кидает NotImplementedError.
    """

    if engine.dialect.name == "sqlite":
        raise NotImplementedError(
            "Удаление CHECK-констреинтов прямыми запросами для SQLite не поддержано: "
            "в большинстве версий требуется пересоздание таблицы."
        )
    if engine.dialect.name not in {"postgresql", "mysql", "mariadb"}:
        raise NotImplementedError(f"Пока не реализовано для диалекта: {engine.dialect.name}")

    with engine.begin() as conn:
        conn_inspection_ = sqlalchemy.inspect(conn)

        for table in base_.metadata.tables.values():
            if not conn_inspection_.has_table(table.name, schema=table.schema):
                continue

            fqtn = _qualified_name(table.schema, table.name, engine.dialect.name)

            # берём ВСЕ реальные CHECK-и из базы
            checks = conn_inspection_.get_check_constraints(table.name, schema=table.schema)

            for check_ in checks:
                name = check_.get("name")
                if not name:
                    # На всякий случай: без имени нам нечего дропать безопасно
                    # (в PG/ MySQL синтаксис требует имя).
                    continue

                if engine.dialect.name == "postgresql":
                    ident = _quote_ident_pg(name)
                    sql = f"ALTER TABLE {fqtn} DROP CONSTRAINT {ident}"
                else:  # mysql / mariadb
                    ident = _quote_ident_mysql(name)
                    # В MySQL/MariaDB именно DROP CHECK <name>
                    sql = f"ALTER TABLE {fqtn} DROP CHECK {ident}"

                # выполняем прямой SQL-запрос
                conn.exec_driver_sql(sql)
