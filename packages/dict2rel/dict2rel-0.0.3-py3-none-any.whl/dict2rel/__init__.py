""":mod:`dict2rel` is a Python package aimed at aiding situations where you
have highly nested JSON objects and want to either flatten them into a
single table or transform them into multiple tables where nested lists get
broken out into their own sheets; turning a dict into relational tables; and
providing the name.

The library is table-type agnostic and therefore ``pandas.DataFrame``,
``polars.DataFrame``, or any other provider can be used when constructing
the tables. The two previously mentioned types are automatically handled
when converting back from tables into JSON.

>>> from dict2rel import dict2rel, UnravelOptions
>>> tables = dict2rel(
...     {
...         "project": "Alpha-Prime",
...         "version": "1.0.3",
...         "config": {
...             "modules": [
...                 {
...                     "id": "A1",
...                     "status": "active",
...                     "settings": {
...                         "security": {
...                             "encryption_level": 5,
...                             "algorithms": ["AES-256", "SHA-512"],
...                         }
...                     },
...                 },
...                 {
...                     "id": "B2",
...                     "status": "passive",
...                     "settings": {
...                         "security": {
...                             "encryption_level": 0,
...                             "algorithms": ["AES-256"],
...                         }
...                     },
...                 },
...             ]
...         },
...     },
...     UnravelOptions(marker="Expanded {len} results to {sheet}"),
... )
>>> tables
{
    "*": pd.DataFrame([...]),
    "*.config.modules": pd.DataFrame([...]),
    "*.config.modules.*.settings.security.algorithms": pd.DataFrame([...])
}

Where the tables in the example above are as follows.

``*``:
    =========== ======= ======================================== ===
    project     version config.modules                           _id
    =========== ======= ======================================== ===
    Alpha-Prime 1.0.3   Expanded 2 results to \\*.config.modules  0
    =========== ======= ======================================== ===

``*.config.modules``:
    == ======= ================================== ===================================================================== ===================
    id status  settings.security.encryption_level settings.security.algorithms                                          _id
    == ======= ================================== ===================================================================== ===================
    A1 active  5                                  Expanded 2 results to \\*.config.modules.settings.security.algorithms  0.config.modules.0
    B2 passive 0                                  Expanded 1 results to \\*.config.modules.settings.security.algorithms  0.config.modules.1
    == ======= ================================== ===================================================================== ===================

``*.config.modules.*.settings.security.algorithm``:
    =======  =================================================
    _value   _id
    =======  =================================================
    AES-256  0.config.modules.0.settings.security.algorithms.0
    SHA-512  0.config.modules.0.settings.security.algorithms.1
    AES-256  0.config.modules.1.settings.security.algorithms.0
    =======  =================================================

These tables can be converted back to the original JSON by applying :func:`rel2dict`.

>>> from dict2rel import rel2dict
>>> rel2dict(tables)
{
    # original value
}

:mod:`dict2rel` also provides functions for converting JSON into a single
table and then back to JSON with :func:`~dict2rel.flatten` and
:func:`~dict2rel.inflate`.
"""

# SPDX-FileCopyrightText: 2025-present Jacob Morris <blendingjake@gmail.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterable, TypeVar

if TYPE_CHECKING:
    from dict2rel._types import JsonObject, Row

from dict2rel.__about__ import __version__
from dict2rel._errors import ToRowsRequiredError
from dict2rel._ravel import inflate as _inflate
from dict2rel._ravel import ravel as _ravel
from dict2rel._types import UnravelOptions
from dict2rel._unravel import flattener as _flattener
from dict2rel._unravel import unravel as _unravel

__all__ = [
    "__version__",
    "dict2rel",
    "flatten",
    "inflate",
    "rel2dict",
    "ToRowsRequiredError",
    "UnravelOptions",
]
P = TypeVar("P")


