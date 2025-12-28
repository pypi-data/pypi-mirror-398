from __future__ import annotations

from dataclasses import replace
from typing import Iterator, NamedTuple

from dict2rel._schema import analyze_schema as _analyze_schema
from dict2rel._types import (
    ID_SENTINEL,
    VALUE_SENTINEL,
    FieldPath,
    JsonObject,
    JsonValue,
    Row,
    UnravelOptions,
)

PartialMarker = NamedTuple(
    "PartialMarker", (("field", str), ("len", int), ("path", FieldPath))
)


def _determine_sheet_name(parts: FieldPath) -> str:
    sheet_parts = ["*" if isinstance(part, int) else part for part in parts]

    if len(sheet_parts) > 1 and sheet_parts[-1] == "*":
        sheet_parts = sheet_parts[:-1]

    return ".".join(sheet_parts)


def _determine_simple_field_path(parts: FieldPath) -> str:
    """Determine what the simple (almost ElasticSearch style)
    field path is for a number of parts. The result will strip
    any levels of array nesting.

    >>> _determine_simple_field_path((0, "addresses", 0))
    "addresses"

    >>> _determine_simple_field_path((1, "releases", 1, "version", "major"))
    "releases.version.major"
    """
    return ".".join(filter(lambda v: isinstance(v, str), parts))


def flattener(obj: list[JsonObject]) -> Iterator[Row]:
    """Take a list of :attr:`JsonObject` and flatten all nesting to a
    dictionary where the values will be singletons. Yield out those
    flattened rows.
    """
    root_objs: dict[int | str, list[tuple[FieldPath, Row]]] = {}
    for fp, true_obj in _unravel(obj, [], UnravelOptions()):
        if fp[0] not in root_objs:
            root_objs[fp[0]] = []

        root_objs[fp[0]].append((fp, true_obj))

    for root_id, objs in root_objs.items():
        sorted_objs = sorted(objs, key=lambda x: x[0])
        root_obj: Row = {ID_SENTINEL: str(root_id), **sorted_objs[0][1]}

        for child_path, child_obj in sorted_objs[1:]:
            # Remove first part of path as it will be root_id
            child_id = ".".join(map(str, child_path[1:]))

            if len(child_obj) == 1 and VALUE_SENTINEL in child_obj:
                root_obj[child_id] = child_obj[VALUE_SENTINEL]
            else:
                root_obj.update({f"{child_id}.{k}": v for k, v in child_obj.items()})

        yield root_obj


def unravel(
    obj: list[JsonObject], options: UnravelOptions
) -> Iterator[tuple[str, Row]]:
    made_homogeneous: set[str] = set()
    if options.support_heterogeneous_data is True:
        new_options = replace(options)
        if options.fields_to_expand:
            new_options.fields_to_expand = list(options.fields_to_expand)
        else:
            new_options.fields_to_expand = []

        schema = _analyze_schema(obj, [])
        for field in schema.values():
            if field.field and dict in field.types and list in field.types:
                new_options.fields_to_expand.append(field.field)
                made_homogeneous.add(field.field)

        options = new_options

    for fp, true_obj in _unravel(obj, [], options):
        _id = ".".join(map(str, fp))
        true_obj[ID_SENTINEL] = _id

        if (simple := _determine_simple_field_path(fp)) in made_homogeneous:
            sheet = simple
        else:
            sheet = _determine_sheet_name(fp)

        for k, v in true_obj.items():
            if isinstance(v, PartialMarker) and options.marker:
                true_obj[k] = options.marker.format(
                    field=v.field,
                    id=_id,
                    len=v.len,
                    sheet=_determine_sheet_name(v.path),
                )

        # Only yield the row data if there is actually data
        if len(true_obj) > 1:
            yield sheet, true_obj


def _unravel(
    obj: JsonValue, path: FieldPath, options: UnravelOptions
) -> Iterator[tuple[FieldPath, Row]]:
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _unravel(v, [*path, i], options)
    elif isinstance(obj, dict):
        # # If the object at this path should be expanded, then add a 0
        # # to the path which will ensure it gets placed on its own sheet
        # if _determine_simple_field_path(path) in options.fields_to_expand_set:
        #     path = [*path, 0]

        new_obj: Row = {}
        for k, v in obj.items():
            if isinstance(v, list):
                new_path: FieldPath = [*path, k]
                yield from _unravel(v, new_path, options)

                if options.marker is not None:
                    new_obj[k] = PartialMarker(field=k, len=len(v), path=new_path)
            elif isinstance(v, dict):
                for fp, nested_obj in _unravel(v, [*path, k], options):
                    if (
                        all(isinstance(part, str) for part in fp[len(path) + 1 :])
                        and _determine_simple_field_path(fp)
                        not in options.fields_to_expand_set
                    ):
                        for kk, vv in nested_obj.items():
                            new_obj[
                                ".".join(
                                    [
                                        k,
                                        *list(map(str, fp[len(path) + 1 :])),
                                        kk,
                                    ]
                                )
                            ] = vv
                    else:
                        yield fp, nested_obj
            else:
                new_obj[k] = v

        yield path, new_obj
    else:
        yield path, {VALUE_SENTINEL: obj}
