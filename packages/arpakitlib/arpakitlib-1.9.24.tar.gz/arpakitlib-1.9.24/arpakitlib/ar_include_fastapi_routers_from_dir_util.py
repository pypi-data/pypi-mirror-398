import importlib.util
import os

from fastapi import APIRouter


def include_fastapi_routers_from_dir(
        *,
        router: APIRouter,
        base_dir: str = ".",
        exclude_filenames: list[str] | None = None,
):
    """
    Рекурсивно ищет все .py файлы с объектом `api_router` типа APIRouter
    и подключает их к переданному `router`.

    Префикс = имя файла без .py
    exclude_filenames — список имён файлов, которые нужно пропустить (без путей)
    """
    if exclude_filenames is None:
        exclude_filenames = ["__init__.py"]

    for root, _, files in os.walk(base_dir):
        files.sort()

        for filename in files:
            if not filename.endswith(".py") or filename in exclude_filenames:
                continue

            file_path = os.path.join(root, filename)
            module_name = (
                os.path.relpath(file_path, base_dir)
                .replace(os.sep, ".")
                .removesuffix(".py")
            )

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            api_router = getattr(module, "api_router", None)
            if isinstance(api_router, APIRouter):
                prefix = "/" + filename[:-3]  # имя файла без .py
                router.include_router(
                    router=api_router,
                    prefix=prefix
                )
