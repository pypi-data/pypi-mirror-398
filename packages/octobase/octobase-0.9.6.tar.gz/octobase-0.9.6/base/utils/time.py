#!/opt/local/bin/python
''' Functions for working with datetimes and timedeltas. '''

import base
import datetime
import math
import os
import re

from .environment import DeferImport
from .metaclasses import Singleton
from importlib    import resources

DeferImport('tzdata')
DeferImport('zoneinfo')


def ParseTimestamp(text, allow_date=False, force_datetime=True):
  ''' returns a datetime if one can be extracted from the given text '''
  when            = text and base.When.From(text)
  if when and when.datetime:
    return when.datetime
  if when and when.date:
    if force_datetime:
      return base.utils.DateTimeFromDate(when.date)
    if allow_date:
      return when.date


def Now():
  ''' Timezone-aware now() '''
  return datetime.datetime.now(base.consts.TIME_UTC)


def LocalTime(dt):
  ''' Converts a datetime to our default timezone. '''
  return dt.astimezone(base.consts.TIME_ZONE)


def EnsureTzInfo(dt, timezone=None):
  ''' Stamps "UTC" on a datetime since we don't know anything better. '''
  if dt.tzinfo:
    return dt
  timezone        = timezone or base.consts.TIME_UTC
  return dt.replace(tzinfo=timezone)


def DateFromDateTime(timestamp):
  ''' Shifts a timestamp to local time, then strips the time part and returns the date. '''
  return LocalTime(timestamp).date()


def DateTimeFromDate(date):
  ''' Promotes a date object into a datetime object by setting the time to high-noon, local time. '''
  timestamp       = datetime.datetime.combine(date, datetime.time(12, 00))
  return EnsureTzInfo(timestamp, timezone=base.consts.TIME_ZONE)


def FormatTimestamp(dt, force_utc=False, force_local=True, limit_granularity=None):
  ''' Returns a nice string representation of the date, time, or datetime. '''
  if not dt:
    return ''

  if type(dt) == datetime.time:
    if limit_granularity == 'minute':
      return dt.strftime('%H:%M %Z')
    return dt.strftime('%H:%M:%S %Z')

  if type(dt) == datetime.date:   # don't use isinstance() because datetime is a date
    if dt <= base.consts.DATE_MIN:
      return 'Dawn of Time'
    if dt >= base.consts.DATE_MAX:
      return 'End of Time'
    return dt.strftime('%Y-%m-%d')

  if dt.tzinfo:
    if dt <= base.consts.DATETIME_MIN:
      return 'Dawn of Time'
    if dt >= base.consts.DATETIME_MAX:
      return 'End of Time'
  else:
    if dt <= datetime.datetime.min:
      return 'Dawn of Time'
    if dt >= datetime.datetime.max:
      return 'End of Time'

  if force_utc:
    dt            = dt.astimezone(base.consts.TIME_UTC)
  elif force_local:
    dt            = dt.astimezone(base.consts.TIME_ZONE)

  if limit_granularity == 'date':
    return dt.strftime('%Y-%m-%d')
  if limit_granularity == 'minute':
    return dt.strftime('%Y-%m-%d %H:%M %Z')
  return dt.strftime('%Y-%m-%d %H:%M:%S %Z')


def FormatTimeDelta(td, fractional=True):
  ''' Returns a human-readable string for a datetime.timedelta. '''
  Plural          = lambda x: x != 1 and 's' or ''

  if not td:
    return ''

  frac, seconds   = math.modf(td.total_seconds())
  seconds         = int(seconds)

  minutes         = int(math.floor(seconds / 60))
  seconds         -= minutes * 60

  hours           = int(math.floor(minutes / 60))
  minutes         -= hours * 60

  days            = int(math.floor(hours / 24))
  hours           -= days * 24

  years           = int(math.floor(days / 365))
  days            -= years * 365

  if frac and fractional:
    sfrac         = '.{:03}'.format(int(math.floor(frac * 1000)))
  else:
    sfrac         = ''

  parts           = []
  if years:
    parts.append('{} year{}'.format(years, Plural(years)))
  if days:
    parts.append('{} day{}'.format(days, Plural(days)))
  if hours or minutes or seconds or sfrac:
    if parts:
      parts.append('{}:{:02}:{:02}{}'.format(hours, minutes, seconds, sfrac))
    else:
      if hours:
        parts.append('{} hour{}'.format(hours, Plural(hours)))
      if minutes:
        parts.append('{} minute{}'.format(minutes, Plural(minutes)))
      if seconds or sfrac:
        if parts:
          parts.append('{} second{}'.format(seconds, Plural(seconds)))
        else:
          parts.append('{}{} second{}'.format(seconds, sfrac, Plural(seconds + frac)))

  if parts:
    return ', '.join(parts)

  return '0'



