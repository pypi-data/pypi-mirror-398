"""Time management and timezone handling module for building energy analysis.

.. module:: batem.core.timemg

This module provides comprehensive tools for time management, timezone handling,
and time series processing in building energy analysis systems. It includes
time conversion utilities, timezone management, date/time formatting, and
time series aggregation and merging capabilities.

Classes
-------

.. autosummary::
   :toctree: generated/

   TimeSeriesMerger

Functions
---------

.. autosummary::
   :toctree: generated/

   stringdate_to_epochtimems
   epochtimems_to_stringdate
   epochtimems_to_datetime
   datetime_to_stringdate
   local_timezone
   TimezoneFinder

Key Features
------------

* Timezone detection and conversion using geographic coordinates
* Epoch time conversion to/from datetime and string formats
* Time series aggregation with multiple processing methods (average, sum, min, max)
* Daily data aggregation with configurable processing algorithms
* Open-Meteo API date format compatibility and conversion
* Local timezone detection and management
* Time quantum calculations for time series analysis
* Date arithmetic and time delta operations
* Integration with building energy data providers and measurement systems
* Support for various date/time formats and timezone standards

The module is designed for building energy analysis, time series processing,
and comprehensive time management in research and practice.

.. note::
    This module requires pytz and tzlocal for timezone handling.

:Author: stephane.ploix@g-scop.grenoble-inp.fr
:License: GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import datetime
import time
import pytz
from zoneinfo import ZoneInfo
from tzlocal import get_localzone_name
from statistics import mean
from tzlocal import get_localzone
from timezonefinder import TimezoneFinder
from collections.abc import Sequence


REGULAR_DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'
REGULAR_DATE_FORMAT = '%d/%m/%Y'


def issequence(x):
    return isinstance(x, Sequence) and not isinstance(x, (str, bytes))


def get_timezone_str(site_latitude_north_deg: float, site_longitude_east_deg: float) -> str:
    timezone_finder = TimezoneFinder()
    timezone_str = timezone_finder.timezone_at(lat=site_latitude_north_deg, lng=site_longitude_east_deg)
    if timezone_str is None:
        return local_timezone()
    return timezone_str


def local_timezone() -> str:
    return get_localzone_name()


def set_timezone(any_datetimes, timezone_str: str, date_format=REGULAR_DATETIME_FORMAT) -> list[datetime.datetime] | datetime.datetime | str | list[str] | list[int] | int:
    if timezone_str is None:
        timezone_str = local_timezone()
    singleton: bool = not issequence(any_datetimes)
    if singleton:
        any_datetimes = [any_datetimes]
    if isinstance(any_datetimes[0], float):
        any_datetimes = [epochtimems_to_datetime(dt, timezone_str) for dt in any_datetimes]
        any_datetimes = [datetime_to_epochtimems(dt) for dt in any_datetimes]
    elif isinstance(any_datetimes[0], str):
        any_datetimes = [stringdate_to_datetime(dt, date_format=date_format, timezone_str=timezone_str) for dt in any_datetimes]
        any_datetimes = [datetime_to_stringdate(dt, date_format) for dt in any_datetimes]
    else:
        any_datetimes = [dt.astimezone(ZoneInfo(timezone_str)) for dt in any_datetimes]
    if not singleton:
        return any_datetimes
    else:
        return any_datetimes[0]


def to_timezone(datetimes: list[datetime.datetime] | datetime.datetime, target_timezone: str, initial_timezone: str = None) -> list[datetime.datetime] | datetime.datetime:
    singleton: bool = isinstance(datetimes, datetime.datetime)
    if singleton:
        datetimes = [datetimes]
    if initial_timezone is None:
        initial_timezone = local_timezone()
    datetimes = [dt.replace(tzinfo=ZoneInfo(initial_timezone)) for dt in datetimes]
    datetimes = [dt.astimezone(ZoneInfo(target_timezone)) for dt in datetimes]
    if not singleton:
        return datetimes
    else:
        return datetimes[0]


def epochtimems_to_stringdate(epochtimems, date_format=REGULAR_DATETIME_FORMAT, timezone_str: str = None) -> str:
    if timezone_str is None:
        timezone_str = str(get_localzone())
    dt = datetime.datetime.fromtimestamp(epochtimems // 1000)
    localized_dt = pytz.timezone(timezone_str).localize(dt, is_dst=True)
    return localized_dt.strftime(date_format)


def epochtimems_to_datetime(epochtimems, timezone_str: str = None) -> datetime.datetime:
    if timezone_str is None:
        timezone_str = str(get_localzone())
    dt = datetime.datetime.fromtimestamp(epochtimems // 1000)
    localized_dt = pytz.timezone(timezone_str).localize(dt, is_dst=True)
    return localized_dt


def date_to_epochtimems(a_date: datetime) -> int:
    return datetime_to_epochtimems(a_date)


def datetime_to_epochtimems(a_datetime) -> int:
    if type(a_datetime) is datetime.date:
        a_datetime: datetime.datetime = datetime.datetime.combine(
            a_datetime, datetime.time(0))
    return a_datetime.timestamp() * 1000


def stringdate_to_epochtimems(stringdatetime, date_format=REGULAR_DATETIME_FORMAT, timezone_str: str = None) -> int:
    if timezone_str is None:
        timezone_str = str(get_localzone())
    dt = datetime.datetime.strptime(stringdatetime, date_format)
    localized_dt = pytz.timezone(timezone_str).localize(
        dt, is_dst=True)  # Changed is_dst to None for automatic detection
    return int(localized_dt.timestamp() * 1000)
    if timezone_str is None:
        timezone_str = str(get_localzone())
    dt = datetime.strptime(stringdatetime, date_format)
    localized_dt: datetime.datetime = pytz.timezone(
        timezone_str).localize(dt, is_dst=True)
    return int(localized_dt.timestamp() * 1000)


def stringdate_to_openmeteo_date(stringdate: str, timezone_str: str = None) -> str:
    if timezone_str is None:
        timezone_str = str(get_localzone())
    a_struct_time: datetime.struct_time = time.strptime(stringdate, '%d/%m/%Y')
    a_datetime = datetime.datetime(
        *a_struct_time[:6], tzinfo=pytz.timezone(timezone_str))
    return a_datetime.strftime('%Y-%m-%d')


def openmeteo_to_stringdate(openmeteo_stringdate: str) -> str:
    year, month, day = openmeteo_stringdate.split('-')
    return day + '/' + month + '/' + year


def openmeteo_to_stringdatetime(openmeteo_date: str) -> str:
    a_date, a_time = openmeteo_date.split('T')
    year, month, day = a_date.split('-')
    hour, minute = a_time.split(':')
    return day + '/' + month + '/' + year + ' ' + hour + ':' + minute + ':00'


def datetime_to_stringdate(a_datetime: datetime, date_format: str = REGULAR_DATETIME_FORMAT) -> str:
    return a_datetime.strftime(date_format)


def stringdate_to_datetime(stringdatetime, date_format=REGULAR_DATETIME_FORMAT, timezone_str: str = None) -> datetime:
    if timezone_str is None:
        timezone_str = str(get_localzone())
    dt = datetime.datetime.strptime(stringdatetime, date_format)
    localized_dt: datetime.datetime = pytz.timezone(
        timezone_str).localize(dt, is_dst=True)
    return localized_dt


def stringdate_to_date(stringdate: str, date_format='%d/%m/%Y', timezone_str: str = None) -> datetime:
    if timezone_str is None:
        timezone_str = str(get_localzone())
    dt = datetime.datetime.strptime(stringdate, date_format)
    localized_dt: datetime.datetime = pytz.timezone(
        timezone_str).localize(dt, is_dst=True)
    return localized_dt.date()


def date_to_stringdate(a_date: datetime.date, date_format='%d/%m/%Y') -> str:
    a_datetime = datetime.datetime.combine(a_date, datetime.time(0))
    # a_datetime.replace(tzinfo=pytz.timezone(tz) if tz is not None else None)
    return a_datetime.strftime(date_format)


def epochtimems_to_timequantum(epochtimems, timequantum_duration_in_secondes) -> int:
    return (epochtimems // (timequantum_duration_in_secondes * 1000)) * timequantum_duration_in_secondes * 1000


def datetime_with_day_delta(a_datetime: datetime.datetime, number_of_days: int = 0, date_format: str = REGULAR_DATETIME_FORMAT) -> str:
    return (a_datetime + datetime.timedelta(days=number_of_days)).strftime(date_format)


def current_stringdate(date_format=REGULAR_DATETIME_FORMAT) -> str:
    return time.strftime(date_format, time.localtime())


def current_epochtimems() -> int:
    return int(time.mktime(time.localtime()) * 1000)


def time_from_seconds_day_hours_minutes(duration_in_seconds: int) -> str:
    d = duration_in_seconds // (24 * 3600)
    h = (duration_in_seconds - 24 * d * 3600) // 3600
    m = (duration_in_seconds - 24 * d * 3600 - h * 3600) // 60
    s = (duration_in_seconds - 24 * d * 3600 - h * 3600 - m * 60) % 60

    return '%i days, %i hours, %i min, %i sec' % (d, h, m, s)


def dayify(datetime_data: list[float], datetimes: list[datetime.datetime], processing: str = 'average') -> tuple[list[float], list[datetime.date]]:
    dates = list()
    daily_data = list()
    buffer = list()
    current_date = datetimes[0].date()
    for i, dt in enumerate(datetimes):
        if dt.date() != current_date or (i+1 == len(datetimes) and len(buffer) > 0):
            if processing in ('average', 'avg', 'mean'):
                if len(buffer) == 0:
                    daily_data.append(0)
                else:
                    daily_data.append(mean(buffer))
            elif processing in ('summation', 'sum'):
                daily_data.append(sum(buffer))
            elif processing in ('max', 'maximize'):
                daily_data.append(max(buffer))
            elif processing in ('min', 'minimize'):
                daily_data.append(min(buffer))
            elif processing == 'avgifpos':
                size = 0
                for v in buffer:
                    if v > 0:
                        size += 1
                if size > 0:
                    daily_data.append(sum(buffer)/size)
                else:
                    daily_data.append(0)
            elif processing == 'maximum':
                daily_data.append(max(buffer))
            else:
                raise ValueError('Unknown processing')
            dates.append(current_date)
            buffer = [datetime_data[i]]
            current_date = datetimes[i].date()
        else:
            buffer.append(datetime_data[i])
    return daily_data, dates


class TimeSeriesMerger:
    """Time series aggregation and merging class for building energy analysis.

    This class provides functionality for aggregating and merging time series data
    based on different time groupings (hour, day, week, month, year) with various
    processing methods including average, sum, minimum, and maximum calculations.
    """

    def __init__(self, datetimes: list[datetime.date] | list[datetime.datetime], values: list[float], group_by: str):

        self._datetimes: list[datetime.date] | list[datetime.datetime] = datetimes
        self.values: list[float] = values
        self.indices: list[tuple[int, int]] = [0]
        self.group_by = group_by
        if group_by != 'hour':
            sequence_types: dict[str, str] = {
                'day': '%d', 'week': '%V', 'month': '%m', 'year': '%Y'}
            sequence_type: str = sequence_types[group_by]

            sequence_id: list[int] = datetimes[0].strftime(sequence_type)
            for i in range(1, len(datetimes)):
                next_sequence_id = datetimes[i].strftime(sequence_type)
                if next_sequence_id != sequence_id:
                    self.indices.append(i)
                    sequence_id = next_sequence_id
            if self.indices[-1] != len(self._datetimes) - 1:
                self.indices.append(len(self._datetimes))

    def __call__(self, merge_function: str = 'avg') -> list[float]:
        if self.group_by == 'hour':
            return self.values
        # Handle '-' as 'no merging' - return raw values
        if merge_function == '-':
            return self.values
        merge_functions: dict[str, str] = {
            'avg': mean, 'mean': mean, 'min': min, 'max': max, 'sum': sum}
        merged_values = list()
        for k in range(1, len(self.indices)):
            group_value: float = merge_functions[merge_function](
                [self.values[i] if self.values[i] is not None else 0 for i in range(self.indices[k-1], self.indices[k])])
            for i in range(self.indices[k] - self.indices[k-1]):
                merged_values.append(group_value)
        return merged_values


# dt = [datetime_to_epochtimems(datetime.datetime.now()), datetime_to_epochtimems(datetime.datetime.now())]
# dt = [datetime_to_stringdate(datetime.datetime.now()), datetime_to_stringdate(datetime.datetime.now())]
# print(dt)
# print(set_timezone(dt, 'Australia/Melbourne'))
