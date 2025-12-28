import os
from datetime import datetime
from typing import List, Optional


def get_dated_filename(
    file_path, suffix: str = "", sep: str = "_", format: str = "%Y%m%d%H%M%S"
) -> str:
    base, ext = os.path.splitext(file_path)
    file_path = f"{base}{sep}{datetime.now().strftime(format)}{sep}{suffix}{ext}"
    return file_path


def get_files(path: str, endswith: Optional[str] = None) -> List[str]:
    return [
        i
        for i in os.listdir(path)
        if os.path.isfile(os.path.join(path, i)) and (endswith is None or i.endswith(endswith))
    ]


def get_folders(path: str) -> List[str]:
    return [i for i in os.listdir(path) if os.path.isdir(os.path.join(path, i))]


def get_unique_filename(file_path: str) -> str:
    base, ext = os.path.splitext(file_path)
    counter = 1

    while os.path.exists(file_path):
        file_path = f"{base}({counter}){ext}"
        counter += 1

    return file_path
