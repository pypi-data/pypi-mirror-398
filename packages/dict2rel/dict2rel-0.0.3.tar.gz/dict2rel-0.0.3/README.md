# dict2rel

[![PyPI - Version](https://img.shields.io/pypi/v/dict2rel.svg)](https://pypi.org/project/dict2rel)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dict2rel.svg)](https://pypi.org/project/dict2rel)
[![codecov](https://codecov.io/github/BlendingJake/Dict2Rel/graph/badge.svg?token=1RXWN2Y0LW)](https://codecov.io/github/BlendingJake/Dict2Rel)

`dict2rel` is a Python library which can transform JSON with any level of nesting into one or more tables which contain enough information that the tables can be modified and then converted back to the nested JSON format. Essentially, JSON can be converted to relational tables and then back.

-----

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation - GitHub Pages](https://blendingjake.github.io/Dict2Rel/)
- [License](#license)

## Installation

```console
pip install dict2rel
```

## Quick Start

```python
from dict2rel import dict2rel
import pandas as pd  # you can also use polars.DataFrame

tables = dict2rel(
    [
        {
            "name": "relay-settings",
            "version": {
                "major": 1,
                "minor": 12,
                "patch": 1
            },
            "settings": [
                {
                    "key": "tempo",
                    "value": 12
                },
                {
                    "key": "delay",
                    "value": 14
                }
            ]
        },
        {
            "name": "response-settings",
            "version": {
                "major": 12,
                "minor": 0,
                "patch": 3
            },
            "settings": [
                {
                    "key": "throttle",
                    "value": "always"
                },
                {
                    "key": "burst",
                    "value": 0.43
                }
            ]
        },
    ],
    pd.DataFrame  # the tables will be of this type
)
```

`tables` will end up being a `dict` of the following tables:

### `*`

| name | version.major | version.minor | version.patch | _id |
| ---- | ------------- | ------------- | ------------- | --- |
| relay-settings | 1 | 12 | 1 | 0 |
| response-settings | 12 | 0 | 3 | 1 |

### `*.settings`

| key | value | _id |
| --- | ----- | --- |
|    tempo |     12 | 0.settings.0 |
|    delay |     14 | 0.settings.1 |
| throttle | always | 1.settings.0 |
|    burst |   0.43 | 1.settings.1 |

These tables can then be modified, maybe by adding a new column:

```python
tables["*.settings"]["added"] = ["2025-12-18"] * len(tables["*.settings"])
```

and then converted back to nested JSON:

```python
from dict2rel import rel2dict

transformed_data = rel2dict(tables)
```

which gives the following JSON:

```json
[
    {
        "name": "relay-settings", 
        "version": {"major": 1, "minor": 12, "patch": 1}, 
        "settings": [
            {"key": "tempo", "value": 12, "added": "2025-12-18"}, 
            {"key": "delay", "value": 14, "added": "2025-12-18"}
        ]
    }, 
    {
        "name": "response-settings", 
        "version": {"major": 12, "minor": 0, "patch": 3}, 
        "settings": [
            {"key": "throttle", "value": "always", "added": "2025-12-18"}, 
            {"key": "burst", "value": 0.43, "added": "2025-12-18"}
        ]
    }
]
```

## License

`dict2rel` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Development

Make sure to run `hatch fmt`, `hatch run black:run`, `hatch run test:run`, and `hatch run docs:build`.
