import importlib.util
import os

from aiogram import Router


def include_aiogram_routers_from_dir(
        *,
        router: Router,
        base_dir: str = ".",
        exclude_filenames: list[str] | None = None,
):
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

            tg_bot_router = getattr(module, "tg_bot_router", None)
            if isinstance(tg_bot_router, Router):
                router.include_router(
                    router=tg_bot_router,
                )
