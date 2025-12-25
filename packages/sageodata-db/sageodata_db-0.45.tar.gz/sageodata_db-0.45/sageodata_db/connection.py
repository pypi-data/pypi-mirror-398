from datetime import timedelta
from inspect import signature, Parameter
from pathlib import Path
from string import Formatter
import logging

import oracledb
import pandas as pd
from PIL import Image
from sa_gwdata import *

from .utils import (
    SQL,
    apply_well_id,
    chunk,
    parse_query_metadata,
)
from .config import *


logger = logging.getLogger(__name__)

# for test_path in (r"C:\Program Files\Oracle\Instant Client v19.9",):
#     if Path(test_path).is_dir():
#         try:
#             cx_Oracle.init_oracle_client(test_path)
#         except cx_Oracle.ProgrammingError:
#             logger.info(
#                 "Ignoring cx_Oracle.ProgrammingError - already initialised likely"
#             )


def load_predefined_query(filename, stub="queries"):
    if not Path(filename).is_file():
        filename = Path(__file__).parent / stub / filename
    if not Path(filename).is_file():
        return load_predefined_query(str(filename) + ".sql")
    with open(str(filename)) as f:
        query = f.read()
    return query


def get_predefined_query_filenames():
    return [p.name for p in (Path(__file__).parent / "queries").glob("*.sql")]


def get_predefined_query_lookup_types():
    results = {}
    root_path = Path(__file__).parent
    for path in (root_path / "queries").rglob("*"):
        if path.suffix.endswith(".sql"):
            lookup_type = path.parent.name
            if lookup_type == "queries":
                query_content = load_predefined_query(path.name)
                m = re.search(r"\{[a-zA-Z_]*\}", query_content)
                if m:
                    lookup_type = m.group()
                else:
                    lookup_type = ""
            if not lookup_type in results:
                results[lookup_type] = [path.name]
            else:
                results[lookup_type].append(path.name)
    return results


def connect(user="gwquery", password="gwquery", **kwargs):
    """Connect to SA Geodata.

    Args:
        user (str): oracle user
        password (str): password
        service_name (str): version of SA Geodata you would like to connect
            to - options are "DMED.WORLD" or "dev"; "DMET.WORLD" or "test" or
            "QA"; or "DMEP.WORLD" or "prod" - see
            :func:`sageodata_db.config.normalize_service_name` for details.

    Other keyword arguments are passed to
    :func:`sageodata_db.config.make_connection_string`.

    Returns:
        a :class:`sageodata_db.SAGeodataConnection` object.

    Example:

        >>> from sageodata_db import connect
        >>> db = connect()
        >>> db
        <sageodata_db.connection.SAGeodataConnection to gwquery@pirsapd07.pirsa.sa.gov.au:1521/DMEP.World>

    """
    connect_string = make_connection_string(**kwargs)
    conn = oracledb.connect(user=user, password=password, dsn=connect_string)
    return SAGeodataConnection(conn=conn)


