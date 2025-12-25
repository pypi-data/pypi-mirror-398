# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Type, Union
from uuid import UUID

# Core Source imports
from core_common_data_types.type_definitions import EnumT

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                  Validator methods                                                   #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def validate_is_uuid(value: Union[str, UUID]) -> UUID:
    """
    Validates that the value is a valid UUID.
    """
    return value if isinstance(value, UUID) else UUID(value)


def validate_enum_name(value: Union[str, EnumT], type_: Type[EnumT]) -> EnumT:
    """
    Retrieve the Enum value by its name.
    """
    return type_[value] if value in [entry.name for entry in type_] else value  # type: ignore
