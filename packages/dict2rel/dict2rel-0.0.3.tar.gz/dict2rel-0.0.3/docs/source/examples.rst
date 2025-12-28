Examples
=========


Nested JSON to tables
----------------------

The original use-case for :mod:`dict2rel` was taking a list of JSON objects with lots of nesting
and flattening them into tables, one table for each field-path of a nested list, while maintaining
a way to reconstruct the original list again after transformations had taken place. :func:`~dict2rel.dict2rel`
is provided to accomplish this goal and takes one or more JSON objects and will produce one or more
tables. The data-type of the tables is dependent on the ``provider`` argument, which must be supplied
and can be values like ``pd.DataFrame``, ``pl.DataFrame``, or simply ``lambda rows: rows``. For example,
if you have the following JSON:

.. code-block:: json

    {
        "catalog_id": "CAT001",
        "name": "Tech Skill Bootcamp",
        "courses": [
            {
                "course_id": "CS101",
                "title": "Introduction to Programming",
                "instructor": "Dr. Alex Lee",
                "modules": [
                    {
                        "module_id": 1,
                        "name": "Fundamentals",
                        "lessons": [
                            "Setting up the environment",
                            "Basic data types",
                            "Control flow (if/else)"
                        ]
                    },
                    {
                        "module_id": 2,
                        "name": "Data Structures",
                        "lessons": [
                            "Lists and Tuples",
                            "Dictionaries and Sets"
                        ]
                    }
                ]
            },
            {
                "course_id": "WD201",
                "title": "Web Development Basics",
                "instructor": "Ms. Jamie Chen",
                "modules": [
                    {
                        "module_id": 1,
                        "name": "HTML & CSS",
                        "lessons": [
                            "Structuring content with HTML5",
                            "Styling with CSS Grid"
                        ]
                    }
                ]
            }
        ]
    }


>>> from dict2rel import dict2rel
>>> import pandas as pd
>>> tables = dict2rel(json_data, pd.DataFrame)
>>> tables
{
    '*.courses.*.modules.*.lessons': pd.DataFrame([...])
    '*.courses.*.modules': pd.DataFrame([...])
    '*.courses': pd.DataFrame([...])
    '*': pd.DataFrame([...])
}

where the tables look like:

``*``:
    ========== =================== ===
    catalog_id name                _id
    ========== =================== ===
    CAT001     Tech Skill Bootcamp 0
    ========== =================== ===

``*.courses``:
    ========= =========================== ============== ===========
    course_id title                       instructor     _id
    ========= =========================== ============== ===========
    CS101     Introduction to Programming Dr. Alex Lee   0.courses.0
    WD201     Web Development Basics      Ms. Jamie Chen 0.courses.1
    ========= =========================== ============== ===========

``*.courses.*.modules``:
    ========= =============== =====================
    module_id name            _id
    ========= =============== =====================
    1         Fundamentals    0.courses.0.modules.0
    2         Data Structures 0.courses.0.modules.1
    1         HTML & CSS      0.courses.1.modules.0
    ========= =============== =====================

``*.courses.*.modules.*.lessons``:
    ============================== ===============================
    _value                         _id
    ============================== ===============================
    Setting up the environment     0.courses.0.modules.0.lessons.0
    Basic data types               0.courses.0.modules.0.lessons.1
    Control flow (if/else)         0.courses.0.modules.0.lessons.2
    Lists and Tuples               0.courses.0.modules.1.lessons.0
    Dictionaries and Sets          0.courses.0.modules.1.lessons.1
    Structuring content with HTML5 0.courses.1.modules.0.lessons.0
    Styling with CSS Grid          0.courses.1.modules.0.lessons.1
    ============================== ===============================

    This last table varies a little in format from the others due the
    ``_value`` key which indicates that the list was of singletons and
    not nested objects.

Now, we can modify these tables if we'd like. For example, lets add the number
of credits each course is:

>>> tables["*.courses"]["credits"] = [2, 3]

If we tried to do that in the original JSON, we'd have to do something like the
following, which involves a lot more indexing and for which there isn't an easy
way to add a new column to all of the objects at a certain level.

>>> json_data["courses"][0]["credits"] = 2
>>> json_data["courses"][1]["credits"] = 3


Tables back to JSON
--------------------

:mod:`dict2rel` also provides a way to take those flattened tables and convert them back
to the nested JSON with :func:`dict2rel.rel2dict`. Applying that to the example we modified
above gives the following, which has been shortened just to highlight the new fields we added:

.. code-block:: json

    [
        {
            "catalog_id": "CAT001", 
            "name": "Tech Skill Bootcamp", 
            "courses": [
                {
                    "course_id": "CS101", 
                    "title": "Introduction to Programming", 
                    "instructor": "Dr. Alex Lee", 
                    "credits": 2, 
                    "modules": [

                    ]
                }, 
                {
                    "course_id": "WD201", 
                    "title": "Web Development Basics", 
                    "instructor": "Ms. Jamie Chen", 
                    "credits": 3, 
                    "modules": [

                    ]
                }
            ]
        }
    ]


