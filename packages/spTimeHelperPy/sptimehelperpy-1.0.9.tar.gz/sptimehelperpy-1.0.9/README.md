# spTimeHelperPy

[![PyPI - Version](https://img.shields.io/pypi/v/spTimeHelperPy.svg)](https://pypi.org/project/spTimeHelperPy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/spTimeHelperPy.svg)](https://pypi.org/project/spTimeHelperPy)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


This package provides the Python module and TimeHelper class for easy conversion and handling of time values.

Python’s datetime and timestamp objects come with various methods to deal with time values. However, often additional functionality is needed, especially when dealing with databases, where time values are stored as nanoseconds since epoch (QuestDB , InfluxDB) or as string representations of a datetime (MariaDB, MySQL). Furthermore, time values need to be converted between the UTC values stored in a database and the timezone values obtained or displayed in an application.

The module’s TimeHelper class contains methods to convert between
*	a datetime object with a UTC value (abbreviated dtUTC) or a target timezone value (dtTZ)
*	a string representation of a datetime with a UTC value (strUTC) or a target timezone value (strTZ)
*	a timestamp value (ts),
*	nanoseconds since epoch (nsse)

Conversion methods are named with a uniform nomenclature using these value types, e.g. get_dtUTC_from_nsse() or get_nsse_from_dtTZ().

To simplify conversion to and from strings, a TimeHelper object can be initiated with an optional time format string, which is used as a default format. Alternatively, a time format string can be given as an optional argument for each conversion method.

Especially for time scale databases and having data stored in a text (or CSV) file, TimeHelper’s get_nsse_from_text() method allows for the text input being a UTC datetime string or a string representation of an integer (nanoseconds). This is helpful, as import routines can digest either value type from the text file.

Additional methods cover getting the target timezone’s ZoneInfo object, its name (e.g. ‘Europe/Berlin’) or a tuple with its abbreviations, e.g. ('CET', 'CEST').

For more details, see the API reference below and the demonstration code in the four files of the examples folder.

Enjoy

&emsp;krokoreit  
&emsp;&emsp;&emsp;<img src="https://github.com/krokoreit/spTimeHelperPy/blob/main/assets/krokoreit-01.svg?raw=true" width="140"/>


## Installation

```console
pip install spTimeHelperPy
```


## Usage & API

### TimeHelper Class
Import module:
```py
  from spTimeHelperPy import TimeHelper
```
TimeHelper objects use a target timezone (target_tz) for converting time values between UTC and target_tz. Additionally you can provide a time format string, e.g. '%Y-%m-%d %H:%M:%S.%f', which will be used as a default format by various methods.

As in most programs such information will be user specific and defined in a configuration file, TimeHelper uses ConfigParser to extract the values from a file, which contains entries like this:
```ini
  [TimeHelper]
  # target time zone and format for converting time strings
  target_tz = Europe/Berlin
  # mask % in format with a leading %, i.e. %Y -> %%Y
  time_format = %%Y-%%m-%%d %%H:%%M:%%S.%%fZ
```

When using a configuration file, a TimeHelper object is created with the name of the configuration file and an optional section name (defaults to 'TimeHelper'):
```py
  th = TimeHelper('config.ini')
  th = TimeHelper('config.ini', 'My TimeHelper Setting')
```

Alternatively, a TimeHelper object can also be created by directly providing target_tz and optionally time_string_format as keyword arguments:
```py
  th = TimeHelper(target_tz="Europe/Paris")
  th = TimeHelper(target_tz="Europe/Paris", time_string_format='%Y-%m-%dT%H:%M:%S.%fZ')
```
</br>


### API

#### Method Parameters
TimeHelper object's methods are used like
```py
  time_string_format = "%Y-%m-%d %H:%M:%S.%f %Z"
  strUTC = "1970-01-01 04:00:00.000000 UTC"
  dt = th.get_dtTZ_from_strUTC(strUTC, time_string_format)
```

All methods and their arguments are uniformly named with the following definitions
* dtTZ  
datetime object for the target timezone. The target timezone was set when creating the TimeHelper object and datetime objects used as arguments will be treated as belonging to this timezone.
* dtUTC  
datetime object for UTC. 
* strTZ  
a string representation of a datetime for a target timezone value
* strUTC  
a string representation of a datetime for a UTC value
* time_string_format, time_string_format_TZ or time_string_format_UTC  
a string with the format applied for converting datetime objects to strings and vice versa. Note that when the format string includes the '%Z' specifier for a timezone's abbreviation and it is used for parsing strUTC or strTZ values, then only 'UTC' or the abbreviations for the target timezone can be converted. All other 'unknown' abbreviations will cause an exception.
* nsse  
an integer value for nanoseconds since epoch
* ts  
a float value for a timestamp value (which represents full seconds and fractions thereof since epoch)
* second_hour  
an optional argument for conversion of strTZ strings. When switching from daylight saving time back to normal time in autumn, the times for one hour are occurring twice. For such ambiguous cases use second_hour to specify that strTZ is for the second occurrence.



</br>

#### Methods<a id="methods"></a>
* [The datetime Methods](#datetime-methods)  
  * [get_dtTZ()](#get_dtTZ-method)  
  * [get_dtTZ_from_dtUTC()](#get_dtTZ_from_dtUTC-method)  
  * [get_dtTZ_from_nsse()](#get_dtTZ_from_nsse-method)  
  * [get_dtTZ_from_strTZ()](#get_dtTZ_from_strTZ-method)  
  * [get_dtTZ_from_strUTC()](#get_dtTZ_from_strUTC-method)  
  * [get_dtTZ_from_ts()](#get_dtTZ_from_ts-method)  
  * [get_dtUTC()](#get_dtUTC-method)  
  * [get_dtUTC_from_dtTZ()](#get_dtUTC_from_dtTZ-method)  
  * [get_dtUTC_from_nsse()](#get_dtUTC_from_nsse-method)  
  * [get_dtUTC_from_strTZ()](#get_dtUTC_from_strTZ-method)  
  * [get_dtUTC_from_strUTC()](#get_dtUTC_from_strUTC-method)  
  * [get_dtUTC_from_ts()](#get_dtUTC_from_ts-method)  
* [The Nanoseconds since Epoch Methods](#nanoseconds-since-epoch-methods)  
  * [get_nsse()](#get_nsse-method)  
  * [get_nsse_from_dtTZ()](#get_nsse_from_dtTZ-method)  
  * [get_nsse_from_dtUTC()](#get_nsse_from_dtUTC-method)  
  * [get_nsse_from_strTZ()](#get_nsse_from_strTZ-method)  
  * [get_nsse_from_strUTC()](#get_nsse_from_strUTC-method)  
  * [get_nsse_from_text()](#get_nsse_from_text-method)  
  * [get_nsse_from_ts()](#get_nsse_from_ts-method)  
* [The datetime string Methods](#datetime-string-methods)  
  * [get_strTZ_from_dtTZ()](#get_strTZ_from_dtTZ-method)  
  * [get_strTZ_from_dtUTC()](#get_strTZ_from_dtUTC-method)  
  * [get_strTZ_from_nsse()](#get_strTZ_from_nsse-method)  
  * [get_strTZ_from_strUTC()](#get_strTZ_from_strUTC-method)  
  * [get_strTZ_from_ts()](#get_strTZ_from_ts-method)  
  * [get_strUTC_from_dtTZ()](#get_strUTC_from_dtTZ-method)  
  * [get_strUTC_from_dtUTC()](#get_strUTC_from_dtUTC-method)  
  * [get_strUTC_from_nsse()](#get_strUTC_from_nsse-method)  
  * [get_strUTC_from_strTZ()](#get_strUTC_from_strTZ-method)  
  * [get_strUTC_from_ts()](#get_strUTC_from_ts-method)  
* [The timestamp Methods](#timestamp-methods)  
  * [get_ts_from_dtTZ()](#get_ts_from_dtTZ-method)  
  * [get_ts_from_dtUTC()](#get_ts_from_dtUTC-method)  
  * [get_ts_from_nsse()](#get_ts_from_nsse-method)  
  * [get_ts_from_strTZ()](#get_ts_from_strTZ-method)  
  * [get_ts_from_strUTC()](#get_ts_from_strUTC-method)  
* [The ZoneInfo Methods](#zoneinfo-methods)  
  * [get_tz_zoneinfo()](#get_tz_zoneinfo-method)  
  * [get_tz_zone_name()](#get_tz_zone_name-method)  
  * [get_tz_zone_abbreviations()](#get_tz_zone_abbreviations-method)  
  * [get_utc_zoneinfo()](#get_utc_zoneinfo-method)  

</br>
</br>

#### The datetime Methods<a id="datetime-methods"></a>  

#### get_dtTZ() Method<a id="get_dtTZ-method"></a>
```py
  get_dtTZ()
```
Returns the target timezone datetime, aka now.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtTZ_from_dtUTC() Method<a id="get_dtTZ_from_dtUTC-method"></a>
```py
  get_dtTZ_from_dtUTC(dtUTC)
```
Returns a target timezone datetime from a UTC datetime.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtTZ_from_nsse() Method<a id="get_dtTZ_from_nsse-method"></a>
```py
  get_dtTZ_from_nsse(nsse)
```
Returns a target timezone datetime from nanoseconds since epoch.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtTZ_from_strTZ() Method<a id="get_dtTZ_from_strTZ-method"></a>
```py
  get_dtTZ_from_strTZ(strTZ, time_string_format=None, second_hour=False)
```
Returns a target timezone datetime from a target timezone datetime string. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. For an ambiguous case when switching back to normal time in autumn (times for one hour occurring twice), use True for second_hour to convert into datetime for the second occurrence.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtTZ_from_strUTC() Method<a id="get_dtTZ_from_strUTC-method"></a>
```py
  get_dtTZ_from_strUTC(strUTC, time_string_format=None)
```
Returns a target timezone datetime from a UTC datetime string. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtTZ_from_ts() Method<a id="get_dtTZ_from_ts-method"></a>
```py
  get_dtTZ_from_ts(ts)
```
Returns a target timezone datetime from a timestamp.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtUTC() Method<a id="get_dtUTC-method"></a>
```py
  get_dtUTC()
```
Returns the current UTC datetime, aka now.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtUTC_from_dtTZ() Method<a id="get_dtUTC_from_dtTZ-method"></a>
```py
  get_dtUTC_from_dtTZ(dtTZ)
```
Returns a UTC datetime from an target timezone datetime.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtUTC_from_nsse() Method<a id="get_dtUTC_from_nsse-method"></a>
```py
  get_dtUTC_from_nsse(nsse)
```
Returns a UTC datetime from nanoseconds since epoch.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtUTC_from_strTZ() Method<a id="get_dtUTC_from_strTZ-method"></a>
```py
  get_dtUTC_from_strTZ(strTZ, time_string_format=None, second_hour=False)
```
Returns a UTC datetime from a target timezone datetime string. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. For an ambiguous case when switching back to normal time in autumn (times for one hour occurring twice), use True for second_hour to convert into datetime for the second occurrence.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtUTC_from_strUTC() Method<a id="get_dtUTC_from_strUTC-method"></a>
```py
  get_dtUTC_from_strUTC(strUTC, time_string_format=None)
```
Returns a UTC datetime from a UTC datetime string. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_dtUTC_from_ts() Method<a id="get_dtUTC_from_ts-method"></a>
```py
  get_dtUTC_from_ts(ts)
```
Returns a UTC datetime from a timestamp.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### The Nanoseconds since Epoch Methods<a id="nanoseconds-since-epoch-methods"></a>  

#### get_nsse() Method<a id="get_nsse-method"></a>
```py
  get_nsse()
```
Returns the current nanoseconds since epoch.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_nsse_from_dtTZ() Method<a id="get_nsse_from_dtTZ-method"></a>
```py
  get_nsse_from_dtTZ(dtTZ)
```
Returns nanoseconds since epoch from an target timezone datetime.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_nsse_from_dtUTC() Method<a id="get_nsse_from_dtUTC-method"></a>
```py
  get_nsse_from_dtUTC(dtUTC)
```
Returns nanoseconds since epoch from a UTC datetime.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_nsse_from_strTZ() Method<a id="get_nsse_from_strTZ-method"></a>
```py
  get_nsse_from_strTZ(strTZ, time_string_format=None, second_hour=False)
```
Returns nanoseconds since epoch from an timezone datetime string. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. For an ambiguous case when switching back to normal time in autumn (times for one hour occurring twice), use True for second_hour to convert into datetime for the second occurrence.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>

#### get_nsse_from_strUTC() Method<a id="get_nsse_from_strUTC-method"></a>
```py
  get_nsse_from_strUTC(strUTC, time_string_format=None)
```
Returns nanoseconds since epoch from a UTC datetime string. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_nsse_from_text() Method<a id="get_nsse_from_text-method"></a>
```py
  get_nsse_from_text(from_text, time_string_format=None)
```
Returns nanoseconds since epoch from a text given as either a UTC datetime string or a string representation of a nanoseconds integer value. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. 

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>

#### get_nsse_from_ts() Method<a id="get_nsse_from_ts-method"></a>
```py
  get_nsse_from_ts(ts)
```
Returns nanoseconds since epoch from a timestamp.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### The datetime string Methods<a id="datetime-string-methods"></a>  

#### get_strTZ_from_dtTZ() Method<a id="get_strTZ_from_dtTZ-method"></a>
```py
  get_strTZ_from_dtTZ(dtTZ, time_string_format=None)
```
Returns a target timezone datetime string from a target timezone datetime. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_strTZ_from_dtUTC() Method<a id="get_strTZ_from_dtUTC-method"></a>
```py
  get_strTZ_from_dtUTC(dtUTC, time_string_format=None)
```
Returns a target timezone datetime string from a UTC datetime. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_strTZ_from_nsse() Method<a id="get_strTZ_from_nsse-method"></a>
```py
  get_strTZ_from_nsse(nsse, time_string_format=None)
```
Returns a target timezone datetime string from nanoseconds since epoch. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. 

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_strTZ_from_strUTC() Method<a id="get_strTZ_from_strUTC-method"></a>
```py
  get_strTZ_from_strUTC(strUTC, time_string_format_UTC=None, time_string_format_TZ=None)
```
Returns a target timezone datetime string from a UTC datetime string. Use the optional time_string_format_UTC and time_string_format_TZ arguments to specify a format for converting the datetime strings. If omitted or None, the default format of the TimeHelper object is used. 

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_strTZ_from_ts() Method<a id="get_strTZ_from_ts-method"></a>
```py
  get_strTZ_from_ts(ts, time_string_format=None)
```
Returns a target timezone datetime string from a timestamp. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_strUTC_from_dtTZ() Method<a id="get_strUTC_from_dtTZ-method"></a>
```py
  get_strUTC_from_dtTZ(dtTZ, time_string_format=None)
```
Returns a UTC datetime string from a target timezone datetime. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. 

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_strUTC_from_dtUTC() Method<a id="get_strUTC_from_dtUTC-method"></a>
```py
  get_strUTC_from_dtUTC(dtUTC, time_string_format=None)
```
Returns a UTC datetime string from a UTC datetime. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. 

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_strUTC_from_nsse() Method<a id="get_strUTC_from_nsse-method"></a>
```py
  get_strUTC_from_nsse(nsse, time_string_format=None)
```
Returns a UTC datetime string from nanoseconds since epoch. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. 

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_strUTC_from_strTZ() Method<a id="get_strUTC_from_strTZ-method"></a>
```py
  get_strUTC_from_strTZ(strTZ, time_string_format_TZ=None, time_string_format_UTC=None, second_hour=False)
```
Returns a UTC timezone datetime string from a target timezone datetime string. Use the optional time_string_format_UTC and time_string_format_TZ arguments to specify a format for converting the datetime strings. If omitted or None, the default format of the TimeHelper object is used. For an ambiguous case when switching back to normal time in autumn (times for one hour occurring twice), use True for second_hour to convert into datetime for the second occurrence.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>

#### get_strUTC_from_ts() Method<a id="get_strUTC_from_ts-method"></a>
```py
  get_strUTC_from_ts(ts, time_string_format=None)
```
Returns a UTC datetime string from a timestamp. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### The timestamp Methods<a id="timestamp-methods"></a>  

#### get_ts_from_dtTZ() Method<a id="get_ts_from_dtTZ-method"></a>
```py
  get_ts_from_dtTZ(dtTZ)
```
Returns a timestamp from a target timezone datetime.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_ts_from_dtUTC() Method<a id="get_ts_from_dtUTC-method"></a>
```py
  get_ts_from_dtUTC(dtUTC)
```
Returns a timestamp from a UTC datetime.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_ts_from_nsse() Method<a id="get_ts_from_nsse-method"></a>
```py
  get_ts_from_nsse(nsse)
```
Returns a timestamp from nanoseconds since epoch.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_ts_from_strTZ() Method<a id="get_ts_from_strTZ-method"></a>
```py
  get_ts_from_strTZ(strTZ, time_string_format=None, second_hour=False)
```
Returns a timestamp from a target timezone datetime string. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. For an ambiguous case when switching back to normal time in autumn (times for one hour occurring twice), use True for second_hour to convert into datetime for the second occurrence.

#### get_ts_from_strUTC() Method<a id="get_ts_from_strUTC-method"></a>
```py
  get_ts_from_strUTC(strUTC, time_string_format=None)
```
Returns a timestamp from a UTC datetime string. Use the optional time_string_format argument to specify a format for converting the datetime string. If omitted or None, the default format of the TimeHelper object is used. 

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### The ZoneInfo Methods<a id="zoneinfo-methods"></a>  

#### get_tz_zoneinfo() Method<a id="get_tz_zoneinfo-method"></a>
```py
  get_tz_zoneinfo()
```
Returns the ZoneInfo object for the target timezone.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_tz_zone_name() Method<a id="get_tz_zone_name-method"></a>
```py
  get_tz_zone_name()
```
Returns the name of the target timezone, e.g. ‘Europe/Berlin’.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_tz_zone_abbreviations() Method<a id="get_tz_zone_abbreviations-method"></a>
```py
  get_tz_zone_abbreviations()
```
Returns a tuple with abbreviations for the normal and daylight saving periods of the target timezone, e.g. ('CET', 'CEST').

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>


#### get_utc_zoneinfo() Method<a id="get_utc_zoneinfo-method"></a>
```py
  get_utc_zoneinfo()
```
Returns the ZoneInfo object for UTC.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>
</br>



## License
MIT license  
Copyright &copy; 2025 by krokoreit
