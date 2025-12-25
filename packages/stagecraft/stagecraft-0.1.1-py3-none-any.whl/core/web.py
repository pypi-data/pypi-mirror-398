from enum import Enum
from typing import Any, Dict, Optional


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


def get_curl(
    method: HttpMethod,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Any = None,
) -> str:
    curl_cmd = f"curl -X {method.value} '{url}'"
    if headers:
        for key, value in headers.items():
            curl_cmd += f" -H '{key}: {value}'"
    if query_params:
        params_str = "&".join([f"{k}={v}" for k, v in query_params.items()])
        curl_cmd += f" (params: {params_str})"
    if json:
        import json as json_lib

        curl_cmd += f" -d '{json_lib.dumps(json)}'"
    if data:
        curl_cmd += f" -d '{data}'"

    return curl_cmd
