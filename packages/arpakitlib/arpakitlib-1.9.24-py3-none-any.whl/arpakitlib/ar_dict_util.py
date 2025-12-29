# arpakit

from typing import Any


def combine_dicts(*dicts: dict) -> dict[Any, Any]:
    res = {}
    for dict_ in dicts:
        res.update(dict_)
    return res


def replace_dict_key(*, dict_: dict, old_key: Any, new_key: Any) -> dict[Any, Any]:
    if old_key in dict_:
        dict_[new_key] = dict_.pop(old_key)
    return dict_


class GetTypedFromDictException(Exception):
    pass


def get_typed_from_dict(
        *,
        d: dict,
        key: str,
        type_,
        allow_missing: bool = False,
        custom_exception: type[Exception] = GetTypedFromDictException
) -> Any:
    """
    Получает d[key], проверяет, что оно относится к типу typ.
    Если ключ отсутствует:
        - если allow_non_existing=True → возвращаем None
        - иначе → KeyError
    Если тип не совпадает → TypeError
    """

    if key not in d:
        if allow_missing:
            return None
        raise custom_exception(f"Missing key: {key}")

    val = d[key]

    if not isinstance(val, type_):
        raise custom_exception(f"Expected {type_}, got {type(val)} for key '{key}'")

    return val


def __example():
    pass


if __name__ == '__main__':
    __example()
