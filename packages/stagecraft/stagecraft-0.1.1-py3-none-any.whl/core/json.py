import json
import logging
import os
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


def append_json(
    content: Dict[str, Any],
    filename: str,
    indent: int = 4,
    default: Callable[[Any], Any] = str,
    verbose: bool = True,
    **kwargs,
):
    dir = os.path.dirname(os.path.realpath(filename))
    os.makedirs(dir, exist_ok=True)
    with open(filename, "w+", encoding="utf-8") as json_file:
        json.dump(
            json.load(json_file).update(content),
            json_file,
            indent=indent,
            default=default,
            **kwargs,
        )
    if verbose:
        logger.info(f"Data is appended to {filename}.")


def read_json(filename: str, **kwargs) -> Dict[str, Any]:
    with open(filename, "r", encoding="utf-8") as json_file:
        return json.load(json_file, **kwargs)


def write_json(
    content: Dict[str, Any],
    filename: str,
    indent: int = 4,
    default: Callable[[Any], Any] = str,
    verbose: bool = True,
    **kwargs,
):
    filename = os.path.realpath(filename)
    dir = os.path.dirname(os.path.realpath(filename))
    os.makedirs(dir, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(content, json_file, indent=indent, default=default, **kwargs)
    if verbose:
        logger.info(f"Data is written to {filename}.")


def strip_json(content: Dict[str, Any]) -> Dict[str, Any]:
    temp_json = content.copy()

    # Remove keys with None values
    for key, value in list(content.items()):
        if value is None:
            del temp_json[key]

    return temp_json
