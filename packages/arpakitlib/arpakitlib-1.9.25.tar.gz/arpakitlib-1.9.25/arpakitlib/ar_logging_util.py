# arpakit

import logging
import os


def init_log_file(*, log_filepath: str | None):
    if not log_filepath:
        return
    directory = os.path.dirname(log_filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    if not os.path.exists(log_filepath):
        with open(log_filepath, mode="w") as file:
            file.write(" \n")


_normal_easy_logging_was_setup: bool = False


def setup_normal_easy_logging():
    global _normal_easy_logging_was_setup
    if _normal_easy_logging_was_setup:
        logging.getLogger().info("normal easy logging was already setup")
        return

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter(
        "%(asctime)s %(msecs)03d | %(levelname)s | %(name)s | %(filename)s | "
        "%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S %p %Z %z",
    )
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    _normal_logging_was_setup = True

    logger.info("normal easy logging was setup")


def __example():
    pass


if __name__ == '__main__':
    __example()