class Stopwatch:
  ''' STDERR-logging timer for use in figuring out where your code is slow. '''

  def __init__(self, name='STOPWATCH', start=None):
    self.name       = base.utils.Slugify(name).upper()
    self.laps       = [start or base.utils.Now()]
    self.lapnames   = []

  def Base(self):
    return self.laps[0]

  def Read(self):
    return base.utils.Now() - self.laps[-1]

  def Total(self):
    return base.utils.Now() - self.laps[0]

  def Lap(self, lapname=None, keep_history=True):
    now             = base.utils.Now()
    prior           = self.laps[-1]
    if keep_history:
      self.laps.append(now)
      self.lapnames.append(lapname)
    else:
      self.laps     = [now]
    return now - prior

  def Log(self):
    base.utils.Log(self.name, str(self.Read()))

  def LapAndLog(self, lapname='Lap'):
    base.utils.Log(self.name, '{!s} {!s}'.format(self.Lap(), lapname))

  def LogAllLaps(self):
    base.utils.Log(self.name, 'Lap times:\n  ' + '\n  '.join(self.FormatLaps()) + '\n')

  def FormatLaps(self):
    times           = []
    for i in range(1, len(self.laps)):
      times.append((self.laps[i] - self.laps[i-1], self.lapnames[i-1] or ''))
    return ['{!s} {!s}'.format(x, y) for x, y in times]



class ZoneInfoByTzName(metaclass=Singleton):
  ''' there is *no* standardized way, nor even a good non-standardized way, of mapping
      timezone names back into the timezone zoneinfos that they came from.  all we have
      is a truly terrible way:  scan all 600-ish zoneinfo files installed in the system,
      tease summer and winter timezone names out of them, and build our own dictionary
      of about 50-ish items
  '''

  def get(self, key):
    if isinstance(key, str):
      return self.data.get(key.upper())

  def __getitem__(self, key):
    return self.data[(key or '').upper()]

  def __init__(self):

    summer          = datetime.datetime(2023,  6, 20, 12, 34, 56)
    winter          = datetime.datetime(2023, 12, 20, 12, 34, 56)

    results         = {}
    for iana in self._ListIANAs():
        try:
          zone      = zoneinfo.ZoneInfo(iana)
        except:
          continue

        localsummer = summer.replace(tzinfo=zone)
        tzname      = localsummer.tzname()
        if tzname and tzname.isalpha():
          results.setdefault(tzname.upper(), []).append(iana)

        localwinter = winter.replace(tzinfo=zone)
        tzname      = localwinter.tzname()
        if tzname and tzname.isalpha():
          results.setdefault(tzname.upper(), []).append(iana)

    self.data       = {x : self._Collapse(y) for x,y in results.items()}

  def _ListIANAs(self):
    if not tzdata:
      return self._ListIANAsFromFiles()
    with resources.open_text('tzdata', 'zones') as fp:
      return [x.strip() for x in fp.readlines()]

  def _ListIANAsFromFiles(self):
    basepath        = '/usr/share/zoneinfo'
    if not os.path.isdir(basepath):
      raise base.errors.TzDataNotAvail(basepath)
    for dirpath, dirnames, filenames in os.walk(basepath):
      relpath       = dirpath[len(basepath):].strip('/') + '/'
      if relpath.startswith('right/'):
        continue
      for filename in filenames:
        yield os.path.join(relpath, filename)

  @staticmethod
  def _Collapse(l):
    for x in l:
      if x.startswith('posix/'):
        return x
      if x.startswith('US/'):
        return x
    counts          = {x: l.count(x) for x in set(l)}
    maxcount        = max(counts.values())
    lengths         = {x: len(x) for x,y in counts.items() if y == maxcount}
    minlen          = min(lengths.values())
    bests           = [x for x,y in lengths.items() if y == minlen]
    bests.sort()
    return bests[0]
