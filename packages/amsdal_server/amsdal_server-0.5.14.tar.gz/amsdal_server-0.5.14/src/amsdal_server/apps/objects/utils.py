from typing import Any

from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.enums import Versions


def apply_version_to_address(
    address: Address,
    version_id: str | None,
    *,
    all_versions: bool = False,
) -> Address:
    object_version: str | Versions
    class_version: str | Versions

    if all_versions:
        object_version = Versions.ALL
        class_version = Versions.ALL
    elif version_id:
        object_version = version_id or address.object_version
        class_version = address.class_version
    else:
        object_version = Versions.LATEST
        class_version = Versions.LATEST

    address.object_version = object_version
    address.class_version = class_version

    return address


def is_fk_object_id(object_id: Any) -> bool:
    return isinstance(object_id, dict) and 'ref' in object_id


def normalize_address(address: str) -> str:
    """
    Converts lakehouse-like address to the standard address format.

    Args:
        address (str): The lakehouse-like address.

    Returns:
        str: The standard address format.
    """
    _address = Address.from_string(address)
    _object_id = _address.object_id

    if is_fk_object_id(_object_id):
        _object_id = _object_id['ref']['object_id']  # type: ignore[call-overload]
    elif isinstance(_object_id, list):
        _object_id = [_id['ref']['object_id'] if is_fk_object_id(_id) else _id for _id in _object_id]

    return Address(
        resource=_address.resource,
        object_id=_object_id,
        object_version=_address.object_version,
        class_name=_address.class_name,
        class_version=_address.class_version,
    ).to_string()
