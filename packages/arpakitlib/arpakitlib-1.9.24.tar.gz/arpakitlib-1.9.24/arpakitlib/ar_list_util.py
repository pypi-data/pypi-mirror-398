# arpakit

from typing import Any


def iter_group_list(list_: list[Any], n: int):
    part = []
    for v in list_:
        if len(part) < n:
            part.append(v)
        else:
            yield part.copy()
            part = [v]
    yield part


def group_list(list_: list[Any], n: int):
    return list(iter_group_list(list_=list_, n=n))


def remove_from_list_if_left(*, list_: list[Any], values: list[Any]) -> list[Any]:
    """
    Удаляет из list_ все элементы, чьи значения перечислены в values,
    НО только если после удаления в list_ останется хотя бы один элемент.

    Всегда возвращает сам список list_ (после возможной модификации in-place).
    """
    if not values:
        return list_

    targets = set(values)
    # кандидат на новое содержимое
    filtered = [x for x in list_ if x not in targets]

    # если нечего удалять — оставляем как есть
    if len(filtered) == len(list_):
        return list_

    # удаляем только если список не опустеет
    if len(filtered) == 0:
        return list_

    # применяем изменения in-place
    list_[:] = filtered
    return list_


def remove_from_lists_if_left(
        *,
        lists_: list[list[Any]],
        values: list[Any]
):
    for list_ in lists_:
        remove_from_list_if_left(list_=list_, values=values)
    return lists_


def int_to_list_(value: int | list | None) -> list[int] | None:
    if isinstance(value, int):
        return [value]
    elif isinstance(value, list):
        return value
    elif value is None:
        return None
    else:
        raise TypeError(f"{type(value)=}")


def str_to_list_(value: str | list | None) -> list[str] | None:
    if isinstance(value, str):
        return [value]
    elif isinstance(value, list):
        return value
    elif value is None:
        return None
    else:
        raise TypeError(f"{type(value)=}")


def __example():
    pass


if __name__ == '__main__':
    __example()
