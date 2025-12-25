# ================================================================================
#
#   TimeHelper class
#
#   object for .....
#
#   MIT License
#
#   Copyright (c) 2024 krokoreit (krokoreit@gmail.com)
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#
# ================================================================================

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import configparser

from spArgValidatorPy import ArgValidator

av = ArgValidator()

cleaner_last_error = ""
def cleaned_str_and_fmt_to_datetime(strTZ, fmt, abbr1, abbr2):
    """Try to get datetime from strTZ and fmt with bypassing the issue of %Z failing in strptime(). 
    Returns datetime or - if exception occurs - returns None with Exception message stored in cleaner_last_error."""
    global cleaner_last_error
    cleaner_last_error = ""
    # erase %Z timezone in format
    clean_fmt = fmt.replace("%Z", "").strip()
    # erase timezone abbreviation in strTZ
    clean_strTZ = strTZ.replace(abbr1, "").replace(abbr2, "").strip()
    # try to create naive datetime, i.e. based on datetime string without 'local'
    try:
        dt = datetime.strptime(clean_strTZ, clean_fmt)
    except Exception as e:
        cleaner_last_error = str(e)
        dt = None
    return dt


def ts_2_nsse(f_value):
    """Returns a nsse value from a ts float value."""
    return int(f_value * 1000000000)


# ================================================================================

