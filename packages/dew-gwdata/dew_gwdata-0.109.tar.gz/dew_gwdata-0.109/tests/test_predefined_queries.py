import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest


import dew_gwdata
from dew_gwdata.sageodata import get_predefined_query_filenames

from utils import on_state_intranet

INTRANET = on_state_intranet()


def get_predefined_query_filenames():
    assert "hydrostrat_logs.sql" in get_predefined_query_filenames()


@pytest.mark.skipif(INTRANET is False, reason="Need to be connected to intranet")
def test_drillhole_details():
    db = dew_gwdata.sageodata()
    assert 593001049 in db.drillhole_details([8721]).unit_long.values


@pytest.mark.skipif(INTRANET is False, reason="Need to be connected to intranet")
def test_hydrostrat_logs_result_length():
    db = dew_gwdata.sageodata()
    assert len(db.hydrostrat_logs([8721, 201270])) == 9
