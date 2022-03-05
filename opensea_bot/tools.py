from typing import Any


def delete_duplicates(list_: list[Any]) -> list[Any]:
    return list(dict.fromkeys(list_))


def find_int_in_string(string: str) -> int:
    return int("".join(filter(str.isdigit, string)))
