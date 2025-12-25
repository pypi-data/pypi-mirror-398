from datetime import datetime, date
from string import Formatter
import re
import warnings
import logging

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import sqlparse
from sa_gwdata import Well, Wells


logger = logging.getLogger(__name__)


class SQL:
    r"""Represents an SQL query or queries.

    Args:
        sql (str): SQL query template
        to_str (bool): TBD
        chunksize (int): when sequences are passed into template fields,
            this is the maximum length allowed before a new query is issued.
        ignore_fields (sequence of str): list of keyword arguments to ignore.

    Remaining positional and keyword arguments are assumed to be filling
    template fields in ``sql``, unless they are listed in ``ignore_fields``.

    Lower-case string template fields are filled directly with the content of the
    keyword argument, while upper-case ones are understood as iterators over a variety
    of sequence types (each then represented in the Oracle SQL correctly according to the
    sequence's element data type). Data-types are processed into SQL according
    to the following tests:

     - if a sequence contains Python ints, they are represented as integers
       in the generated SQL
     - if a sequence contains Python floats, they are represented as floating
       point numbers in the generated SQL
     - if a sequence contains Python datetime, date, or :class:`pandas.Timestamp`
       objects, they are represented as strings in the generated SQL with the
       Python datetime formatting ``%Y-%m-%d %H:%M:%S``.
     - all other Python objects are represented as strings in the generated
       SQL

    The generated SQL should always be retrieved by iterating over this object,
    even if sequences are not being passed. An example of how this class can be
    used follows.

        >>> from sageodata_db import SQL
        >>> query = SQL(
        ...     "select * from dhdb.dd_drillhole_vw where drillhole_no in {dh_no}",
        ...     dh_no=1
        ... )
        >>> for sql in query:
        ...     print(sql)
        SELECT *
        FROM dhdb.dd_drillhole_vw
        WHERE drillhole_no IN 1

    Or for a sequence data type:

        >>> from sageodata_db import SQL
        >>> sequence_query = SQL(
        ...     "select * from dhdb.dd_drillhole_vw where drillhole_no in {DH_NO}",
        ...     dh_no=[1, 2, 3, 4, 5, 6, 7]
        ... )
        >>> for sql in sequence_query:
        ...     print(sql)
        SELECT *
        FROM dhdb.dd_drillhole_vw
        WHERE drillhole_no IN (1,2,3,4,5,6,7)

    To illustrate how a long list of qualifiers is automatically broken into the
    maximum acceptable length by the database engine, let's artifically reduce
    the default chunk size of 1000 to something we can easily visualize:

        >>> sequence_query.chunksize = 3
        >>> for i, sql in enumerate(sequence_query):
        ...     print((i, sql))
        (0, 'SELECT *\nFROM dhdb.dd_drillhole_vw\nWHERE drillhole_no IN (1,2,3)')
        (1, 'SELECT *\nFROM dhdb.dd_drillhole_vw\nWHERE drillhole_no IN (4,5,6)')
        (2, 'SELECT *\nFROM dhdb.dd_drillhole_vw\nWHERE drillhole_no IN (7)')

    The kwarg to_str provides a function which turns the elements from field_list
    to a string. By default it is determined by the type of the first element.

    You can re-use a :class:`sageodata_db.SQL` object with a new field_list:

        >>> sequence_query_2 = SQL(sequence_query, [8, 9, 10])
        >>> for sql in sequence_query_2:
        ...     print(sql)
        SELECT *
        FROM dhdb.dd_drillhole_vw
        WHERE drillhole_no IN (8,9,10)

    """

    def __init__(
        self, sql, *args, to_str=None, chunksize=1000, ignore_fields=None, **kwargs
    ):
        if isinstance(sql, SQL):
            sql = sql.sql

        if ignore_fields is None:
            ignore_fields = ()

        self.chunksize = chunksize
        self.sql = sqlparse.format(sql, reindent=True, keyword_case="upper")

        fields = [
            fname
            for _, fname, _, _ in Formatter().parse(self.sql)
            if fname and (not fname in ignore_fields) and (not re.match(r"\d+", fname))
        ]

        # Assign a field name to each positional argument. Most of the time there
        # will only be one positional argument, and only one field in the SQL query.
        # But in general, we assign them in the order we find them, and clobber
        # anything from **kwargs in the process.

        for i in range(len(args)):
            kwargs[fields[i]] = args[i]

        # Fields in uppercase are to be filled as lists.
        # Fields in lowercase are to be filled as items for every query.

        uppercase_fields = [x for x in fields if x.upper() == x]
        lowercase_fields = [x for x in fields if not x in uppercase_fields]
        # assert len(uppercase_fields) in (0, 1)

        # logger.debug(f"uppercase_fields: {uppercase_fields}")
        # logger.debug(f"lowercase_fields: {lowercase_fields}")

        # If an SQL field e.g. DH_NO is present in kwargs in lowercase, then we need
        # to convert the kwargs to uppercase, so that everything else works sensibly.

        for upper_field in uppercase_fields:
            keys = list(kwargs.keys())
            for k in keys:
                if k == upper_field.lower():
                    kwargs[upper_field] = kwargs[k]
                    del kwargs[k]
                    break

        if len(uppercase_fields) > 0:
            items = kwargs[uppercase_fields[0]]
            if isinstance(items, Wells):
                items = getattr(
                    items, uppercase_fields[0].lower()
                )  # e.g. for {DH_NO}, fetch [w.dh_no for w in Wells]
            elif isinstance(items, pd.DataFrame):
                items = items[uppercase_fields[0].lower()].tolist()
            self.field_list = items
            self.field_list_name = uppercase_fields[0]  # remain uppercase
        else:
            self.field_list = []
            self.field_list_name = None

        self.to_str_funcs = {}
        for field_name, example in kwargs.items():
            if field_name == field_name.upper():
                if isinstance(example, pd.DataFrame):
                    example = example.iloc[0]
                else:
                    try:
                        example = example[0]
                    except IndexError:
                        example = None

            # np.int64 needs conversion to int
            if "numpy.int" in str(type(example)):
                example = int(example)

            if example is None:
                # Field list is empty. We need a valid SQL query, so that we
                # return an empty table with the correct column names.
                # We assume that nothing will match an empty string in the
                # SQL where clause.

                self.to_str_funcs[field_name] = lambda x: "'{}'".format(str(x))
                self.field_list = [""]

            else:
                if isinstance(example, int) or isinstance(example, np.int64):
                    self.to_str_funcs[field_name] = lambda x: str(int(x))
                elif isinstance(example, float):
                    self.to_str_funcs[field_name] = lambda x: str(float(x))
                elif (
                    isinstance(example, datetime)
                    or isinstance(example, pd.Timestamp)
                    or isinstance(example, date)
                ):
                    self.to_str_funcs[field_name] = lambda x: x.strftime(
                        "'%Y-%m-%d %H:%M:%S'"
                    )
                else:
                    if "fragment" in field_name.lower():
                        target = "'%{}%'"
                    else:
                        target = "'{}'"

                    if "uppercase" in field_name.lower():
                        self.to_str_funcs[field_name] = lambda x: target.format(
                            str(x).upper()
                        )
                    else:
                        self.to_str_funcs[field_name] = lambda x: target.format(str(x))

        if self.field_list_name:
            del kwargs[self.field_list_name]

        self.scalar_fields = kwargs

    def __iter__(self):
        scalar_inserts = {
            k: self.to_str_funcs[k](v) for k, v in self.scalar_fields.items()
        }

        if len(self.field_list):
            for sub_list in chunk(self.field_list, self.chunksize):
                to_str = self.to_str_funcs[self.field_list_name]
                sub_list_str = "(" + ",".join(map(to_str, sub_list)) + ")"
                inserts = dict(scalar_inserts)
                inserts[self.field_list_name] = sub_list_str
                result = self.sql.format(**inserts)
                yield result
        elif len(scalar_inserts):
            result = self.sql.format(**scalar_inserts)
            yield result
        else:
            result = self.sql
            yield result


