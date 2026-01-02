from collections.abc import Mapping
from typing import Dict

from clipped.utils.json import orjson_dumps


def sanitize_value(d: Dict, handle_dict: bool = False):
    if isinstance(d, str):
        return d
    if not isinstance(d, Mapping):
        return orjson_dumps(d)
    if not handle_dict:
        return orjson_dumps(d)
    return {d_k: sanitize_value(d_v, handle_dict=True) for d_k, d_v in d.items()}


def sanitize_string_dict(d: Dict[str, str] = None):
    if isinstance(d, Mapping):
        return {d_k: sanitize_value(d_v, handle_dict=False) for d_k, d_v in d.items()}
    return d
