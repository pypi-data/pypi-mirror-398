from __future__ import annotations

from dict2rel._types import FieldPath, JsonValue, Schema


def analyze_schema(
    obj: JsonValue, path: FieldPath, schema: Schema | None = None
) -> Schema:
    """Analyze the schema of an object, recursively, building out
    the provided ``schema`` or creating one if needed. The schema
    contains the path and the types observed for that path.
    """
    if schema is None:
        schema = Schema()

    string_path = ".".join(map(str, path))
    if isinstance(obj, list):
        schema.add_or_update(string_path, list)

        for o in obj:
            analyze_schema(o, path, schema)
    elif isinstance(obj, dict):
        schema.add_or_update(string_path, dict)

        for k, v in obj.items():
            analyze_schema(v, [*path, k], schema)
    else:
        schema.add_or_update(string_path, type(obj))

    return schema