PREDEF_COL_SPECS = {
    "dh_no": "drillhole number (unique ID for drillholes) - integer",
    "unit_long": "- unit number in 9-digit numeric integer form e.g. 662800123",
    "unit_hyphen": "- unit number in condensed hyphenated form e.g. 6628-123",
    "obs_no": "- observation well number in 6-character padded form e.g. YAT056",
    "dh_name": "- drillhole name",
    "easting": "- UTM easting in metres, GDA2020",
    "northing": "- UTM northing in metres, GDA2020",
    "zone": "- UTM zone, GDA2020",
    "latitude": "- geographic latitude in GDA2020 datum as decimal degrees",
    "longitude": "- geographic longitude in GDA2020 datum as decimal degrees",
    "aquifer": "- the current aquifer code - e.g. the combination of strat symbol and hydro subunit such as 'Tomw(T1)'. If there are multiple aquifer monitored codes, they are joined with a plus e.g. 'Qpah+Tomw(T1)'",
    "created_by": "- SA Geodata user that orginally created the record. DHDB is a system user.",
    "creation_date": "- Date and time that the record was originally created.",
    "modified_by": "- SA Geodata user that most recently modified the record.",
    "modified_date": "- date and time that the record was most recently modified (:class:`pandas.Timestamp`)",
}


