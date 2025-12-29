# arpakit
from typing import Optional, Any


class NotSet:
    pass


def is_set(v: Any) -> bool:
    return not (v is NotSet or isinstance(v, NotSet))


def is_set_and_not_none(v: Any) -> bool:
    return is_set(v) and (v is not None)


def is_not_set(v: Any) -> bool:
    return not is_set(v)


def is_not_set_or_none(v: Any) -> bool:
    return is_not_set(v) or (v is None)


def raise_if_set(v: Any):
    if is_set(v):
        raise ValueError("value is set")


def raise_if_not_set(v: Any):
    if not is_set(v):
        raise ValueError("value not set")


def make_none_if_not_set(v: Any) -> Any:
    if is_not_set(v):
        return None
    return v


def raise_for_type(comparable, need_type, comment_for_error: Optional[str] = None):
    if comparable is need_type:
        return

    if not isinstance(comparable, need_type):
        err = f"raise_for_type, {comparable} != {need_type}, type {type(comparable)} != type {need_type}"
        if comment_for_error:
            err += f"\n{comment_for_error}"
        raise TypeError(err)


def raise_for_types(comparable, need_types, comment_for_error: Optional[str] = None):
    exceptions = []
    for need_type in need_types:
        try:
            raise_for_type(comparable=comparable, need_type=need_type, comment_for_error=comment_for_error)
            return
        except TypeError as e:
            exceptions.append(e)
    if exceptions:
        err = f"raise_for_types, {comparable} not in {need_types}, type {type(comparable)} not in {need_types}"
        if comment_for_error:
            err += f"\n{comment_for_error}"
        raise TypeError(err)


def make_none_to_false(v: Any) -> Any:
    if v is None:
        return False
    return v


def raise_if_none(v: Any) -> Any:
    if v is None:
        raise ValueError(f"v is None, v={v}, type(v)={type(v)}")
    return v


def raise_if_not_none(v: Any) -> Any:
    if v is not None:
        raise ValueError(f"v is not None, v={v}, type(v)={type(v)}")
    return v


def get_setted_elements_as_dict_from_dict(d: dict) -> dict[str, Any]:
    raise_for_type(d, dict)
    setted_ = {}
    for k, v in d.items():
        if is_set(v):
            setted_[k] = v
    return setted_


def get_setted_keys_from_dict(d: dict) -> list[Any]:
    return list(get_setted_elements_as_dict_from_dict(d).keys())


def __example():
    pass


if __name__ == '__main__':
    __example()
