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


print("\nWorking in target timezone '" + use_target_tz + "' (" + th.get_tz_zoneinfo().tzname(datetime(2025, 1, 1)) + ", " + th.get_tz_zoneinfo().tzname(datetime(2025, 7, 1)) + ")")

print("\nExamples for other methods:")

print("\nget_tz_zoneinfo()")
print("TZ ZoneInfo:", type(th.get_tz_zoneinfo()))

print("\nget_tz_zone_name()")
print("TZ name:", th.get_tz_zone_name())

print("\nget_tz_zone_abbreviations()")
print("TZ abbreviations:", th.get_tz_zone_abbreviations())
