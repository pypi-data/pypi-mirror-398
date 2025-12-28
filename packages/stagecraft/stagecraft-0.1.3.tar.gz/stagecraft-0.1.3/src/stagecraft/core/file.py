import logging
import os

logger = logging.getLogger(__name__)


def append_file(content: str, filename: str, verbose: bool = True):
    dir = os.path.dirname(os.path.realpath(filename))
    os.makedirs(dir, exist_ok=True)
    with open(filename, "a", encoding="utf-8") as file:
        file.write(content)
    if verbose:
        logger.info(f"Data is appended to {filename}.")


def read_file(filename: str):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


def write_file(content: str, filename: str, verbose: bool = True):
    filename = os.path.realpath(filename)
    dir = os.path.dirname(os.path.realpath(filename))
    os.makedirs(dir, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    if verbose:
        logger.info(f"Data is written to {filename}.")
