from datetime import datetime


def get_timestamp(format: str = "%Y%m%d%H%M%S") -> str:
    return datetime.now().strftime(format)


def get_current_date() -> str:
    return get_timestamp("%d %B %Y")
