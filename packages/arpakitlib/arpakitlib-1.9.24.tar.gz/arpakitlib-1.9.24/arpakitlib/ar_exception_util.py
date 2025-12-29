import traceback


def exception_to_traceback_str(exception: BaseException) -> str:
    try:
        return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    except Exception as exception_:
        return f"Failed to format exception to traceback str {exception!r}: {exception_!r}"


def __example():
    pass


if __name__ == '__main__':
    __example()
