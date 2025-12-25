from spTimeHelperPy import TimeHelper

import os
from datetime import datetime

import pytest

f_path, f_ext = os.path.splitext(__file__)
f_head, f_tail = os.path.split(f_path)
file_path = f_head + os.sep

use_config_file_name = file_path + "config.ini"
use_section_name = "My TimeHelper Setting"
use_target_tz = "Europe/Paris"
use_time_string_format = '%Y-%m-%d %H:%M:%S.%f %Z'

bad_config_file_name = file_path + "bad_config.ini"
bad_section_name = "BadTimeHelper"
bad_target_tz = "Hamburg"
bad_time_string_format = '%A-%A-%d %H:%M:%S.%fZ'

# 4 hours past epoch
FOUR_HOURS_IN_SEC = 14400.0


def test_01():
    # with config and section
    try:
        th = TimeHelper(use_config_file_name, use_section_name)
    except Exception as e:
        assert False, "Got an exception ()" + str(type(e)) + ") " + str(e)

def test_01A():
    # with config and no section
    try:
        th = TimeHelper(use_config_file_name)
    except Exception as e:
        assert False, "Got an exception ()" + str(type(e)) + ") " + str(e)

def test_01B():
    # with config and empty section
    with pytest.raises(ValueError):
        th = TimeHelper(use_config_file_name, "")

def test_02():
    # with config and bad section
    with pytest.raises(ValueError):
        th = TimeHelper(use_config_file_name, bad_section_name)

def test_03():
    # with bad config and section
    with pytest.raises(ValueError):
        th = TimeHelper(bad_config_file_name, use_section_name)

def test_04():
    # with bad config and section
    with pytest.raises(TypeError):
        th = TimeHelper(33, use_section_name)

def test_05():
    # with target_tz
    try:
        th = TimeHelper(target_tz=use_target_tz)
    except Exception as e:
        assert False, "Got an exception ()" + str(type(e)) + ") " + str(e)

def test_06():
    # with bad target_tz
    with pytest.raises(ValueError):
        th = TimeHelper(target_tz=bad_target_tz)

def test_06A():
    # with bad target_tz
    with pytest.raises(TypeError):
        th = TimeHelper(target_tz=55)

# TimeHelper for all following tests
th = TimeHelper(target_tz="Europe/Berlin", time_string_format="%Y-%m-%d %H:%M:%S")

def test_07():
    # dtTZ from dtUTC
    dtUTC = datetime(2025, 7, 1, 10, 0, 0, 0, th.get_utc_zoneinfo())
    dt = th.get_dtTZ_from_dtUTC(dtUTC)
    assert dt.strftime(use_time_string_format) == "2025-07-01 12:00:00.000000 CEST"

def test_08():
    # dtTZ from NSSE
    nsse = 1751364000000000000
    dt = th.get_dtTZ_from_nsse(nsse)
    assert dt.strftime(use_time_string_format) == "2025-07-01 12:00:00.000000 CEST"

# skipped
#def test_09():


def test_10():
    # dzTZ from strTZ
    dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
    strTZ = dtTZ.strftime(use_time_string_format)
    dt = th.get_dtTZ_from_strTZ(strTZ, use_time_string_format)
    assert dtTZ == dt

def test_10A():
    # dzTZ from strTZ with bad timezone abbreviation
    dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
    strTZ = dtTZ.strftime(use_time_string_format).replace("CEST", "XXXX")
    with pytest.raises(ValueError):
        dt = th.get_dtTZ_from_strTZ(strTZ, use_time_string_format)

def test_11():
    # dtTZ from strUTC
    dtUTC = datetime(2002, 2, 22, 12, 0, 0, 0, th.get_utc_zoneinfo())
    strUTC = dtUTC.strftime(use_time_string_format)
    dt = th.get_dtTZ_from_strUTC(strUTC, use_time_string_format)
    assert dtUTC.timestamp() == dt.timestamp()

def test_12():
    # dtTZ from 4h timestamp with use_time_string_format
    dtTZ = th.get_dtTZ_from_ts(FOUR_HOURS_IN_SEC)
    assert dtTZ.strftime(use_time_string_format) == "1970-01-01 05:00:00.000000 CET"

def test_12A():
    # dtTZ from 4h timestamp with th's time_string_format
    dtTZ = th.get_dtTZ_from_ts(FOUR_HOURS_IN_SEC)
    assert dtTZ.strftime(th._get_time_string_format()) == "1970-01-01 05:00:00"

def test_07_Reverse():
    # dtUTC from dtTZ
    dtTZ = datetime(2025, 7, 1, 12, 0, 0, 0, th.get_tz_zoneinfo())
    dt = th.get_dtUTC_from_dtTZ(dtTZ)
    assert dt.strftime(use_time_string_format) == "2025-07-01 10:00:00.000000 UTC"

def test_13():
    # dtUTC from NSSE
    nsse = 1751364000000000000
    dt = th.get_dtUTC_from_nsse(nsse)
    assert dt.strftime(use_time_string_format) == "2025-07-01 10:00:00.000000 UTC"


# skipped
#def test_14():

def test_15():
    # dtUTC from strTZ
    dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
    strTZ = dtTZ.strftime(use_time_string_format)
    dt = th.get_dtUTC_from_strTZ(strTZ, use_time_string_format)
    assert dtTZ.timestamp() == dt.timestamp()

