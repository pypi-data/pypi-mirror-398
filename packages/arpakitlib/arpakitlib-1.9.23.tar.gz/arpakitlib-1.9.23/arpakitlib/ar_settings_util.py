# arpakit
from typing import Union, Any

from pydantic import ConfigDict, model_validator
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings


def generate_env_example(settings_class: Union[BaseSettings, type[BaseSettings]]) -> str:
    res = ""
    for k, f in settings_class.model_fields.items():
        if f.default is not PydanticUndefined:
            v = f.default
            # Приводим к строке для .env
            if isinstance(v, bool):
                s = "true" if v else "false"
            elif v is None:
                s = "None"
            else:
                s = str(v)
            # Если дефолт — строка с пробелами → в кавычки (экранируем \ и ")
            if isinstance(v, str) and any(ch.isspace() for ch in v):
                s = '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
            res += f"{k}={s}\n"
        else:
            # обязательное поле — без значения
            res += f"{k}=\n"
    return res


class SimpleSettings(BaseSettings):
    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        for key, value in values.items():
            if not isinstance(value, str):
                continue
            if value.lower().strip() in {"null", "none", "nil"}:
                values[key] = None
            elif value.lower().strip() == "default_value":
                field = cls.model_fields.get(key)
                if field is not None:
                    if field.default is not None:
                        values[key] = field.default
                    elif field.default_factory is not None:
                        values[key] = field.default_factory()
        return values

    @classmethod
    def generate_env_example(cls) -> str:
        return generate_env_example(settings_class=cls)

    @classmethod
    def save_env_example_to_file(cls, filepath: str) -> str:
        env_example = cls.generate_env_example()
        with open(filepath, mode="w") as f:
            f.write(env_example)
        return env_example


def __example():
    pass


if __name__ == '__main__':
    __example()
