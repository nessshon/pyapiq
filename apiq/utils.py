import json
import string
import typing as t

__all__ = [
    "extract_path_keys",
    "format_path",
    "try_parse_json",
]


def extract_path_keys(path: str) -> t.Set[str]:
    formatter = string.Formatter()
    return {name for _, name, _, _ in formatter.parse(path) if name}


def format_path(path: str, args: t.Mapping[str, t.Any]) -> str:
    return path.format(**args)


def try_parse_json(text: str) -> t.Any:
    try:
        return json.loads(text)
    except (Exception,):
        return text
