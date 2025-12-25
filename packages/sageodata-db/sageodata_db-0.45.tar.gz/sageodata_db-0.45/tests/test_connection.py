import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import oracledb
import pytest
from sa_gwdata import Well, UnitNumber

import sageodata_db
from utils import on_state_intranet

INTRANET = on_state_intranet()


@pytest.mark.skipif(INTRANET is False, reason="Need to be connected to intranet")
def test_test_alive():
    db = sageodata_db.connect()
    assert db.test_alive()


def test_wrong_service_name():
    with pytest.raises(KeyError):
        db = sageodata_db.connect(service_name="DEWNR.World")


@pytest.mark.skipif(INTRANET is False, reason="Need to be connected to intranet")
def test_create_well_instances_dtype():
    db = sageodata_db.connect()
    well = db._create_well_instances([8721])[0]
    assert isinstance(well, Well)


@pytest.mark.skipif(INTRANET is False, reason="Need to be connected to intranet")
def test_create_well_instances_unit_no_parsed():
    db = sageodata_db.connect()
    well = db._create_well_instances([8721])[0]
    assert isinstance(well.unit_no, UnitNumber)


@pytest.mark.skipif(INTRANET is False, reason="Need to be connected to intranet")
def test_create_well_instances_unit_pulled_yep():
    db = sageodata_db.connect()
    well = db._create_well_instances([8721])[0]
    assert well.unit_hyphen == "5930-1049"


@pytest.mark.skipif(INTRANET is False, reason="Need to be connected to intranet")
def test_create_well_instances_easting():
    db = sageodata_db.connect()
    well = db._create_well_instances([8721])[0]
    assert well.easting > 530000 and well.easting < 540000