class SAGeodataConnection:
    """SA Geodata database connection object with methods to read groundwater data.

    This should not be instantiated directly. Instead use::

        >>> from sageodata_db import connect
        >>> db = connect()
        >>> type(db)
        <class 'sageodata_db.connection.SAGeodataConnection'>

    """

    SQL = SQL

    def __init__(self, conn):
        self.conn = conn

        from sageodata_db import __version__

        self.__version__ = __version__
        self._all_replacement_drillholes = self.all_replacement_drillholes()

    def _make_predefined_query_lambda(self, query_name):
        return lambda *args, **kwargs: self._predefined_query(
            query_name, *args, **kwargs
        )

    def test_alive(self):
        """Test whether connection is functioning.

        Returns:
            bool: ``True`` or ``False``

        """
        df = self.query("select distinct owner from all_tables")
        try:
            owners = df["owner"]
        except oracledb.Error:
            return False
        if "SYS" in owners.values:
            return True
        return False

    def _predefined_query(
        self,
        filename,
        *args,
        stub="queries",
        query_method="query",
        include_replacements=False,
        **kwargs,
    ):
        """Run a predefined query on the database.

        Args:
            query_name (str): see below for possible predefined queries.

        Other args and kwargs are passed to `_predefined_query()` along with the fixed
        kwargs `stub="queries", query_method="query"`.

        Returns:
            pandas DataFrame.

        """
        sql = load_predefined_query(filename, stub=stub)
        query_method = getattr(self, query_method)
        df = query_method(SQL(sql, *args, **kwargs))
        cols = [x for x in df.columns]
        if (
            "obs_no" in df.columns
            and "unit_hyphen" in df.columns
            and "dh_no" in df.columns
        ):
            if len(df):
                df["well_id"] = df.apply(apply_well_id, axis="columns")
            else:
                df = df.assign(well_id=None)
            cols = ["well_id"] + cols
        df = df[cols]
        logger.debug(f"Include replacements? {include_replacements}")
        if include_replacements:
            dfs = []
            for dh_no in df.dh_no.unique():
                all_dhs = self.find_replacements([dh_no])
                if len(all_dhs) > 0:
                    missing_dhs = set(all_dhs.old_dh_no).difference(set(df.dh_no))
                    logger.debug(f"missing_dhs {missing_dhs}")
                    all_df = self._predefined_query(
                        filename,
                        list(missing_dhs),
                        include_replacements=False,
                        **kwargs,
                    )
                    df2 = pd.concat([df, all_df])
                    if "obs_date" in df2.columns:
                        dt_col = "obs_date"
                    elif "collected_date" in df2.columns:
                        dt_col = "collected_date"

                    df3 = df2[df2.dh_no == all_dhs.iloc[0].old_dh_no]

                    for idx, row in all_dhs.sort_values("replaced_from").iterrows():
                        logger.debug(
                            f"Adding in data from replacement: {row.to_dict()}"
                        )
                        if ~pd.isnull(row.new_dh_no) and ~pd.isnull(row.replaced_from):
                            # Remove measurements from the old_dh_no after or on the replacement date.
                            remove_old = (df3.dh_no == row.old_dh_no) & (
                                df3[dt_col] >= row.replaced_from
                            )
                            df3 = df3[~remove_old]
                            # Add measurements from the new_dh_no on and after the replacement date.
                            keep_new = (df2.dh_no == row.new_dh_no) & (
                                df2[dt_col] >= row.replaced_from
                            )
                            df3 = pd.concat([df3, df2[keep_new]])
                    df3 = df3.sort_values([dt_col])

                    # Improve columns
                    current = (
                        self.drillhole_details(all_dhs.index.unique()).iloc[0].to_dict()
                    )
                    logger.debug(f"Current well is: {current}")
                    well_cols = [
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
                    ]
                    for col in ["dh_no", "unit_long", "unit_hyphen", "obs_no"]:
                        df3[f"from_{col}"] = df3[col]
                    for col in well_cols[::-1]:
                        df3[col] = current[col]
                else:
                    df3 = df[df.dh_no == dh_no]
                dfs.append(df3)
            df = pd.concat(dfs)
        return df

    def query(self, query, lowercase_columns=True, *args, conn=None, **kwargs):
        """Run an SQL query on SA Geodata and return a :class:`pandas.DataFrame`.

        Args:
            query (str, SQL): SQL query as string or
                :class:`sageodata_db.connection.SQL`

        Returns:
            a :class:`pandas.DataFrame` object.

        """
        if conn is None:
            conn = self.conn
        if isinstance(query, str):
            query = SQL(query, *args, **kwargs)
        dfs = []
        for sql in query:
            logger.debug("running query:\n{}".format(sql))
            dfs.append(pd.read_sql_query(sql, conn))
        df = pd.concat(dfs)
        if lowercase_columns:
            df = df.rename(columns=str.lower)
        return df

    def _create_well_instances(self, dh_nos):
        """Private method to create Well instances from dh_nos.

        Args:
            dh_nos (array-like): drillhole numbers as integers.

        Returns:
            :class:`sa_gwdata.Wells` object (sequence of :class:`sa_gwdata.Well` objects).

        """
        df = self.drillhole_details(dh_nos)
        df.loc[:, "name"] = df["dh_name"]
        df.loc[:, "unit_no.hyphen"] = df["unit_hyphen"]
        df.loc[:, "unit_no"] = df["unit_hyphen"]
        df.loc[:, "dh_no"] = df["dh_no"]
        return Wells([Well(**vals.to_dict()) for _, vals in df.iterrows()])

    def find_replacement_history(self, dh_no):
        """Find the chain of drillholes that replaced one another, for *dh_no*.

        Args:
            dh_no (int): drillhole number

        Returns:
            a pandas dataframe with columns "old_dh_no", "new_dh_no", and
            "replaced_from".

        """

        df = self._all_replacement_drillholes

        def _find_replacement_history(
            dh_no_chain, check_for_newer_wells=True, check_for_older_wells=True
        ):
            earliest_dh_no = dh_no_chain[0]
            latest_dh_no = dh_no_chain[-1]
            if check_for_newer_wells:
                replacements = df[df["dh_no"] == latest_dh_no]
                if len(replacements) == 1:
                    row = replacements.iloc[0]
                    dh_no_chain = list(dh_no_chain) + [row.new_dh_no]
                    return _find_replacement_history(
                        dh_no_chain, check_for_newer_wells=True
                    )
            if check_for_older_wells:
                replaced = df[df["new_dh_no"] == earliest_dh_no]
                if len(replaced) == 0:
                    return dh_no_chain
                elif len(replaced) == 1:
                    row = replaced.iloc[0]
                    previous_dh_no = row.dh_no
                    dh_no_chain = [previous_dh_no] + list(dh_no_chain)
                    return _find_replacement_history(
                        dh_no_chain, check_for_newer_wells=False
                    )

        dh_no_chain = _find_replacement_history([dh_no])
        hdf = df[df.dh_no.isin(dh_no_chain)]
        hdf = hdf.set_index("dh_no")
        hdf2 = hdf.reindex(dh_no_chain)
        hdf3 = hdf2.reset_index().rename(columns={"dh_no": "old_dh_no"})
        return hdf3

    def find_replacements(self, wells):
        """Find replacements for a set of wells.

        Args:
            wells (Wells, pandas dataframe, or list of ints): either must
                have an attribute "dh_no", or a list of drillhole numbers.

        Returns:
            pandas DataFrame with index "current_dh_no" and
            columns "queried_dh_no", "old_dh_no", "new_dh_no", "replaced_from"

        """
        if hasattr(wells, "dh_no"):
            dh_nos = [getattr(o, "dh_no") for o in wells]
        else:
            dh_nos = wells
        dfs = []
        for dh_no in dh_nos:
            df = self.find_replacement_history(dh_no)
            if len(df) > 1:
                df.insert(0, "current_dh_no", _find_current_for_replacement_chain(df))
                df.insert(0, "queried_dh_no", dh_no)
            else:
                df = df.assign(current_dh_no=dh_no, queried_dh_no=dh_no)
            dfs.append(df)
        return pd.concat(dfs).set_index("current_dh_no")

    def find_wells(self, input_text, **kwargs):
        """Find wells and retrieve some summary information.

        Args:
            input_text (str): any well identifiers to parse. See
                :func:`sa_gwdata.parse_well_ids_plaintext` for details of
                other keyword arguments you can pass here.

        Returns:
            wells (pandas.DataFrame): a table of well summary
                details (via :meth:`sageodata_db.SAGeodataConnection.wells_summary`)

        For example::

            >>> from sageodata_db import connect
            >>> db = connect()
            >>> wells = db.find_wells(": G662801265, 6628-14328, YAT30, and ULE 205.")

        See :func:`sa_gwdata.parse_well_ids` for more details.

        """
        ids = parse_well_ids(input_text, **kwargs)
        dh_nos = [x for id_type, x in ids if id_type == "dh_no"]
        unit_nos = [x for id_type, x in ids if id_type == "unit_no"]
        obs_nos = [x for id_type, x in ids if id_type == "obs_no"]
        unit_long_ints = [UnitNumber(x).long_int for x in unit_nos]
        logger.debug("unit_no.long_int: {}".format(unit_long_ints))
        r_obs_nos = []

        if obs_nos:
            r1 = self._predefined_query("drillhole_no_by_obs_no.sql", obs_nos)
            r_obs_nos = r1.dh_no.tolist()
        r_unit_nos = []
        if unit_long_ints:
            # r2 = self._predefined_query("drillhole_no_by_unit_long.sql", unit_long_ints)
            r2 = self.drillhole_no_by_unit_long(unit_long_ints)
            r_unit_nos = r2.dh_no.tolist()
        logger.debug("obs_nos -> {}".format(r_obs_nos))
        logger.debug("unit_nos -> {}".format(r_unit_nos))
        all_dh_nos = list(set(dh_nos + r_obs_nos + r_unit_nos))
        return self.wells_summary(all_dh_nos)
        # return self._create_well_instances(all_dh_nos)

    def find_wells_from_df(
        self,
        df,
        copy=True,
        return_id_cols=("unit_hyphen",),
        remap_id_col_names=True,
        **kwargs,
    ):
        """Find wells identifier in a dataframe and merge them together.

        Args:
            df (pd.DataFrame): dataframe containing well IDs
            copy (bool): if True return a copy otherwise just return well IDs.
            return_id_cols (list of str): columns containing identified well
                IDs which are returned. If *remap_id_col_names* is True, you can
                pick from: dh_no, well_id, dh_name, unit_hyphen, unit_long, unit_wilma
                unit_hydstra, obs_no, and obs_egis. If *remap_id_col_names* is False,
                you can choose from dh_no, id, name, unit_no.map, unit_no.seq,
                unit_no.hyphen, unit_no.long_int, unit_no.long,
                unit_no.wilma, unit_no.hydstra, obs_no.plan, obs_no.seq, obs_no.id,
                and obs_no.egis.
            remap_id_col_names (bool): remap from Wells.df to the typical columns
                found in other data queries.

        Other kwargs are passed to parse_well_ids().

        Returns:
            If **copy** == ``True``, a dataframe with **return_id_cols** added at the start, with all
            well identifiers matched. Otherwise, a dataframe with only **return_id_cols** is
            provided.

        """
        if isinstance(df, pd.Series):
            df = df.to_frame()

        # Parse any well identifier for each row of the
        # dataframe.
        wids = df.apply(
            lambda series: parse_well_ids("|".join(map(str, series.values)), **kwargs),
            axis="columns",
        )

        # Use only the first of each well identifier in each row
        wids = [wid[0] if len(wid) else "" for wid in wids]

        search_lines = list(set([str(wid[1]) if len(wid) == 2 else "" for wid in wids]))
        vwids_dfs = []
        for search in chunk(search_lines, 1000):
            logger.info(f"Searching for {len(search)} well IDs")
            vwids_dfs.append(self.find_wells("/".join(search), **kwargs))
        vwids = pd.concat(vwids_dfs).drop_duplicates()
        values = []
        for wid in wids:
            row = False
            if wid == "":
                pass
            elif wid[0] == "unit_no":
                row_sel = vwids[vwids["unit_hyphen"] == wid[1]]
                if len(row_sel) == 1:
                    row = row_sel.iloc[0]
            elif wid[0] == "obs_no":
                row_sel = vwids[vwids["obs_no"] == wid[1]]
                if len(row_sel) == 1:
                    row = row_sel.iloc[0]
            elif wid[0] == "dh_no":
                row_sel = vwids[vwids.dh_no == wid[1]]
                if len(row_sel) == 1:
                    row = row_sel.iloc[0]
            if row is False:
                row = pd.Series([None for x in vwids.columns], index=vwids.columns)
            row.loc["parsed_id"] = wid
            values.append(row)
        id_cols = pd.DataFrame(values, index=df.index.values)
        if remap_id_col_names:
            id_cols = id_cols.rename(
                columns={
                    "id": "well_id",
                    "name": "dh_name",
                    "unit_no.hyphen": "unit_hyphen",
                    "unit_no.long_int": "unit_long",
                    "unit_no.wilma": "unit_wilma",
                    "unit_no.hydstra": "unit_hydstra",
                    "obs_no.id": "obs_no",
                    "obs_no.egis": "obs_egis",
                }
            )
        if return_id_cols is None:
            return_id_cols = id_cols.columns
        else:
            return_id_cols = ["parsed_id"] + list(return_id_cols)
        if copy:
            return pd.concat([id_cols[return_id_cols], df], axis=1)
        else:
            return id_cols[return_id_cols].T.drop_duplicates().T

    def drillhole_no_by_unit_hyphen(self, unit_hyphens):
        return self.drillhole_no_by_unit_long(unit_hyphens)

    def drillhole_no_by_unit_long(self, unit_longs):
        mapsheet_components = {}
        for unit_long in unit_longs:
            unit = UnitNumber(unit_long)
            if not unit.map in mapsheet_components:
                mapsheet_components[unit.map] = []
            mapsheet_components[unit.map].append(int(unit.seq))
        dfs = []
        for map_num, seq_nos in mapsheet_components.items():
            df = self.query(
                f"""
                select drillhole_no as dh_no, --col
                    unit_no as unit_long, --col
                    To_char(map_100000_no) || '-' || To_char(dh_seq_no) as unit_hyphen, --col,
                    Trim(To_char(obs_well_plan_code)) || Trim(To_char(obs_well_seq_no, '000')) as obs_no --col
                from dd_drillhole
                where map_100000_no = {map_num}
                    and dh_seq_no in ({','.join([f'{s:.0f}' for s in seq_nos])})
                    and deletion_ind = 'N'
            """
            )
            dfs.append(df)
        return pd.concat(dfs)

    def drillhole_no_by_obs_no(self, obs_nos):
        plan_components = {}
        for obs_no in obs_nos:
            obs = ObsNumber(obs_no)
            if not obs.plan in plan_components:
                plan_components[obs.plan] = []
            plan_components[obs.plan].append(int(obs.seq))
        dfs = []
        for plan, seq_nos in plan_components.items():
            df = self.query(
                f"""
                select drillhole_no as dh_no, --col
                    unit_no as unit_long, --col
                    To_char(map_100000_no) || '-' || To_char(dh_seq_no) as unit_hyphen, --col,
                    Trim(To_char(obs_well_plan_code)) || Trim(To_char(obs_well_seq_no, '000')) as obs_no --col
                from dd_drillhole
                where obs_well_plan_code = '{plan}'
                    and obs_well_seq_no in ({','.join([f'{s:.0f}' for s in seq_nos])})
                    and deletion_ind = 'N'
            """
            )
            dfs.append(df)
        return pd.concat(dfs)

    def find_edits_by(self, *modified_by):
        """Return a table of edits made to certain tables by a set of users.

        The tables which are current queried are water levels, salinity samples,
        and elevation surveys.

        Args:
            *modified_by (str): SA Geodata usernames

        Returns:
            A pandas dataframe.

        """
        wls = self.water_level_edits(modified_by)
        sals = self.salinity_edits(modified_by)
        elevs = self.elevation_edits(modified_by)
        wls = _remove_elev_mods_from_wl(wls, elevs)
        wls = wls.groupby(["well_id", "modified_date"]).filter(lambda x: len(x) <= 1)
        df = pd.concat(
            [
                wls.assign(table="WL").rename(columns={"wl": "data_values"}),
                sals.assign(table="Salinity").rename(
                    columns={"salinity": "data_values"}
                ),
                elevs.assign(table="Elevation").rename(columns={"elev": "data_values"}),
            ]
        ).sort_values("modified_date", ascending=False)
        cols = [x for x in df.columns if not x == "table"]
        cols.insert(cols.index("well_id") + 1, "table")
        return df[cols]

    def find_additions_by(self, *created_by):
        """Return a table of additions made to certain tables by a set of users.

        The tables which are current queried are water levels, salinity samples,
        and elevation surveys.

        Args:
            *created_by (str): SA Geodata usernames

        Returns:
            A pandas dataframe.

        """
        wls = self.water_level_additions(created_by)
        sals = self.salinity_additions(created_by)
        elevs = self.elevation_additions(created_by)
        wls = wls.groupby(["well_id", "creation_date"]).filter(lambda x: len(x) <= 1)
        df = pd.concat(
            [
                wls.assign(table="WL").rename(columns={"wl": "data_values"}),
                sals.assign(table="Salinity").rename(
                    columns={"salinity": "data_values"}
                ),
                elevs.assign(table="Elevation").rename(columns={"elev": "data_values"}),
            ]
        ).sort_values("creation_date", ascending=False)
        cols = [x for x in df.columns if not x == "table"]
        cols.insert(cols.index("well_id") + 1, "table")
        return df[cols]

    def open_drillhole_document_image(self, image_no):
        """Load a drillhole document image from DD_DH_IMAGE

        Args:
            image_no (int): see predefined query "drillhole_document_image_list"

        Returns:
            ``PIL.Image`` object

        """
        cursor = self.conn.cursor()
        var = cursor.var(oracledb.BLOB)      
        cursor.execute(
            """
                declare
                    t_Image ordsys.ordimage;
                begin
                    select Image
                    into t_Image
                    from dhdb.dd_dh_image where image_no = {:.0f};

                    :1 := t_Image.source.localdata;

                end;""".format(
                image_no
            ),
            (var,),
        )
        blob = var.getvalue()
        return Image.open(blob)

    def open_drillhole_image(self, image_no):
        """Load a drillhole image (photograph) from IM_IMAGE

        Args:
            image_no (int): see predefined query "drillhole_image_list"

        Returns:
            ``PIL.Image`` object

        """
        cursor = self.conn.cursor()
        var = cursor.var(oracledb.BLOB)
        cursor.execute(
            """
                declare
                    t_Image ordsys.ordimage;
                begin
                    select Image
                    into t_Image
                    from dhdb.im_image where image_no = {:.0f};

                    :1 := t_Image.source.localdata;

                end;""".format(
                image_no
            ),
            (var,),
        )
        blob = var.getvalue()
        return Image.open(blob)

    def open_db_file(self, file_no):
        """Open database file.

        Args:
            file_no (int)

        Returns:
            A tuple, where the first item is a string with the filename, the second is a ``io.BytesIO`` object
            with the file contents.

        """
        cursor = self.conn.cursor()
        var = cursor.var(oracledb.BLOB)
        cursor.execute(
            f"select file_name, file_contents from dhdb.fi_file where file_no = {file_no}"
        )
        for item in cursor:
            file_name = item[0]
            file_object = item[1]
        return file_name, io.BytesIO(file_object.read())

    def open_db_file_as_text(
        self, file_no, encoding=("ascii", "cp1252", "utf-8"), raise_error=True
    ):
        """Open database file as text.

        Args:
            file_no (int)
            encoding (sequence of str or str): the encodings to try in the order to try them.

        Returns:
            A tuple. The first item is a string with the filename, the second is a string
            with the file contents.

        """
        filename, buffer = self.open_db_file(file_no)
        buffer_contents = buffer.read()
        if isinstance(encoding, str):
            encoding = [encoding]

        contents = False
        i = 0
        while i < len(encoding):
            try_encoding = encoding[i]
            try:
                contents = buffer_contents.decode(try_encoding)
                contents = contents.strip()
                if len(contents) > 0:
                    break
            except:
                i += 1
        if contents is False:
            if raise_error:
                try:
                    raise
                except:
                    contents = ""
            else:
                logger.warning(f"Encoding error reading file_no={file_no}")
                contents = ""
        return filename, contents

    def list_geophys_log_db_files(self, job_nos=None):
        """Query for a list of geophysical log files stored in SA Geodata.

        Args:
            job_nos (sequence of int, optional): filter to particular
                job numbers, otherwise this will return all records in SAGD.

        The query is hard-coded into this function and is across FI_FILE,
        FI_FILE_LINK_VW and GL_LOG_HDR_VW.

        Returns:
            pandas.DataFrame: The table has columns:

            - job_no (int)
            - path (str). This column does not contain file paths, but is
              used for compatibility with functions utilising the gtslogs
              shared folder location. In this case it is populated with
              e.g. "sagd:file_no=1234"
            - file_type (str): filename suffix in uppercase
            - file_size (float): not populated as the files are not
              retrieved.

        """
        if job_nos:
            df = self.geophys_log_files_by_job_no(job_nos)
        else:
            df = self.geophys_log_files_all()

        df = df.rename(columns={"file_name": "filename", "file_no": "path"})
        df = df.drop(["log_hdr_no"], axis=1)
        df["path"] = df.path.apply(lambda file_no: f"sagd:file_no={file_no}")
        df["file_type"] = df.filename.apply(lambda fn: Path(fn).suffix.upper()[1:])
        return df

    def lookup_unit_numbers(conn, unit_nos):
        """Look up unit numbers.

        Args:
            unit_nos (sequence of str or int): anything that can be parsed by
                sa_gwdata.UnitNumber

        Returns:
            pandas.DataFrame: This has columns dh_no, unit_long,
            unit_hyphen, obs_no, dh_name etc.

        Order is not preserved, sorry.

        """
        std_unit_nos = [UnitNumber(u) for u in unit_nos]
        mapsheet_sets = {}
        for u in std_unit_nos:
            if not u.map in mapsheet_sets:
                mapsheet_sets[u.map] = [u.seq]
            else:
                mapsheet_sets[u.map].append(u.seq)
        dfs = []
        for mapsheet_num, dh_seq_nos in mapsheet_sets.items():
            dfs.append(conn.drillhole_by_dh_seq_no(mapsheet_num, dh_seq_nos))
        df = pd.concat(dfs)
        return df

    def lookup_obs_numbers(conn, obs_nos):
        """Look up obswell IDs.

        Args:
            obs_nos (sequence of str): anything that can be parsed by
                sa_gwdata.ObsNumber

        Returns:
            pandas.DataFrame: This has columns dh_no, unit_long,
            unit_hyphen, obs_no, dh_name etc.

        Order is not preserved, sorry.

        """
        std_obs_nos = [ObsNumber(o) for o in obs_nos]
        hundred_sets = {}
        for o in std_obs_nos:
            if not o.plan in hundred_sets:
                hundred_sets[o.plan] = [o.seq]
            else:
                hundred_sets[o.plan].append(o.seq)
        dfs = []
        for hundred_sets, dh_seq_nos in hundred_sets.items():
            dfs.append(conn.drillhole_by_obs_seq_no(hundred_sets, dh_seq_nos))
        df = pd.concat(dfs)
        return df

    def aquifer_units_details(self, aquifer_code):
        df = self.aquifer_units(aquifer_code)
        p = re.compile(r"\[SU(\d*)\]")

        def extract_su(desc):
            m = p.search(desc)
            if m:
                return int(m.group(1))
            else:
                return pd.NA

        out_cols = [
            "aquifer_code",
            "hydro_subunit_desc",
            "linked_strat_unit_no",
            "linked_map_symbol",
            "linked_strat_name",
            "linked_strat_agso_number",
            "major_strat_unit_no",
            "major_map_symbol",
            "hydro_subunit_code",
        ]
        if len(df) == 0:
            return pd.DataFrame(columns=out_cols)
        else:
            df = df.rename(
                columns={
                    "strat_unit_no": "major_strat_unit_no",
                    "map_symbol": "major_map_symbol",
                    "strat_name": "major_strat_name",
                }
            )
            df["linked_strat_unit_no"] = df.hydro_subunit_desc.apply(extract_su)
            su = self.strat_unit_details(df.linked_strat_unit_no.dropna())
            su = su.rename(
                columns={
                    "strat_unit_no": "linked_strat_unit_no",
                    "map_symbol": "linked_map_symbol",
                    "strat_name": "linked_strat_name",
                    "agso_number": "linked_strat_agso_number",
                }
            )
            su = su[
                [
                    "linked_strat_unit_no",
                    "linked_map_symbol",
                    "linked_strat_name",
                    "linked_strat_agso_number",
                ]
            ]
            dfm = pd.merge(df, su, on="linked_strat_unit_no")
            dfm = dfm[out_cols]
            return dfm


