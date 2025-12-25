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

print("\nExamples for nanoseconds and timestamps methods:")

print("\nget_nsse_from_dtTZ()")
dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
print(p_str(dtTZ.strftime(use_time_string_format)), "->", str(th.get_nsse_from_dtTZ(dtTZ)))

print("\nget_nsse_from_dtUTC()")
dtUTC = datetime(2025, 5, 15, 10, 0, 0, 0, th.get_utc_zoneinfo())
print(p_str(dtUTC.strftime(use_time_string_format)), "->", str(th.get_nsse_from_dtUTC(dtUTC)))

print("\nget_nsse_from_strTZ()")
strTZ = dtTZ.strftime(use_time_string_format)
print(p_str(strTZ), "->", str(th.get_nsse_from_strTZ(strTZ, use_time_string_format)))

print("\nget_nsse_from_strUTC()")
strUTC = dtUTC.strftime(use_time_string_format)
print(p_str(strUTC), "->", str(th.get_nsse_from_strUTC(strUTC, use_time_string_format)))

print("\nget_nsse_from_ts()")
ts = dtTZ.timestamp()
print(str(ts), "->", str(th.get_nsse_from_ts(ts)))

print("\nget_nsse_from_text()")
txt = "1970-01-01 04:00:00.000000 UTC"
print(p_str(txt), "->", str(th.get_nsse_from_text(txt, use_time_string_format)))

print("\nget_nsse_from_text()")
txt = "14400000000000"
print(p_str(txt), "->", str(th.get_nsse_from_text(txt, use_time_string_format)))

print("\nget_ts_from_dtTZ()")
print(p_str(dtTZ.strftime(use_time_string_format)), "->", str(th.get_ts_from_dtTZ(dtTZ)))

print("\nget_ts_from_dtUTC()")
print(p_str(dtUTC.strftime(use_time_string_format)), "->", str(th.get_ts_from_dtUTC(dtUTC)))

print("\nget_ts_from_nsse()")
nsse = 14400000000000
print(str(nsse), "->", str(th.get_ts_from_nsse(nsse)))

print("\nget_ts_from_strTZ()")
txt = "1970-01-01 05:00:00.000000 CET"
print(p_str(txt), "->", str(th.get_ts_from_strTZ(txt, use_time_string_format)))

print("\nget_ts_from_strUTC()")
txt = "1970-01-01 04:00:00.000000 UTC"
print(p_str(txt), "->", str(th.get_ts_from_strUTC(txt, use_time_string_format)))


