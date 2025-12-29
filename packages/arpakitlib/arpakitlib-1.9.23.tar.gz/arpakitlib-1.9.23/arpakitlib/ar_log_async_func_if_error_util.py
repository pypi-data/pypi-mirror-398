# arpakit


import logging


async def log_async_func_if_error(
        async_func,
        logger: logging.Logger | None = None,
        logger_name: str | None = None,
        **kwargs
):
    if logger is None:
        logger = logging.getLogger()
    if logger is None and logger_name is not None:
        logger = logging.getLogger(logger_name)

    try:
        await async_func(**kwargs)
    except Exception as exception:
        logger.error(
            f"error in async_func, {async_func.__name__=}",
            exc_info=exception,
            extra={
                "log_async_func_if_error": True,
                "async_func_name": async_func.__name__
            }
        )
