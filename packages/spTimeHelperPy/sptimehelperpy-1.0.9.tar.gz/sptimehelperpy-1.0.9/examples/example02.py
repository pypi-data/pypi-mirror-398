#   example01.py
#
#   file to demonstrate the use of spTimeHelperPy
#
#
import sys
import os
import time

from spTimeHelperPy import TimeHelper

from datetime import datetime


print("running Python executable from path", sys.executable)


use_config_file_name = "config.ini"
use_section_name = "TimeHelper"
use_target_tz = "Europe/Berlin"
use_time_string_format = "%Y-%m-%d %H:%M:%S.%f %Z"


th = TimeHelper(use_config_file_name)

# helper func
def p_str(txt):
    return "'" + txt + "'"

print("\nWorking in target timezone '" + use_target_tz + "' (" + th.get_tz_zoneinfo().tzname(datetime(2025, 1, 1)) + ", " + th.get_tz_zoneinfo().tzname(datetime(2025, 7, 1)) + ")")


print("\nExamples for datetime string methods:")


print("\nget_strTZ_from_dtTZ()")
dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
print(dtTZ.strftime(use_time_string_format), "->", p_str(th.get_strTZ_from_dtTZ(dtTZ, use_time_string_format)))

print("\nget_strTZ_from_dtUTC()")
dtUTC = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_utc_zoneinfo())
print(dtUTC.strftime(use_time_string_format), "->", p_str(th.get_strTZ_from_dtUTC(dtUTC, use_time_string_format)))

print("\nget_strTZ_from_nsse()")
nsse = 2567998223500000000
print(str(nsse), "->", p_str(th.get_strTZ_from_nsse(nsse, use_time_string_format)))

print("\nget_strTZ_from_strUTC()")
txt = "1970-01-01 04:00:00.000000 UTC"
print(p_str(txt), "->", p_str(th.get_strTZ_from_strUTC(txt, use_time_string_format, use_time_string_format)))

print("\nget_strTZ_from_ts()")
ts = dtTZ.timestamp()
print(str(ts), "->", p_str(th.get_strTZ_from_ts(ts, use_time_string_format)))

# ------------------------------------

print("\nget_strUTC_from_dtTZ()")
dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
print(dtTZ.strftime(use_time_string_format), "->", p_str(th.get_strUTC_from_dtTZ(dtTZ, use_time_string_format)))


print("\nget_strUTC_from_dtUTC()")
dtUTC = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_utc_zoneinfo())
print(dtUTC.strftime(use_time_string_format), "->", p_str(th.get_strUTC_from_dtUTC(dtUTC, use_time_string_format)))

print("\nget_strUTC_from_nsse()")
nsse = 2567998223500000000
print(str(nsse), "->", p_str(th.get_strUTC_from_nsse(nsse, use_time_string_format)))

print("\nget_strUTC_from_strTZ()")
txt = "1970-01-01 05:00:00.000000 CET"
print(p_str(txt), "->", p_str(th.get_strUTC_from_strTZ(txt, use_time_string_format, use_time_string_format)))

print("\nget_strUTC_from_ts()")
ts = dtUTC.timestamp()
print(str(ts), "->", p_str(th.get_strUTC_from_ts(ts, use_time_string_format)))


