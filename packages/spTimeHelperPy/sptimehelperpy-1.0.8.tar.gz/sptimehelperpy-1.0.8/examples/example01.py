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
print("TZ now: ", th.get_dtTZ())
print("UTC now:", th.get_dtUTC())
print("nsse   :", th.get_nsse())


print("\nExamples for datetime methods:")


# 4 hours past epoch
FOUR_HOURS_IN_SEC = 14400.0
print("\nget_dtTZ_from_ts()")
print("4 hours past epoch in TZ:", th.get_dtTZ_from_ts(FOUR_HOURS_IN_SEC).strftime(use_time_string_format))

print("\nget_dtTZ_from_strTZ()")
dtTZ = datetime(2025, 5, 15, 12, 0, 0, 0, th.get_tz_zoneinfo())
strTZ = dtTZ.strftime(use_time_string_format)
dt = th.get_dtTZ_from_strTZ(strTZ, use_time_string_format)
print(p_str(strTZ), "->", dt.strftime(use_time_string_format))

print("\nget_dtUTC_from_strTZ()")
dtUTC = th.get_dtUTC_from_strTZ(strTZ, use_time_string_format)
print(p_str(strTZ), "->", dtUTC.strftime(use_time_string_format))

print("\nget_dtTZ_from_strUTC()")
dtUTC = datetime(2002, 2, 22, 12, 0, 0, 0, th.get_utc_zoneinfo())
strUTC = dtUTC.strftime(use_time_string_format)
dt = th.get_dtTZ_from_strUTC(strUTC, use_time_string_format)
print(p_str(strUTC), "->", dt.strftime(use_time_string_format))


print("\nget_dtTZ_from_nsse()")
nsse = 1766601120000000000
dt = th.get_dtTZ_from_nsse(nsse)
print(str(nsse), "->", dt.strftime(use_time_string_format))

print("\nget_dtUTC_from_nsse()")
nsse = 1766601120000000000
dt = th.get_dtUTC_from_nsse(nsse)
print(str(nsse), "->", dt.strftime(use_time_string_format))

