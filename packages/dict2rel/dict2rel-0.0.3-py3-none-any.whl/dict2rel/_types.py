from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Dict, Iterable, List, Union

FieldPath = List[Union[int, str]]

JsonPrimitive = Union[int, float, str, bool, None]
JsonValue = Union[JsonPrimitive, List["JsonValue"], "JsonObject"]
JsonObject = Dict[str, JsonValue]
Row = Dict[str, JsonPrimitive]

ID_SENTINEL = "_id"
VALUE_SENTINEL = "_value"


@dataclass
class Field:
    field: str
    types: set[type]


class Schema(dict[str, Field]):
    def add_or_update(self, field: str, tp: type):
        if field not in self:
            self[field] = Field(field, set())

        self[field].types.add(tp)


@dataclass(kw_only=True)
class UnravelOptions:
    """Options for configuring how an object is unraveled and
    expanded into one or more tables. Used by :func:`dict2rel.dict2rel`.
    """

    fields_to_expand: Iterable[str] | None = None
    """Field paths which point to nested objects which should be expanded
    to their own tables instead of being flattened inline. Essentially,
    this will treat the nested objects as if they were nested lists.

    The field paths should ignore any nested arrays and mirror field paths
    seen in query languages like ElasticSearch's DSL.

    >>> data = [
    ...     {
    ...         "addresses": {
    ...
    ...         }
    ...     }
    ... ]
    >>> UnravelOptions(
    ...     fields_to_expand=["addresses"]  # not *.addresses
    ... )

    .. versionadded:: 0.0.2

    .. versionchanged:: 0.0.3
        :func:`~dict2rel.rel2dict` will now correctly reconstruct the
        original object even when specific fields were set to be expanded.
        Fields which were objects are no longer reconstructed as lists of
        a single object.
    """

    marker: str | None = None
    """The value, if any, which will be placed in a column when
    the value was a list and therefore got expanded to its own table.
    By default, the column is not included.

    String interpolation is supported and the provided values are:

    * ``field: str`` - the name of the field being expanded
    * ``id: str`` - the ``_id`` of the current row
    * ``len: int`` - the length of the nested list
    * ``sheet: str`` - the name of the sheet where the nested values
      were placed

    An example marker value would be: ``"{len} values placed in {sheet}"``.
    """

    support_heterogeneous_data: bool = False
    """By default, the expectation is that the value for a given field path
    has the same type across all objects. However, that is not always the
    case and that is particularly impactful if the value is sometimes an
    object, which will be flattened inline, and other times a list of objects,
    which will be put in their own sheet.

    By setting this flag, fields which have object values sometimes and list
    values others will be handled consistently and always placed in a
    separate table.

    .. note::
        The produced table names may be different for the same data depending
        on whether this flag is set or not. The data will be reconstructed
        to the same original objects, but the intermediate tables may be named
        differently.

    .. versionadded:: 0.0.3
    """

    @cached_property
    def fields_to_expand_set(self) -> set[str]:
        if self.fields_to_expand:
            return set(self.fields_to_expand)

        return set()