def dict2rel(
    obj: list[JsonObject] | JsonObject,
    provider: Callable[[list[Row]], P],
    options: UnravelOptions | None = None,
) -> dict[str, P]:
    """Take a list of (or single) JSON object(s) and convert them to tables using
    the provider of your choice to construct the tables (like Polars, Pandas, etc.).
    Nested arrays of JSON objects will be broken out into their own tables while
    nested objects will be flattened inline. ``options`` can be provided to do things
    like place a marker whenever a list is expanded to a new table instead of dropping
    the column.

    :func:`rel2dict` can be used to convert the results of this function back to
    ``obj``, such that ``rel2dict(dict2rel(obj, ...)) == obj``.

    >>> dict2rel(
    ...     [
    ...         {
    ...             "name": {"first": "John", "last": "Smith"},
    ...             "phones": [
    ...                 {"country": "USA", "number": "1234567890"},
    ...                 {"country": "ESP", "number": "987654321"},
    ...             ],
    ...         }
    ...     ],
    ...     pd.DataFrame,
    ... )
    {
        "*": pd.DataFrame([
            {
                "_id": "0",
                "name.first": "John",
                "name.last": "Smith"
            }
        ]),
        "*.phones": pd.DataFrame([
            {
                "_id": "0.phones.0",
                "country": "USA",
                "number": "1234567890"
            },
            {
                "_id": "0.phones.1",
                "country": "ESP",
                "number": "987654321"
            }
        ])
    }

    .. versionchanged:: 0.0.3
        Rows are no longer produced if they would otherwise be empty (or just
        ``_id``). Tables are no longer produced when there are no rows. Empty
        rows were generated if an object only had one key and it was nested
        such that the values got placed in a separate table.

    :param obj: A :attr:`JSONObject` or list of them
    :param provider: A function which converts a list of rows into a table. Typically,
        this will be a value like ``pandas.DataFrame`` or ``polars.DataFrame``, but
        can be an identity lambda which will return the results as lists of dictionaries.
    :param options: Options to configure how ``obj`` is unraveled, like whether to place
        markers whenever a column is a list which gets expanded to its own table.
    """
    objs = [obj] if isinstance(obj, dict) else obj
    rows: dict[str, list[Row]] = {}
    for sheet, data in _unravel(objs, options or UnravelOptions()):
        if sheet not in rows:
            rows[sheet] = []

        rows[sheet].append(data)

    return {sheet: provider(rs) for sheet, rs in rows.items()}


def flatten(
    obj: list[JsonObject] | JsonObject, provider: Callable[[list[Row]], P]
) -> P:
    """Take a list of objects, or a single dict, and flatten it into a single sheet.
    Unlike :func:`dict2rel`, nested lists are kept on the primary sheet and
    provided unique column names.

    :func:`inflate` can be used to reverse this process such that
    ``inflate(flatten(obj, ...)) == obj``.

    >>> from dict2rel import flatten
    >>> flatten(
    ...     [
    ...         {
    ...             "name": {"first": "John", "last": "Smith"},
    ...             "phones": [
    ...                 {"country": "USA", "number": "1234567890"},
    ...                 {"country": "ESP", "number": "987654321"},
    ...             ],
    ...         }
    ...     ],
    ...     pl.DataFrame,
    ... )
    pl.DataFrame([
        {
            "_id": "0",
            "name.first": "John",
            "name.last": "Smith",
            "phones.0.country": "USA",
            "phones.0.number": "1234567890",
            "phones.1.country": "ESP",
            "phones.1.number": "987654321"
        }
    ])

    :param obj: A :attr:`JSONObject` or list of them
    :param provider: A function which converts a list of rows into a table. Typically,
        this will be a value like ``pandas.DataFrame`` or ``polars.DataFrame``, but
        can be an identity lambda which will return the results as list of dictionaries.
    """
    objs = [obj] if isinstance(obj, dict) else obj
    return provider(list(_flattener(objs)))


