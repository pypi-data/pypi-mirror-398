#!/usr/bin/env python
from typing import Dict, Any, List, Optional, TypeVar, overload, cast
from collections.abc import MutableMapping, Mapping

T = TypeVar("T")


def additional_properties(data: MutableMapping[str, Any]) -> Dict[str, Any]:
    """
    Recursively traverses a nested dictionary (typically representing a JSON schema) and sets 'additionalProperties' to False for any dictionary containing 'properties' but lacking 'additionalProperties'.

    This mimics the behavior of kubectl schema validation, ensuring that objects with defined properties do not allow unspecified additional properties unless explicitly permitted.

    Args:
        data (MutableMapping[str, Any]): The input dictionary to process.

    Returns:
        Dict[str, Any]: A new dictionary with 'additionalProperties' set to False where appropriate.
    """
    new: Dict[str, Any] = {}
    for k, v in data.items():
        new_v: Any = v
        if isinstance(v, MutableMapping):
            if "properties" in v and "additionalProperties" not in v:
                v["additionalProperties"] = False
            # v is a mutable mapping; help the type checker with a cast
            new_v = additional_properties(cast(MutableMapping[str, Any], v))
        new[k] = new_v
    return new


def replace_int_or_string(data: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Recursively replaces any dictionary entry with a "format" key set to "int-or-string"
    with a JSON Schema "oneOf" construct allowing either a string or integer type.

    Args:
        data (Mapping[str, Any]): The input mapping (typically a JSON-like dictionary)
            to process.

    Returns:
        Dict[str, Any]: A new dictionary with all "int-or-string" formats replaced
            by the appropriate "oneOf" schema.

    Example:
        Input:
            {"foo": {"format": "int-or-string"}, "bar": {"type": "string"}}
        Output:
            {"foo": {"oneOf": [{"type": "string"}, {"type": "integer"}]}, "bar": {"type": "string"}}
    """
    # Handle the "self has format=int-or-string" case first
    if data.get("format") == "int-or-string":
        return {"oneOf": [{"type": "string"}, {"type": "integer"}]}

    new: Dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, Mapping):
            new[k] = replace_int_or_string(cast(Mapping[str, Any], v))
        elif isinstance(v, list):
            lv = cast(list[Any], v)
            out: list[Any] = []
            for x in lv:
                if isinstance(x, Mapping):
                    out.append(replace_int_or_string(cast(Mapping[str, Any], x)))
                else:
                    out.append(x)
            new[k] = out
        else:
            new[k] = v
    return new


def allow_null_optional_fields(
    data: Any,
    parent: Optional[Any] = None,
    grand_parent: Optional[Any] = None,
    key: Optional[str] = None,
) -> Any:
    """
    Recursively traverses a nested data structure (typically representing a JSON Schema)
    and modifies optional fields to allow `null` values.

    For each field with a `"type"` key that is not `"null"` and is not listed as required
    in its grandparent's `"required"` array, the function changes the value of `"type"`
    to a list containing the original type and `"null"` (e.g., `["string", "null"]`).
    This allows the field to accept `null` as a valid value.

    Args:
        data (Any): The input data structure (dict, list, or scalar) to process.
        parent (Optional[Any], optional): The immediate parent of the current data node. Defaults to None.
        grand_parent (Optional[Any], optional): The grandparent of the current data node. Defaults to None.
        key (Optional[str], optional): The key associated with the current data node in its parent. Defaults to None.

    Returns:
        Any: The modified data structure with optional fields allowing `null` values.
    """
    # Mapping case
    if isinstance(data, Mapping):
        m = cast(Mapping[str, Any], data)  # <-- give key/value types
        new: Dict[str, Any] = {}
        for k, v in m.items():  # k: str, v: Any
            if isinstance(v, Mapping):
                mv = cast(Mapping[str, Any], v)
                new[k] = allow_null_optional_fields(mv, m, parent, k)
            elif isinstance(v, list):
                lv = cast(list[Any], v)  # <-- give element type
                new_list: list[Any] = []
                for x in lv:
                    new_list.append(allow_null_optional_fields(x, lv, parent, k))
                new[k] = new_list
            elif isinstance(v, str):
                is_non_null_type: bool = (k == "type") and (v != "null")

                is_required_field = False
                if isinstance(grand_parent, Mapping):
                    gp = cast(Mapping[str, Any], grand_parent)
                    req = gp.get("required")
                    if isinstance(req, list) and key is not None:
                        is_required_field = key in req

                new[k] = (
                    [v, "null"] if (is_non_null_type and not is_required_field) else v
                )
            else:
                new[k] = v
        return new

    # List case
    if isinstance(data, list):
        lv = cast(list[Any], data)  # <-- give element type
        new_list_list: list[Any] = []
        for item in lv:
            new_list_list.append(allow_null_optional_fields(item, lv, parent, key))
        return new_list_list

    # Scalar case
    return data


# overload function signatures for different input types
@overload
def change_dict_values(
    d: Mapping[str, Any], prefix: str, version: str
) -> Dict[str, Any]: ...
@overload
def change_dict_values(d: list[Any], prefix: str, version: str) -> list[Any]: ...
@overload
def change_dict_values(d: Any, prefix: str, version: str) -> Any: ...


def change_dict_values(d: Any, prefix: str, version: str) -> Any:
    """
    Recursively traverses a dictionary, list, or scalar value, modifying values associated with the "$ref" key.

    For each "$ref" string value:
        - If `version` is less than "3", prepends the given `prefix` to the value.
        - If `version` is "3" or greater, replaces "#/components/schemas/" in the value with an empty string and appends ".json".

    Other values are left unchanged. The function handles nested dictionaries and lists.

    Args:
        d (Any): The input data structure (dict, list, or scalar) to process.
        prefix (str): The prefix to prepend to "$ref" values for versions less than "3".
        version (str): The version string used to determine how "$ref" values are modified.

    Returns:
        Any: The processed data structure with updated "$ref" values.
    """
    # Mapping case
    if isinstance(d, Mapping):
        m = cast(Mapping[str, Any], d)
        new: Dict[str, Any] = {}
        for k, v in m.items():  # k: str, v: Any
            if isinstance(v, Mapping):
                mv = cast(Mapping[str, Any], v)
                new[k] = change_dict_values(mv, prefix, version)
            elif isinstance(v, list):
                lv = cast(list[Any], v)
                new_list: list[Any] = []
                for x in lv:
                    new_list.append(change_dict_values(x, prefix, version))
                new[k] = new_list
            elif isinstance(v, str):
                if k == "$ref":
                    new[k] = (
                        f"{prefix}{v}"
                        if (version < "3")
                        else v.replace("#/components/schemas/", "") + ".json"
                    )
                else:
                    new[k] = v
            else:
                new[k] = v
        return new

    # List case
    if isinstance(d, list):
        lv = cast(list[Any], d)
        out: list[Any] = []
        for x in lv:
            out.append(change_dict_values(x, prefix, version))
        return out

    # Scalar case
    return d


def append_no_duplicates(obj: Dict[str, List[T]], key: str, value: T) -> None:
    """
    Appends a value to the list at the specified key in the dictionary, ensuring no duplicates.

    If the key does not exist in the dictionary, a new list is created.
    The value is only appended if it is not already present in the list.

    Args:
        obj (Dict[str, List[T]]): The dictionary containing lists as values.
        key (str): The key whose list should be appended to.
        value (T): The value to append if not already present.

    Returns:
        None
    """
    if key not in obj:
        obj[key] = []
    if value not in obj[key]:
        obj[key].append(value)
