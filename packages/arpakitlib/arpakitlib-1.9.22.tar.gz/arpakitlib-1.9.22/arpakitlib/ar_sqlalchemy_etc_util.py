from typing import Any


def _str_no_self(v: str) -> str:
    return v.replace("self.", "").strip()


def generate_sqlalchemy_model_repr(*, title: str, parts: list[Any]):
    res = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, int):
            part = str(part)
        elif isinstance(part, bool):
            part = str(part)
        elif isinstance(part, str):
            part = _str_no_self(part)
            part = part.strip()
        if not part:
            continue
        res.append(part)
    return f"{title} ({', '.join(res)})"