class TimeHelper:
    def __init__(self, config_file_name=None, section_name=None, *, target_tz=None, time_string_format=None):

        # use own checks in __init__ instead of get_validated_.. to get class name constructor into Exception message
        err_class_prefix = self.__class__.__name__ + '():'
        err_bad_argument = err_class_prefix + " invalid %s argument."
        err_empty_string = err_class_prefix + " argument %s is an empty string."
        
        # default section_name
        if section_name is None:
            section_name = "TimeHelper"
        # default timezone
        if target_tz is None:
            target_tz = 'Europe/Berlin'
        # defaults datetime string format
        if time_string_format is None:
            time_string_format = "%Y-%m-%dT%H:%M:%S.%fZ"


        if config_file_name is not None and section_name is not None:
            # config setup must provide valid args
            if not isinstance(config_file_name, str):
                raise TypeError (err_bad_argument % "config_file_name")
            if len(config_file_name) == 0:
                raise ValueError (err_empty_string % "config_file_name")
            
            # need to resolve relative path given for config_file_name when cwd is not the correct starting point
            # check for Path.exists() == False
            p1 = Path(config_file_name)
            if not p1.exists():
                # get absolute path of main script and resolve with Path object
                f_path, f_ext = os.path.splitext(sys.argv[0])
                f_head, f_tail = os.path.split(f_path)
                path_to_resolve = Path(os.path.abspath(f_head) + os.sep + config_file_name)
                path_to_resolve.resolve()
                # now Path.exists() or raise exception
                if path_to_resolve.exists():
                    config_file_name = str(path_to_resolve)
                else:
                    raise ValueError (err_class_prefix + " config file '" + config_file_name + "' does not exist.")

            if not isinstance(section_name, str):
                raise TypeError (err_bad_argument % "section_name")
            if len(section_name) == 0:
                raise ValueError (err_empty_string % "section_name")

            config = configparser.ConfigParser(inline_comment_prefixes='#', empty_lines_in_values=False)
            config.read(config_file_name)
            if config.has_section(section_name):
                target_tz = config[section_name].get('target_tz', target_tz)
                time_string_format = config[section_name].get('time_format', time_string_format)
            else:
                raise ValueError (err_class_prefix + " section '" + section_name + "' does not exist in '" + config_file_name + "'.")

        
        # must have valid parameters now
        if not isinstance(target_tz, str):
            raise TypeError (err_bad_argument % "target_tz")
        if len(target_tz) == 0:
            raise ValueError (err_empty_string % "target_tz")
        if not isinstance(time_string_format, str):
            raise TypeError (err_bad_argument % "time_string_format")
        if len(time_string_format) == 0:
            raise ValueError (err_empty_string % "time_string_format")
        
        # try to use target_tz
        try:
            self._target_tz = ZoneInfo(target_tz)
        except Exception as e:
            raise ValueError(err_bad_argument % "target_tz" + " " + str(e))

        self._target_tz_zone = target_tz
        self._target_tz_abbr1 = self._target_tz.tzname(datetime(2025, 1, 1))
        self._target_tz_abbr2 = self._target_tz.tzname(datetime(2025, 7, 1))
        self._utc = ZoneInfo("UTC")
        self._time_string_format = time_string_format


    def _get_time_string_format(self, fmt=None):
        """Internal method to use fallback datetime string format (default or '%Y-%m-%d %H:%M:%S.%f')"""
        if fmt is None or not isinstance(fmt, str) or len(fmt) == 0:
            fmt = self._time_string_format
            if fmt is None:
                fmt = '%Y-%m-%d %H:%M:%S.%f'
        return fmt


    # -----------------------------------------------------------------------------
    # datetime target timezone
    # -----------------------------------------------------------------------------

    def get_dtTZ(self):
        """Returns the target timezone datetime, aka now."""
        return datetime.now(self._target_tz)


    def get_dtTZ_from_dtUTC(self, dtUTC):
        """Returns a target timezone datetime from an UTC datetime."""
        if not isinstance(dtUTC, datetime):
            raise TypeError("get_dtTZ_from_dtUTC() called with dtUTC argument not being a datetime object.")
        return dtUTC.astimezone(self._target_tz)


    def get_dtTZ_from_nsse(self, nsse):
        """Returns a target timezone datetime from nanoseconds since epoch."""
        nsse = av.get_validated_int("nsse", min_value=0)
        return datetime.fromtimestamp(nsse / 1000000000, self._target_tz)


    def get_dtTZ_from_strTZ(self, strTZ, time_string_format=None, second_hour=False):
        """Returns a target timezone datetime from a target timezone datetime string. For ambigious cases when switching 
        back to normal time in autumn (times for one hour occuring twice), use second_hour to 
        convert into datetime for the second occurance."""
        strTZ = av.get_validated_str("strTZ", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        second_hour = isinstance(second_hour, bool) and second_hour
        dt = cleaned_str_and_fmt_to_datetime(strTZ, fmt, self._target_tz_abbr1, self._target_tz_abbr2)
        if dt is None:
            raise ValueError("get_dtTZ_from_strTZ(): Converting " + strTZ + " failed with error: '" + cleaner_last_error + "'.")
        # make tz aware datetime for timezone and second_hour
        if second_hour:
            return dt.replace(tzinfo=self._target_tz, fold=1)
        else:
            return dt.replace(tzinfo=self._target_tz, fold=0)


    def get_dtTZ_from_strUTC(self, strUTC, time_string_format=None):
        """Returns a target timezone datetime from an UTC datetime string."""
        strUTC = av.get_validated_str("strUTC", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        # create naive datetime from datetime string and make it UTC aware and convert to trget TZ
        return datetime.strptime(strUTC, fmt).replace(tzinfo=self._utc).astimezone(self._target_tz)


    def get_dtTZ_from_ts(self, ts):
        """Returns a target timezone datetime from a timestamp."""
        ts = av.get_validated_float("ts", min_value=0.0)
        return datetime.fromtimestamp(ts, self._target_tz)


    # -----------------------------------------------------------------------------
    # datetime UTC
    # -----------------------------------------------------------------------------

    def get_dtUTC(self):
        """Returns the current UTC datetime, aka now."""
        return datetime.now(self._utc)
    

    def get_dtUTC_from_dtTZ(self, dtTZ):
        """Returns an UTC datetime from an target timezone datetime."""
        if not isinstance(dtTZ, datetime):
            raise TypeError("get_dtUTC_from_dtTZ() called with dtTZ argument not being a datetime object.")
        return dtTZ.astimezone(self._utc)


    def get_dtUTC_from_nsse(self, nsse):
        """Returns a UTC datetime from nanoseconds since epoch."""
        nsse = av.get_validated_int("nsse", min_value=0)
        return datetime.fromtimestamp(nsse / 1000000000, self._utc)


    def get_dtUTC_from_strTZ(self, strTZ, time_string_format=None, second_hour=False):
        """Returns a UTC datetime from a target timezone datetime string. For an ambigious case when switching 
        back to normal time in autumn (times for one hour occuring twice), use second_hour to 
        convert into datetime for the second occurance."""
        strTZ = av.get_validated_str("strTZ", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        second_hour = isinstance(second_hour, bool) and second_hour
        
        dt = cleaned_str_and_fmt_to_datetime(strTZ, fmt, self._target_tz_abbr1, self._target_tz_abbr2)
        if dt is None:
            raise ValueError("get_dtUTC_from_strTZ() converting " + strTZ + " failed with error: '" + cleaner_last_error + "'.")
        # make tz aware datetime for timezone and second_hour
        if second_hour:
            return dt.replace(tzinfo=self._target_tz, fold=1).astimezone(self._utc)
        else:
            return dt.replace(tzinfo=self._target_tz, fold=0).astimezone(self._utc)


    def get_dtUTC_from_strUTC(self, strUTC, time_string_format=None):
        """Returns a UTC datetime from an UTC datetime string."""
        strUTC = av.get_validated_str("strUTC", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        # create naive datetime from datetime string and make it UTC aware
        return datetime.strptime(strUTC, fmt).replace(tzinfo=self._utc)

    def get_dtUTC_from_ts(self, ts):
        """Returns a UTC datetime from a timestamp."""
        ts = av.get_validated_float("ts", min_value=0.0)
        return datetime.fromtimestamp(ts, self._utc)

    
    # -----------------------------------------------------------------------------
    # nanoseconds since epoch
    # -----------------------------------------------------------------------------

    def get_nsse(self):
        """Returns the current nanoseconds since epoch."""
        return ts_2_nsse(datetime.now().timestamp())

    def get_nsse_from_dtTZ(self, dtTZ):
        """Returns nanoseconds since epoch from an target timezone datetime."""
        if not isinstance(dtTZ, datetime):
            raise TypeError("get_nsse_from_dtTZ() called with dtTZ argument not being a datetime object.")
        return ts_2_nsse(dtTZ.timestamp())


    def get_nsse_from_dtUTC(self, dtUTC):
        """Returns nanoseconds since epoch from a UTC datetime."""
        if not isinstance(dtUTC, datetime):
            raise TypeError("get_nsse_from_dtUTC() called with dtUTC argument not being a datetime object.")
        return ts_2_nsse(dtUTC.timestamp())


    def get_nsse_from_strTZ(self, strTZ, time_string_format=None, second_hour=False):
        """Returns nanoseconds since epoch from an timezone datetime string. For an ambigious case when switching 
        back to normal time in autumn (times for one hour occuring twice), use second_hour to 
        convert into datetime for the second occurance."""
        strTZ = av.get_validated_str("strTZ", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        second_hour = isinstance(second_hour, bool) and second_hour
        
        dt = cleaned_str_and_fmt_to_datetime(strTZ, fmt, self._target_tz_abbr1, self._target_tz_abbr2)
        if dt is None:
            raise ValueError("get_nsse_from_strTZ(): Converting " + strTZ + " failed with error: '" + cleaner_last_error + "'.")
        # make tz aware datetime for timezone and second_hour
        if second_hour:
            return ts_2_nsse(dt.replace(tzinfo=self._target_tz, fold=1).timestamp())
        else:
            return ts_2_nsse(dt.replace(tzinfo=self._target_tz, fold=0).timestamp())


    def get_nsse_from_strUTC(self, strUTC, time_string_format=None):
        """Returns nanoseconds since epoch from an UTC datetime string."""
        strUTC = av.get_validated_str("strUTC", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        # create naive datetime from datetime string and make it UTC aware
        dt = datetime.strptime(strUTC, fmt).replace(tzinfo=self._utc)
        return ts_2_nsse(dt.timestamp())


    def get_nsse_from_text(self, from_text, time_string_format=None):
        """Returns nanoseconds since epoch from a text given as either a UTC datetime string or
        a string representation of a nanoseconds integer value."""
        from_text = av.get_validated_str("from_text", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        try:
            dt = datetime.strptime(from_text, fmt).replace(tzinfo=self._utc)
            return ts_2_nsse(dt.timestamp())
        except Exception as e:
            pass
        try:
            vInt = int(from_text)
            if str(vInt) == from_text:
                return vInt
        except Exception as e:
            pass
        raise Exception("get_nsse_from_text(): Error getting nanoseconds since epoch from '" + from_text + "'")


    def get_nsse_from_ts(self, ts):
        """Returns nanoseconds since epoch from a timestamp."""
        ts = av.get_validated_float("ts", min_value=0.0)
        return ts_2_nsse(ts)

    # -----------------------------------------------------------------------------
    # datetime string target timezone
    # -----------------------------------------------------------------------------

    def get_strTZ_from_dtTZ(self, dtTZ, time_string_format=None):
        """Returns a target timezone datetime string from a target timezone datetime."""
        if not isinstance(dtTZ, datetime):
            raise TypeError("get_strTZ_from_dtTZ() called with dtTZ argument not being a datetime object.")
        fmt = self._get_time_string_format(time_string_format)
        return dtTZ.strftime(fmt)


    def get_strTZ_from_dtUTC(self, dtUTC, time_string_format=None):
        """Returns a target timezone datetime string from an UTC datetime."""
        if not isinstance(dtUTC, datetime):
            raise TypeError("get_strTZ_from_dtUTC() called with dtUTC argument not being a datetime object.")
        fmt = self._get_time_string_format(time_string_format)
        return dtUTC.astimezone(self._target_tz).strftime(fmt)


    def get_strTZ_from_nsse(self, nsse, time_string_format=None):
        """Returns a target timezone datetime string from nanoseconds since epoch."""
        nsse = av.get_validated_int("nsse", min_value=0)
        fmt = self._get_time_string_format(time_string_format)
        return datetime.fromtimestamp(nsse / 1000000000, self._target_tz).strftime(fmt)


    def get_strTZ_from_strUTC(self, strUTC, time_string_format_UTC=None, time_string_format_TZ=None):
        """Returns a target timezone datetime string from an UTC datetime string."""
        strUTC = av.get_validated_str("strUTC", strict=True)
        fmt_UTC = self._get_time_string_format(time_string_format_UTC)
        fmt_TZ = self._get_time_string_format(time_string_format_TZ)
        # create naive datetime from datetime string and make it UTC aware and convert to trget TZ
        return datetime.strptime(strUTC, fmt_UTC).replace(tzinfo=self._utc).astimezone(self._target_tz).strftime(fmt_TZ)


    def get_strTZ_from_ts(self, ts, time_string_format=None):
        """Returns a target timezone datetime string from a timestamp."""
        ts = av.get_validated_float("ts", min_value=0.0)
        fmt = self._get_time_string_format(time_string_format)
        return datetime.fromtimestamp(ts, self._target_tz).strftime(fmt)


    # -----------------------------------------------------------------------------
    # datetime string UTC
    # -----------------------------------------------------------------------------

    def get_strUTC_from_dtTZ(self, dtTZ, time_string_format=None):
        """Returns an UTC datetime string from a target timezone datetime."""
        if not isinstance(dtTZ, datetime):
            raise TypeError("get_strUTC_from_dtTZ() called with dtTZ argument not being a datetime object.")
        fmt = self._get_time_string_format(time_string_format)
        return dtTZ.astimezone(self._utc).strftime(fmt)


    def get_strUTC_from_dtUTC(self, dtUTC, time_string_format=None):
        """Returns an UTC datetime string from an UTC datetime."""
        if not isinstance(dtUTC, datetime):
            raise TypeError("get_strUTC_from_dtUTC() called with dtUTC argument not being a datetime object.")
        fmt = self._get_time_string_format(time_string_format)
        return dtUTC.strftime(fmt)


    def get_strUTC_from_nsse(self, nsse, time_string_format=None):
        """Returns an UTC datetime string from nanoseconds since epoch."""
        nsse = av.get_validated_int("nsse", min_value=0)
        fmt = self._get_time_string_format(time_string_format)
        return datetime.fromtimestamp(nsse / 1000000000, self._utc).strftime(fmt)


    def get_strUTC_from_strTZ(self, strTZ, time_string_format_TZ=None, time_string_format_UTC=None, second_hour=False):
        """Returns a target timezone datetime string from a target timezone datetime string. For ambigious cases when switching 
        back to normal time in autumn (times for one hour occuring twice), use second_hour to 
        convert into datetime for the second occurance."""
        strTZ = av.get_validated_str("strTZ", strict=True)
        fmt_UTC = self._get_time_string_format(time_string_format_UTC)
        fmt_TZ = self._get_time_string_format(time_string_format_TZ)
        second_hour = isinstance(second_hour, bool) and second_hour
        dt = cleaned_str_and_fmt_to_datetime(strTZ, fmt_TZ, self._target_tz_abbr1, self._target_tz_abbr2)
        if dt is None:
            raise ValueError("get_strUTC_from_strTZ(): Converting " + strTZ + " failed with error: '" + cleaner_last_error + "'.")
        # make tz aware datetime for timezone and second_hour
        if second_hour:
            return dt.replace(tzinfo=self._target_tz, fold=1).astimezone(self._utc).strftime(fmt_UTC)
        else:
            return dt.replace(tzinfo=self._target_tz, fold=0).astimezone(self._utc).strftime(fmt_UTC)


    def get_strUTC_from_ts(self, ts, time_string_format=None):
        """Returns an UTC datetime string from a timestamp."""
        ts = av.get_validated_float("ts", min_value=0.0)
        fmt = self._get_time_string_format(time_string_format)
        return datetime.fromtimestamp(ts, self._utc).strftime(fmt)


    # -----------------------------------------------------------------------------
    # timestamp
    # -----------------------------------------------------------------------------

    def get_ts_from_dtTZ(self, dtTZ):
        """Returns timestamp from an target timezone datetime."""
        if not isinstance(dtTZ, datetime):
            raise TypeError("get_ts_from_dtTZ() called with dtTZ argument not being a datetime object.")
        return dtTZ.timestamp()
 

    def get_ts_from_dtUTC(self, dtUTC):
        """Returns timestamp from a UTC datetime."""
        if not isinstance(dtUTC, datetime):
            raise TypeError("get_ts_from_dtUTC() called with dtUTC argument not being a datetime object.")
        return dtUTC.timestamp()
 

    def get_ts_from_nsse(self, nsse):
        """Returns timestamp from nanoseconds since epoch."""
        nsse = av.get_validated_int("nsse", min_value=0)
        return nsse / 1000000000


    def get_ts_from_strTZ(self, strTZ, time_string_format=None, second_hour=False):
        """Returns a timestamp from an timezone datetime string. For an ambigious case when switching 
        back to normal time in autumn (times for one hour occuring twice), use second_hour to 
        convert into datetime for the second occurance."""
        strTZ = av.get_validated_str("strTZ", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        second_hour = isinstance(second_hour, bool) and second_hour
        
        dt = cleaned_str_and_fmt_to_datetime(strTZ, fmt, self._target_tz_abbr1, self._target_tz_abbr2)
        if dt is None:
            raise ValueError("get_ts_from_strTZ(): Converting " + strTZ + " failed with error: '" + cleaner_last_error + "'.")
        # make tz aware datetime for timezone and second_hour
        if second_hour:
            return dt.replace(tzinfo=self._target_tz, fold=1).timestamp()
        else:
            return dt.replace(tzinfo=self._target_tz, fold=0).timestamp()


    def get_ts_from_strUTC(self, strUTC, time_string_format=None):
        """Returns a timestamp from an UTC datetime string."""
        strUTC = av.get_validated_str("strUTC", strict=True)
        fmt = self._get_time_string_format(time_string_format)
        # create naive datetime from datetime string and make it UTC aware
        return datetime.strptime(strUTC, fmt).replace(tzinfo=self._utc).timestamp()


    # -----------------------------------------------------------------------------
    # zoneinfo
    # -----------------------------------------------------------------------------

    def get_tz_zoneinfo(self):
        """Returns the ZoneInfo object for target timezone."""
        return self._target_tz

    def get_tz_zone_name(self):
        """Returns the name of target timezone."""
        return self._target_tz_zone

    def get_tz_zone_abbreviations(self):
        """Returns a tuple with abbreviations for normal and daylight saving periods of target timezone."""
        return self._target_tz_abbr1, self._target_tz_abbr2

    def get_utc_zoneinfo(self):
        """Returns the ZoneInfo object for UTC."""
        return self._utc