def inflate(
    table: P, to_rows: Callable[[P], Iterable[Row]] | None = None
) -> list[JsonObject]:
    """Undo :func:`flatten` and take a sheet with nesting represented by column
    names and inflate it back to a list of dictionaries with actual nesting.

    >>> from dict2rel import inflate
    >>> inflate(
    ...     pl.DataFrame(
    ...         [
    ...             {
    ...                 "name": "Bravo",
    ...                 "version.major": "1",
    ...                 "version.minor": "0",
    ...                 "version.patch": "12",
    ...                 "releases.0.date": "2025-02-12",
    ...                 "releases.0.version": "0.0.1",
    ...                 "releases.1.date": "2025-02-18",
    ...                 "releases.1.version": "0.1.0",
    ...             }
    ...         ]
    ...     )
    ... )
    [{
        'name': 'Bravo',
        'version': {
            'major': '1',
            'minor': '0',
            'patch': '12'
        },
        'releases': [
            {'date': '2025-02-12', 'version': '0.0.1'},
            {'date': '2025-02-18', 'version': '0.1.0'}
        ]
    }]

    :param table: The table to inflate. This can either be a list of dictionaries,
        or a table such as ``pandas.DataFrame`` or ``polars.DataFrame``.
    :param to_rows: A function to convert the table data to dictionaries. This is only
        needed if the data isn't already in that format or the tables are a datatype
        other than ``pandas.DataFrame`` or ``polars.DataFrame``.
    :raise ToRowsRequiredError: If any of the tables aren't lists or a known
        table-type like ``pandas.DataFrame`` or ``polars.DataFrame``.
    """
    rows: Iterable[Row] = _to_rows(to_rows)(table)
    return _inflate(rows)


def rel2dict(
    tables: dict[str, P],
    to_rows: Callable[[P], Iterable[Row]] | None = None,
) -> list[JsonObject]:
    """Take a mapping of tables, likely produced by :func:`dict2rel`, and
    reconstruct the nested JSON from them. The tables themselves can be objects
    like ``pandas.DataFrame`` or ``polars.DataFrame``, or other table-types if
    ``to_rows`` is provided.

    >>> from dict2rel import rel2dict
    >>> rel2dict(
    ...     {
    ...         "*": pl.DataFrame(
    ...             [
    ...                 {
    ...                     "_id": "0",
    ...                     "name": "Acme Corp.",
    ...                     "state": "AZ",
    ...                     "board": "4 board members in *.board",
    ...                 },
    ...                 {
    ...                     "_id": "1",
    ...                     "name": "ZZZ Consulting",
    ...                     "state": "NY",
    ...                     "board": "2 board members in *.board",
    ...                 },
    ...             ]
    ...         ),
    ...         "*.board": pl.DataFrame(
    ...             [
    ...                 {"_id": "0.board.0", "name": "Wile E. Coyote"},
    ...                 {"_id": "0.board.1", "name": "Someone Else"},
    ...                 {"_id": "1.board.0", "name": "Leonhard Euler"},
    ...                 {"_id": "1.board.1", "name": "Carl Gauss"},
    ...             ]
    ...         ),
    ...     }
    ... )
    [
        {
            'name': 'Acme Corp.',
            'state': 'AZ',
            'board': [
                {'name': 'Wile E. Coyote'},
                {'name': 'Someone Else'}
            ]
        },
        {
            'name': 'ZZZ Consulting',
            'state': 'NY',
            'board': [
                {'name': 'Leonhard Euler'},
                {'name': 'Carl Gauss'}
            ]
        }
    ]

    :param tables: A mapping of table names to table data
    :param to_rows: A function to convert the table data to dictionaries. This is only
        needed if the data isn't already in that format or the tables are a datatype
        other than ``pandas.DataFrame`` or ``polars.DataFrame``.
    :raise ToRowsRequiredError: If any of the tables aren't lists or a known
        table-type like ``pandas.DataFrame`` or ``polars.DataFrame``.
    """
    true_to_rows = _to_rows(to_rows)
    return _ravel({sheet: true_to_rows(rows) for sheet, rows in tables.items()})


def _to_rows(
    to_rows: Callable[[P], Iterable[Row]] | None,
) -> Callable[[P], Iterable[Row]]:
    """Take an optional to_rows converter and produce a new converter
    which will fallback and fill handling for pandas and polars.
    """

    def worker(sheet: P) -> Iterable[Row]:
        if to_rows:
            return to_rows(sheet)

        tp = type(sheet)
        if tp.__name__ == "DataFrame":
            if "pandas" in tp.__module__:
                return (row for _, row in sheet.iterrows())
            if "polars" in tp.__module__:
                return sheet.rows(named=True)
        if isinstance(sheet, list):
            return sheet

        raise ToRowsRequiredError

    return worker