def _remove_elev_mods_from_wl(wl, elev):
    """Remove any edit records from WL data when there is an edit made to
    the elevation table within 5 seconds.

    """
    remove_indices = []
    wl_copy = pd.DataFrame(wl)
    for (dh_no, modified_date), gdf in elev.groupby(["dh_no", "modified_date"]):
        n1 = len(wl[wl.dh_no == dh_no])
        date1 = modified_date - timedelta(seconds=2)
        date2 = modified_date + timedelta(seconds=2)
        remove_idx = (
            (wl.dh_no == dh_no)
            & (wl.modified_date >= date1)
            & (wl.modified_date <= date2)
        )
        n2 = len(wl[remove_idx])
        logger.debug(f"{dh_no}, {modified_date}: wl {n1} -> {n2}")
        remove_indices.append(remove_idx)
        wl_copy = wl_copy[~remove_idx]
    return wl_copy


def _find_current_for_replacement_chain(df):
    """Identify which drillhole is current in a chain of
    replacement drillholes.

    Args:
        df (pandas DataFrame): returned by
            SAGeodataConnection.find_replacement_history()

    Returns:
        int, the drillhole number of the current well.

    """
    candidate = df[df.new_dh_no.isnull()].iloc[0]
    candidate_start = df.loc[df.new_dh_no == candidate.old_dh_no, "replaced_from"].iloc[
        0
    ]
    other_candidates = df.loc[df.replaced_from > candidate_start, :]
    if len(other_candidates) > 0:
        return int(other_candidates.sort_values("replaced_from").iloc[-1].new_dh_no)
    else:
        return int(candidate.old_dh_no)


