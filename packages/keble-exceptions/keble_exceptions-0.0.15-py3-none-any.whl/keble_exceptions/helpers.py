from typing import List

from .exceptions import KebleException


def raise_if_not(condition: bool | List[bool], exception: KebleException):
    if isinstance(condition, list):
        condition = all(condition)  # Ensure all conditions are True
    if not condition:
        raise exception
