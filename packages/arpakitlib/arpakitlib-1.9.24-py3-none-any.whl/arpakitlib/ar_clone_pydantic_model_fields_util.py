# arpakit
from typing import Any, Type, Iterable

from pydantic import BaseModel, create_model
from pydantic_core import PydanticUndefined


def clone_pydantic_model_fields(
        *,
        model_cls: Type[BaseModel],
        base_model: Type[BaseModel] = BaseModel,
        fields_to_remove: Iterable[str] | None = None,
        new_class_name: str | None = None,
        class_name_suffix: str | None = "Cloned"
) -> Type[BaseModel]:
    if fields_to_remove is None:
        fields_to_remove = set()
    if class_name_suffix is None:
        class_name_suffix = "Cloned"
    if new_class_name is None:
        new_class_name = f"{model_cls.__name__}{class_name_suffix}"

    field_defs: dict[str, tuple[type[Any], Any]] = {}

    for field_name, field_ in model_cls.model_fields.items():
        if field_name in fields_to_remove:
            continue

        if field_.default_factory is not None and field_.default is PydanticUndefined:
            default = field_
        elif field_.default is not PydanticUndefined:
            default = field_.default
        else:
            default = field_

        field_defs[field_name] = ((field_.annotation or Any), default)

    res = create_model(
        new_class_name,
        __base__=base_model,
        __module__=model_cls.__module__,
        **field_defs,
    )

    return res


def __example():
    pass


if __name__ == '__main__':
    __example()
