import logging

import oracledb

logger = logging.getLogger(__name__)

# PIRSA_DEV_SERVER = "pirzapd08.pirsa.sa.gov.au"  # Decommissioned as of 7/9/25
# PIRSA_TEST_SERVER = "pirzapd08.pirsa.sa.gov.au" # Decommissioned as of 7/9/25
# PIRSA_PROD_SERVER = "pirsapd07.pirsa.sa.gov.au"
DEW_DEV_SERVER = "sageodata.db.dev.env.sa.gov.au"
DEW_TEST_SERVER = "sageodata.db.qa.env.sa.gov.au"
DEW_PROD_SERVER = "sageodata.db.env.sa.gov.au"

PORT = 1521

DEV_SERVER = DEW_DEV_SERVER
TEST_SERVER = DEW_TEST_SERVER
PROD_SERVER = DEW_PROD_SERVER


def normalize_service_name(name: str) -> str:
    """Ensure consistent SA Geodata service name.

    Args:
        service_name (str): database service name either
            "prod", "test" or "dev" or
            one of "DMET.WORLD@PIRSA", "DMED.WORLD@PIRSA",
            "DMEP.WORLD@PIRSA", "DMET@DEW", "DMED@DEW" or
            "DMEP.WORLD@DEW". If the @PIRSA or @DEW is
            omitted @PIRSA will be used.

    Returns:
        string: The proper service name e.g. DMEP.WORLD@PIRSA
        for the current "prod".

    """
    name = name.upper()

    if not "@" in name:
        # name += "@PIRSA"
        name += "@DEW"

    name1, name2 = name.split("@")
    name1 = name1.strip().upper()
    name2 = name2.strip().upper()

    if name1 == "PROD":
        name1 = "DMEP.WORLD"
    elif name1 == "TEST" or name1.lower() == "QA":
        name1 = "DMET.WORLD"
    elif name1 == "DEV":
        name1 = "DMED.WORLD"

    error = "service@location - "
    if not name1.upper() in ("DMEP.WORLD", "DMET.WORLD", "DMED.WORLD"):
        raise KeyError(error + "service must be either PROD, TEST, or DEV")
    if not name2 in ("DEW", "PIRSA"):
        raise KeyError(error + "location must be either DEW or PIRSA")

    if name2 == "DEW":
        if "DMET" in name1:
            name1 = "DMET"
        elif "DMED" in name1:
            name1 = "DMED"

    final = name1 + "@" + name2

    if final in ("TEST@PIRSA", "QA@PIRSA", "DEV@PIRSA"):
        raise KeyError("Server has been decommissioned. Use ...@DEW instead.")

    return final


def find_appropriate_server(service_name: str) -> str:
    """Find the server that each service name lives on. See PROD_SERVER
    and TEST_SERVER.

    Args:
        service_name (str): one of "DMET.WORLD@PIRSA", "DMED.WORLD@PIRSA",
            "DMEP.WORLD@PIRSA", "DMET@DEW", "DMED@DEW" or "DMEP.WORLD@DEW".

    Returns:
        string: Server address.

    """
    if service_name == "DMET.WORLD@PIRSA":
        # server = PIRSA_TEST_SERVER
        raise KeyError("PIRSA environments have been decommissioned.")
    elif service_name == "DMED.WORLD@PIRSA":
        # server = PIRSA_DEV_SERVER
        raise KeyError("PIRSA environments have been decommissioned.")
    elif service_name == "DMEP.WORLD@PIRSA":
        # server = PIRSA_PROD_SERVER
        raise KeyError("PIRSA environments have been decommissioned.")
    elif service_name == "DMET@DEW":
        server = DEW_TEST_SERVER
    elif service_name == "DMED@DEW":
        server = DEW_DEV_SERVER
    elif service_name == "DMEP.WORLD@DEW":
        server = DEW_PROD_SERVER
    else:
        raise KeyError(
            "service_name must be either DMEP.WORLD@DEW, DMET.WORLD@DEW, or DMED.WORLD@DEW (or @PIRSA)"
        )
    return server


def makedsn(service_name="DMEP.WORLD", server=None, port=PORT):
    """Get the appropriate Oracle DSN.

    Args:
        service_name (str): database service name one of
            "DMET.WORLD@PIRSA", "DMED.WORLD@PIRSA", "DMEP.WORLD@PIRSA",
            "DMET@DEW", "DMED@DEW" or "DMEP.WORLD@DEW".
            This goes to :func:`sageodata_db.normalize_service_name`
            first so you can also pass "prod", "test", or "dev".
        server (str, optional): server address
        port (int, optional): port

    Returns:
        string: DSN connection string.

    For example, to get the production database:

        >>> from sageodata_db import makedsn
        >>> makedsn("prod")
        '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=pirsapd07.pirsa.sa.gov.au)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=DMEP.World)))'

    """
    service_name = normalize_service_name(service_name)
    if server is None:
        server = find_appropriate_server(service_name)
    return oracledb.makedsn(server, port, service_name=service_name.split("@")[0])


def make_connection_string(service_name="DMEP.WORLD", server=None, port=PORT):
    """Get the appropriate oracledb connection string.

    Args:
        service_name (str): database service name one of
            "DMET.WORLD@PIRSA", "DMED.WORLD@PIRSA", "DMEP.WORLD@PIRSA",
            "DMET@DEW", "DMED@DEW" or "DMEP.WORLD@DEW".
            This goes to :func:`sageodata_db.normalize_service_name`
            first so you can also pass "prod", "test", or "dev".
        server (str, optional): server address
        port (int, optional): port

    Returns:
        string: DSN connection string.

    For example, to get the production database:

        >>> from sageodata_db import makedsn
        >>> makedsn("prod")
        '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=pirsapd07.pirsa.sa.gov.au)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=DMEP.World)))'

    """
    service_name = normalize_service_name(service_name)
    if server is None:
        server = find_appropriate_server(service_name)
    return "{}:{}/{}".format(server, port, service_name.split("@")[0])
