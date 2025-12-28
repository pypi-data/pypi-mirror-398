import re
from typing import Any, Callable, Optional


def camel_to_snake_case(string: str) -> str:
    output_str = []
    for index, char in enumerate(string):
        if char.isupper() and index > 0:
            output_str.append("_")
        output_str.append(char.lower())
    return "".join(output_str)


def camel_to_spaced(camel_case_str: str) -> str:
    if not camel_case_str:
        return ""
    spaced_str = camel_case_str[0].upper()
    for char in camel_case_str[1:]:
        if char.isupper():
            spaced_str += " " + char
        else:
            spaced_str += char
    return spaced_str


def snake_to_camel_case(string: str, pascal: bool = False) -> str:
    string = string.strip("_")
    if not string:
        return ""
    words = string.split("_")
    edited = "".join([word.title() for word in words])
    if pascal:
        return edited
    if len(edited) == 1:
        return edited.lower()
    return edited[0].lower() + edited[1:]


def spaced_to_camel(spaced_str: str) -> str:
    if not spaced_str:
        return ""
    words = spaced_str.split()
    if not words:
        return ""
    camel_case = words[0].lower() + "".join(word.capitalize() for word in words[1:])
    return camel_case


def anti_capitalize(string: str) -> str:
    if not string:
        return ""
    return string[0].lower() + string[1:]


def capitalize(string: str) -> str:
    if not string:
        return ""
    return string[0].upper() + string[1:]


def dstr(
    data: dict,
    sep: Optional[str] = "\n",
    keys: bool = True,
) -> str:
    text = ""
    items = data.items()
    if keys:
        for idx, (k, v) in enumerate(items):
            text += f"{k}: {v}{(sep if idx + 1 < len(items) else '')}"
    else:
        for idx, (_, v) in enumerate(items):
            text += f"{v}{(sep if idx + 1 < len(items) else '')}"
    return text


def lstr(
    data: list,
    sep: Optional[str] = "\n",
    index: bool = False,
    apply: Optional[Callable[[Any], Any]] = None,
):
    text = ""
    for idx, item in enumerate(data):
        start = f"[{idx}] " if index else ""
        item = item if apply is None else apply(item)
        text += f"{start}{item}{(sep if idx + 1 < len(data) else '')}"
    return text


def clear_string(string: str) -> str:
    # Remove newlines
    string = re.sub(r"\n", " ", string)
    # For excel, remove line breaks
    string = re.sub("_x000D_", " ", string)
    # Remove multiple whitespaces
    string = re.sub(r"\s+", " ", string)
    # Remove leading and trailing spaces
    string = string.strip()
    return string