JSON to a single table
-----------------------

Now, sometimes you have a highly nested JSON object, but just want a single table.
:mod:`dict2rel` also support this scenario with :func:`dict2rel.flatten`. Similar to
:func:`dict2rel.dict2rel`, it takes one or more JSON objects and a provider argument.
Unlike :func:`~dict2rel.dict2rel`, it will only return a single table objects.

>>> from dict2rel import flatten
>>> table = flatten(json_data, pd.DataFrame)  # data from earlier example
>>> table
pd.DataFrame([...])

=== ========== =================== =================== =========================== ==================== ============================= ======================== ============================= ============================= ============================= ============================= ======================== ============================= ============================= =================== ====================== ==================== ============================= ======================== ==============================  =============================
_id catalog_id name                courses.0.course_id courses.0.title             courses.0.instructor courses.0.modules.0.module_id courses.0.modules.0.name courses.0.modules.0.lessons.0 courses.0.modules.0.lessons.1 courses.0.modules.0.lessons.2 courses.0.modules.1.module_id courses.0.modules.1.name courses.0.modules.1.lessons.0 courses.0.modules.1.lessons.1 courses.1.course_id courses.1.title        courses.1.instructor courses.1.modules.0.module_id courses.1.modules.0.name courses.1.modules.0.lessons.0   courses.1.modules.0.lessons.1
=== ========== =================== =================== =========================== ==================== ============================= ======================== ============================= ============================= ============================= ============================= ======================== ============================= ============================= =================== ====================== ==================== ============================= ======================== ==============================  =============================
0   CAT001     Tech Skill Bootcamp CS101               Introduction to Programming Dr. Alex Lee         1                             Fundamentals             Setting up the environment    Basic data types              Control flow (if/else)        2                             Data Structures          Lists and Tuples              Dictionaries and Sets         WD201               Web Development Basics Ms. Jamie Chen       1                             HTML & CSS               Structuring content with HTML5  Styling with CSS Grid
=== ========== =================== =================== =========================== ==================== ============================= ======================== ============================= ============================= ============================= ============================= ======================== ============================= ============================= =================== ====================== ==================== ============================= ======================== ==============================  =============================

:func:`dict2rel.inflate` provides the complement to :func:`~dict2rel.flatten` as :func:`~dict2rel.rel2dict`
does for :func:`dict2rel.dict2rel`.


Heterogeneous data
------------------

Heterogeneous means diverse or varied. In the context of :mod:`dict2rel`, this refers to
fields where the value has different types across objects. In particular, the situation
where the value is sometimes an object and other times a list of objects stands out as
the object will be flattened inline and the list of objects will be placed in a separate
table. This can result in data for the same field being placed in two different places.

To address this, :attr:`dict2rel.UnravelOptions.support_heterogeneous_data` can be set.
When it is, a pass will be done to analyze the data and detect these mismatched type
scenarios. Then, the fields will be handled consistently and the data will always be
placed in a separate table. See the examples below to contrast the flag being set versus
not set.

.. code-block:: json
    :caption: Data for examples below

    [
        {
            "addresses": {
                "address1": "101 North Street",
                "city": "Waco",
                "state": "Texas",
                "zip": "76711",
            }
        },
        {
            "addresses": [
                {
                    "address1": "500 W 6th St",
                    "city": "Waterloo",
                    "state": "Iowa",
                    "zip": "50701",
                }
            ]
        }
    ]

With ``support_heterogeneous_data = False``:

* ``*``

  +--------------------+----------------+-----------------+---------------+-----+
  | addresses.address1 | addresses.city | addresses.state | addresses.zip | _id |
  +====================+================+=================+===============+=====+
  | 101 North Street   | Waco           | Texas           | 76711         | 0   |
  +--------------------+----------------+-----------------+---------------+-----+

* ``*.addresses``

  +--------------+----------+-------+-------+---------------+
  | address1     | city     | state | zip   | _id           |
  +==============+==========+=======+=======+===============+
  | 500 W 6th St | Waterloo | Iowa  | 50701 | 1.addresses.0 |
  +--------------+----------+-------+-------+---------------+

With ``support_heterogeneous_data = True``

* ``addresses``

  +------------------+----------+-------+-------+---------------+
  | address1         | city     | state | zip   | _id           |
  +==================+==========+=======+=======+===============+
  | 101 North Street | Waco     | Texas | 76711 | 0.addresses.0 |
  +------------------+----------+-------+-------+---------------+
  | 500 W 6th St     | Waterloo | Iowa  | 50701 | 1.addresses.0 |
  +------------------+----------+-------+-------+---------------+
