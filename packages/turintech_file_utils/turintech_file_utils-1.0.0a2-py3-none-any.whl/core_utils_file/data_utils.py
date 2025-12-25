"""
This module implements useful methods for data treatment.
"""

# pylint: disable=too-many-return-statements
# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeVar
from uuid import UUID

# Internal libraries
from pydantic import BaseModel, SecretStr

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "join_values",
    "list_mapping",
    "optional_list_mapping",
    "get_current_datetime",
    "ISO_DATA_FORMAT",
    "iso_format",
    "iso_format_optional",
    "serialize_data",
]

from core_common_data_types import PropertyBaseModel

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                   Internal types                                                     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

MappableT = TypeVar("MappableT")
MappedT = TypeVar("MappedT")

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                      Constants                                                       #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

# ISO_DATA_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%f%z"
ISO_DATA_FORMAT: str = "%Y-%m-%dT%H:%M:%SZ"


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                    Multi-purpose                                                     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def join_values(values: List[Optional[str]], union: str = "") -> str:
    """
    Joins all the strings in the list by means of the string indicated in "union", filtering those null or empty values.
    """
    return union.join(list(filter(lambda value: value, values)))  # type: ignore


def list_mapping(mapper: Callable[[MappableT], MappedT], values: List[MappableT]) -> List[MappedT]:
    return [mapper(value) for value in values]


def optional_list_mapping(
    mapper: Callable[[MappableT], MappedT], values: Optional[List[MappableT]] = None
) -> Optional[List[MappedT]]:
    return [mapper(value) for value in values] if values else None


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                  Related with time                                                   #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_current_datetime() -> datetime:
    """
    Returns the current datetime.
    """
    return datetime.now(timezone.utc)


def iso_format(data: datetime) -> str:
    return data.strftime(ISO_DATA_FORMAT)


def iso_format_optional(data: Optional[datetime]) -> Optional[str]:
    return iso_format(data=data) if data else None


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                   Serializing data                                                   #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def serialize_data(data: Any, date_format: str = ISO_DATA_FORMAT, by_name: bool = False, **kwargs_model):
    """
    Serialize any type of data.
    """
    kwargs = {"date_format": date_format, "by_name": by_name}
    if isinstance(data, dict):
        return {
            serialize_data(key, **kwargs): serialize_data(value, **kwargs)  # type: ignore
            for key, value in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [serialize_data(data=value, **kwargs) for value in data]  # type: ignore
    if isinstance(data, datetime):
        return data.strftime(date_format)
    if isinstance(data, Enum):
        return data.name if by_name else data.value
    if isinstance(data, PropertyBaseModel):
        return serialize_data(data=data.dict_prop(), **kwargs)  # type: ignore
    if isinstance(data, BaseModel):
        kwargs_model.update({"by_alias": not by_name})
        return serialize_data(data=data.model_dump(**kwargs_model), **kwargs)  # type: ignore
    if isinstance(data, (type, Path, UUID)):
        return str(data)
    return data.get_secret_value() if isinstance(data, SecretStr) else data