def __monkey_patch_predefined_queries(cls, method_name):
    """Monkey-patch predefined query methods on to a class.

    Args:
        cls (class): class to monkey-patch methods on to
        method_name (str): name of method in cls which takes
            the query_name as its first argument. Other args
            and kwargs are passed through to this method

    Returns:
        nothing.

    """

    def __make_lambda(query_name, method_name):
        return lambda self, *args, **kwargs: getattr(self, method_name)(
            query_name, *args, **kwargs
        )

    docstring_lines = []
    query_names = get_predefined_query_filenames()
    for query_name in query_names:
        query = load_predefined_query(query_name)
        columns, param_defns, docstring_parts = parse_query_metadata(query)
        query_name = query_name.replace(".sql", "")
        func = __make_lambda(query_name, method_name=method_name)
        func.__name__ = query_name
        field_names = [fname for _, fname, _, _ in Formatter().parse(query) if fname]
        if field_names:
            params = [Parameter("self", Parameter.POSITIONAL_OR_KEYWORD)]
            for field_name in field_names:
                param_meta = param_defns.get(field_name, {"default": None, "descr": ""})
                if not param_meta["default"]:
                    param_meta["default"] = Parameter.empty
                params.append(
                    Parameter(
                        field_name,
                        Parameter.POSITIONAL_OR_KEYWORD,
                        default=param_meta["default"],
                    )
                )
            if "dh_no" in [n.lower() for n in field_names]:
                params.append(
                    Parameter(
                        "include_replacements",
                        Parameter.POSITIONAL_OR_KEYWORD,
                        default=False,
                    )
                )
                param_defns["include_replacements"] = {
                    "descr": (
                        "include_replacements (bool): default ``False``. "
                        "Fold data from replaced drillholes the newest "
                        "drillhole (e.g. data from dh_no 12345 will be included"
                        " as part of drillhole 23500 if 23500 is marked as a "
                        "replacement for 12345)"
                    ),
                    "default": False,
                }

            unique_params = []
            for p in params:
                if not p in unique_params:
                    unique_params.append(p)
            func.__signature__ = signature(func).replace(parameters=unique_params)

        doclines = [f"Run predefined query '{query_name}.sql'.", ""]
        if docstring_parts[0]:
            doclines += docstring_parts[0]
            doclines += [""]
        if param_defns:
            doclines += ["Args:"]
            doclines += [
                f"    {meta['descr'].strip()}" for name, meta in param_defns.items()
            ]
            doclines += [""]
        if len(columns):
            doclines += ["Returns:", "    :class:`pandas.DataFrame`", ""]
            doclines += ["The returned DataFrame has the following columns:", ""]
            doclines += [
                f" - ``'{name}'`` {meta['descr']}" for name, meta in columns.items()
            ]
            doclines += [""]
        if docstring_parts[1]:
            doclines += docstring_parts[1]
            doclines += [""]
        # doclines += [
        #     "The SQL template (used by :class:`sageodata_db.SQL`) for this query:",
        #     "",
        #     ".. code-block:: plpgsql",
        #     "",
        # ]
        # doclines += [
        #     f"    {line}"
        #     for line in query.splitlines()
        #     if not line.strip().startswith("-- ")
        # ]
        # doclines += [""]

        func.__doc__ = "\n".join([f"    {line}" for line in doclines])
        setattr(cls, query_name, func)


__monkey_patch_predefined_queries(SAGeodataConnection, method_name="_predefined_query")