def test_16():
    # dtUTC from strUTC
    dtUTC = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_utc_zoneinfo())
    strUTC = dtUTC.strftime(use_time_string_format)
    dt = th.get_dtUTC_from_strUTC(strUTC, use_time_string_format)
    assert dtUTC.timestamp() == dt.timestamp()

def test_17():
    # dtUTC from 4h timestamp with use_time_string_format
    dtUTC = th.get_dtUTC_from_ts(FOUR_HOURS_IN_SEC)
    assert dtUTC.strftime(use_time_string_format) == "1970-01-01 04:00:00.000000 UTC"

def test_18():
    # NSSE from dtTZ
    dtTZ = datetime(1970, 1, 1, 5, 0, 0, 0, th.get_tz_zoneinfo())
    assert th.get_nsse_from_dtTZ(dtTZ) == 14400000000000

def test_19():
    # NSSE from dtUTC
    dtUTC = datetime(1970, 1, 1, 4, 0, 0, 0, th.get_utc_zoneinfo())
    assert th.get_nsse_from_dtUTC(dtUTC) == 14400000000000

def test_20():
    # strTZ from dtTZ
    dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
    assert th.get_strTZ_from_dtTZ(dtTZ, use_time_string_format) == "2025-05-15 12:00:00.000000 CEST"

def test_21():
    # strTZ from dtUTC
    dtUTC = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_utc_zoneinfo())
    assert th.get_strTZ_from_dtUTC(dtUTC, use_time_string_format) == "2025-05-15 14:00:00.000000 CEST"

def test_22():
    # strTZ from nsse
    nsse = 2567998223500000000
    assert th.get_strTZ_from_nsse(nsse, use_time_string_format) == "2051-05-18 06:50:23.500000 CEST"

def test_23():
    # strTZ from strUTC
    txt = "1970-01-01 04:00:00.000000 UTC"
    assert th.get_strTZ_from_strUTC(txt, use_time_string_format, use_time_string_format) == "1970-01-01 05:00:00.000000 CET"

def test_24():
    # strTZ from ts
    ts = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo()).timestamp()
    assert th.get_strTZ_from_ts(ts, use_time_string_format) == "2025-05-15 12:00:00.000000 CEST"


def test_25():
    # strUTC from dtTZ
    dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
    assert th.get_strUTC_from_dtTZ(dtTZ, use_time_string_format) == "2025-05-15 10:00:00.000000 UTC"

def test_26():
    # strUTC from dtUTC
    dtUTC = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_utc_zoneinfo())
    assert th.get_strUTC_from_dtUTC(dtUTC, use_time_string_format) == "2025-05-15 12:00:00.000000 UTC"

def test_27():
    # strUTC from nsse
    nsse = 2567998223500000000
    assert th.get_strUTC_from_nsse(nsse, use_time_string_format) == "2051-05-18 04:50:23.500000 UTC"

def test_28():
    # strUTC from strTZ
    txt = "1970-01-01 05:00:00.000000 CET"
    assert th.get_strUTC_from_strTZ(txt, use_time_string_format, use_time_string_format) == "1970-01-01 04:00:00.000000 UTC"

def test_29():
    # strUTC from ts
    ts = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_utc_zoneinfo()).timestamp()
    assert th.get_strUTC_from_ts(ts, use_time_string_format) == "2025-05-15 12:00:00.000000 UTC"


def test_30_before():
    # nsse from dtTZ
    dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
    assert th.get_nsse_from_dtTZ(dtTZ) == 1747303200000000000

def test_30():
    # nsse from dtUTC
    dtUTC = datetime(2025, 5, 15, 10, 0, 0, 0, th.get_utc_zoneinfo())
    assert th.get_nsse_from_dtUTC(dtUTC) == 1747303200000000000

def test_31():
    # nsse from strTZ
    strTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo()).strftime(use_time_string_format)
    assert th.get_nsse_from_strTZ(strTZ, use_time_string_format) == 1747303200000000000

def test_32_before():
    # nsse from strUTC
    strUTC = datetime(2025, 5, 15, 10, 0, 0, 0, th.get_utc_zoneinfo()).strftime(use_time_string_format)
    assert th.get_nsse_from_strUTC(strUTC, use_time_string_format) == 1747303200000000000

def test_32():
    # nsse from ts
    ts = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo()).timestamp()
    assert th.get_nsse_from_ts(ts) == 1747303200000000000

def test_33():
    # nsse from text1
    txt = "1970-01-01 04:00:00.000000 UTC"
    assert th.get_nsse_from_text(txt, use_time_string_format) == 14400000000000

def test_34():
    # nsse from text2
    txt = "14400000000000"
    assert th.get_nsse_from_text(txt, use_time_string_format) == 14400000000000

def test_35():
    # ts from dtTZ
    assert th.get_ts_from_dtTZ(datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())) == 1747303200.0

def test_36():
    # ts from dtUTC
    assert th.get_ts_from_dtUTC(datetime(2025, 5, 15, 10, 0, 0, 0, th.get_utc_zoneinfo())) == 1747303200.0

def test_37():
    # ts from nsse
    nsse = 14400000000000
    assert th.get_ts_from_nsse(nsse) == 14400.0

def test_38():
    # ts from strTZ
    txt = "1970-01-01 05:00:00.000000 CET"
    assert th.get_ts_from_strTZ(txt, use_time_string_format) == 14400.0

def test_39():
    # ts from strUTC
    txt = "1970-01-01 04:00:00.000000 UTC"
    assert th.get_ts_from_strUTC(txt, use_time_string_format) == 14400.0