def parse_query_metadata(query):
    columns = {}
    params = {}
    docstring = [[], []]
    first_part_over = False
    for line in query.splitlines():
        if line.startswith("--") and not first_part_over:
            docstring[0].append(line.strip("-- "))
        elif line.startswith("--") and first_part_over:
            docstring[1].append(line.strip("-- "))
        else:
            first_part_over = True
            if "--col" in line:
                before, after = line.split("--col", 1)
                name = before.split()[-1]
                name = name.strip(",")
                if "." in name:
                    name = name.split(".")[-1]
                descr = after.strip()
                if descr:
                    descr = " - " + descr
                elif name in PREDEF_COL_SPECS.keys():
                    descr = PREDEF_COL_SPECS[name]
                columns[name] = {"descr": descr}
            elif "--arg" in line:
                descr = line.split("--arg")[-1]
                parts = descr.split()
                if len(parts) > 1:
                    name = parts[0]
                else:
                    name = "?"
                m = re.search(r"default=(['\".a-zA-Z0-9]+)", descr)
                if m:
                    default = m.group(1)
                else:
                    default = None
                params[name] = {"descr": descr, "default": default}
    return columns, params, docstring


def chunk(l, n=1000):
    """Yield successive n-sized chunks from a list l.

    >>> from sageodata_db.utils import chunk
    >>> for x in chunk([0, 1, 2, 3, 4], n=2):
    ...     print(x)
    [0, 1]
    [2, 3]
    [4]

    """
    y = 0
    for i in range(0, len(l), n):
        y += 1
        yield l[i : i + n]
    if y == 0:
        yield l


def apply_well_id(row, columns=("obs_no", "unit_hyphen", "dh_no")):
    for col in columns:
        if row[col]:
            return row[col]
    return ""


def cleanup_columns(df, keep_cols="well_id", remove_metadata=False):
    """Remove unneeded drillhole identifier columns.

    Args:
        df (pandas DataFrame): dataframe to remove columns from
        keep_cols (sequence of str): columns to retain (only applies to the
            well identifiers columns; any other columns will be retained
            regardless)

    Returns: dataframe

    """
    if not "well_id" in df.columns:
        cols = [x for x in df.columns]
        df["well_id"] = df.apply(apply_well_id, axis="columns")
        df = df[["well_id"] + cols]
    if remove_metadata:
        for col in df:
            if (
                "modified_date" in col
                or "creation_date" in col
                or "modified_by" in col
                or "created_by" in col
            ):
                df = df.drop(col, axis=1)
    keep_columns = []
    for col in df.columns:
        if (
            col
            in (
                "well_id",
                "dh_no",
                "unit_long",
                "unit_hyphen",
                "obs_no",
                "dh_name",
                "easting",
                "northing",
                "zone",
                "latitude",
                "longitude",
                "aquifer",
            )
            and not col in keep_cols
        ):
            pass
        else:
            keep_columns.append(col)
    return df[keep_columns]
