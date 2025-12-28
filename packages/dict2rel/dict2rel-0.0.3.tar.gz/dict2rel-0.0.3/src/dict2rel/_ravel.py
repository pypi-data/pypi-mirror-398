from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from dict2rel._types import JsonObject, JsonValue, Row

from dict2rel._types import ID_SENTINEL, VALUE_SENTINEL


def _parse_int_and_pad_parent(val: str, parent: list[JsonValue]) -> int:
    """Parse a string which is an int and then pad the length
    of parent to ensure the int will be a valid index.
    """
    value = int(val)
    parent.extend(None for _ in range(max(0, value - len(parent) + 1)))
    return value


def inflate(rows: Iterable[Row]) -> list[JsonObject]:
    inflated_rows: list[JsonObject] = []
    for row in rows:
        new_obj: JsonObject = {}
        for k, v in row.items():
            if k == ID_SENTINEL:
                continue

            if "." in k:
                _rebuild_nesting_and_place_value(new_obj, tuple(k.split(".")), v)
            else:
                new_obj[k] = v

        inflated_rows.append(new_obj)
    return inflated_rows


def ravel(tables: dict[str, Iterable[Row]]) -> list[JsonObject]:
    # First, we need to reconstruct any nested dicts on all rows.
    id_to_value: dict[tuple[str, ...], JsonValue] = {}
    for rows in tables.values():
        for row in rows:
            id_to_value[tuple(row[ID_SENTINEL].split("."))] = _rebuild_dicts(row)

    # Figure out what is the most nested id and work from there up,
    # reconstructing the original values.
    most_nested = sorted(id_to_value, reverse=True)
    for parts in most_nested:
        if len(parts) <= 1:
            continue

        # Find the longest prefix id which exists in the lookup
        longest = (parts[0],)  # this has to be there
        for i in range(len(parts) - 1):
            if parts[:i] in id_to_value:
                longest = parts[:i]

        if longest not in id_to_value:
            id_to_value[longest] = {}

        _rebuild_nesting_and_place_value(
            id_to_value[longest], parts[len(longest) :], id_to_value[parts]
        )

        # We've added this thing to its parent, so we can remove it
        # from the index. The bonus of this is that anything left at the
        # end must be a root/original row.
        del id_to_value[parts]

    # Depending on nesting and whether stubs existed for ancestors, the
    # results may be out of order. For example, if the * table was
    # dropped because it was empty, then we don't have stubs for the
    # top-level objects with IDs like 0, 1, etc. They'll get recreated
    # in this process, but if 1 was really nested, then it's descendant
    # gets sorted first above and thus the stub for 1 gets created before
    # the stub for 0, thus putting them out of order.
    return [value for _, value in sorted(id_to_value.items(), key=lambda tup: tup[0])]


def _rebuild_dicts(row: Row) -> JsonValue:
    """Take a row and rebuild any nested dicts that are present, remove
    the _id field, and handle any value-only rows. Rebuilding rows involves
    taking "name.first" and changing it back into {"name": {"first": ...}}.
    """
    # _id has to be there, so this must be a "value" row if there's
    # only two values and the value sentinel is present.
    if len(row) == 1 + 1 and VALUE_SENTINEL in row:
        return row[VALUE_SENTINEL]

    new_obj: JsonObject = {}
    for key, value in row.items():
        if "." in key:
            parts = key.split(".")
            pointer = new_obj

            # Build any missing levels
            for part in parts[:-1]:
                if part not in pointer:
                    pointer[part] = {}

                pointer = pointer[part]

            # Assign the value to that last part
            pointer[parts[-1]] = value
        elif key != ID_SENTINEL:
            new_obj[key] = value

    return new_obj


def _rebuild_nesting_and_place_value(
    parent: JsonValue, path_to_build: tuple[str, ...], value_at_path: JsonValue
) -> JsonValue:
    """Build any missing layers referenced by ``path_to_build`` in
    ``parent``. Once rebuilt, place ``value_at_path`` there.

    >>> _rebuild_nesting_and_place_value(
    ...     {"foo": "bar"}, ["path1", "0", "path2"], "the value"
    ... )
    {
        "foo": "bar",
        "path1": [
            {
                "path2": "the value"
            }
        ]
    }
    """
    # Build the layers that are missing between the closest parent
    # we found in the index and what is specified by this _id.
    for i in range(len(path_to_build) - 1):
        # The type of the current part being added is based on the
        # next part. If the next part is a numeric value, then this
        # thing we're adding must be a list. If it is a list, then make
        # sure it is long enough to handle the index we're setting.
        cur = path_to_build[i]
        _next = path_to_build[i + 1]
        next_type = list if _next.isdigit() else dict

        if cur.isdigit():
            value = _parse_int_and_pad_parent(cur, parent)
            if not isinstance(parent[value], next_type):
                parent[value] = next_type()

            parent = parent[value]
        else:
            if cur not in parent or not isinstance(parent[cur], next_type):
                parent[cur] = next_type()

            parent = parent[cur]

    # We've built the intervening levels, so we can go ahead and
    # assign the value of interest to what we've built.
    if path_to_build[-1].isdigit():
        value = _parse_int_and_pad_parent(path_to_build[-1], parent)
        parent[value] = value_at_path
    else:
        parent[path_to_build[-1]] = value_at_path
