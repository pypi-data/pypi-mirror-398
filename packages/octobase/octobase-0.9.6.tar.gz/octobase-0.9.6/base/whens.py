#!/opt/local/bin/python

import base
import datetime
import math
import re
import weakref
import zoneinfo

from base.regexp import Group


base.Enum.Define(('SPECIALWHEN', 'SpecialWhens'), (
    ('star',                  'Dawn of Time',   'dawn',           'DAWN_OF_TIME'),
    ('calendar-minus',        'Yesterday',      'past',           'YESTERDAY'),
    ('calendar-day',          'Today',          'day',            'TODAY'),
    ('calendar-star',         'Now',            'now',            'NOW'),
    ('calendar-plus',         'Tomorrow',       'plus',           'TOMORROW'),
    ('hexagon',               'End of Days',    'dusk',           'END_OF_DAYS'),
))


base.Enum.Define(('DATERANGE', 'DateRanges'), (
    ('calendar-day',      'Yesterday',          'day0',           'YESTERDAY'),
    ('calendar-day',      'Today',              'day1',           'TODAY'),
    ('calendar-day',      'Tomorrow',           'day2',           'TOMORROW'),

    ('calendar-week',     'This Week',          'week0',          'THIS_WEEK'),
    ('calendar-week',     'Last Week',          'week1',          'LAST_WEEK'),
    ('calendar-week',     'Next Week',          'week2',          'NEXT_WEEK'),

    ('calendar',          'This Month',         'month0',         'THIS_MONTH'),
    ('calendar',          'Last Month',         'month1',         'LAST_MONTH'),
    ('calendar',          'Next Month',         'month2',         'NEXT_MONTH'),

    ('calendars',         'This Year',          'year0',          'THIS_YEAR'),
    ('calendars',         'Last Year',          'year1',          'LAST_YEAR'),
    ('calendars',         'Next Year',          'year2',          'NEXT_YEAR'),

    ('circle-calendar',   'All Time',           'all',            'ALL_TIME'),
))


class When(base.Thing):
  ''' a replacement for datetime, extensible for use with timelines that are not gregorian '''

  ATTRIBUTES        = [         # which of our attributes get copied
      'era', 'timezone', 'tzname', 'special',
      'year', 'month', 'day', 'weekday', 'hour', 'minute', 'second',
  ]

  era               = None      # Era subclass
  tzname            = None      # uppercase alphabetic code for the timezone
  timezone          = None      # zoneinfo instance

  special           = None      # SpecialWhens

  year              = None      # int
  month             = None      # int, subtract 1 to get an index into era.months
  day               = None      # int
  weekday           = None      # int, also an index into era.weekdays

  hour              = None      # int
  minute            = None      # int
  second            = None      # real

  @classmethod
  def Now(klass, fractional=True):
    ''' return a When initialized to now '''
    return base.CommonEra.MakeNow(fractional=fractional)

  @classmethod
  def From(klass, thing, era=None, **kwargs):
    ''' convert the thing -- string, datetime, or dict -- into a When '''
    if isinstance(thing, klass):
      return thing.Dupe()
    if not era and isinstance(thing, str):
      era           = klass.__GuessEra(thing)
    era             = era or base.CommonEra
    if isinstance(thing, str):
      if thing.startswith('/') and thing.endswith('/'):
        parts       = klass.__SortableParts(thing)
        if parts:
          return era.MakeWhenFromParts(**parts)
    try:
      return era.MakeWhen(thing, **kwargs)
    except base.errors.BadWhen:
      pass

  @classmethod
  def FromAndLocalize(klass, *args, default_timezone=None, **kwargs):
    ''' convenience method to attempt to localize at time of parse '''
    thing           = klass.From(*args, **kwargs)
    if thing and thing.time:
      thing.Localize(default=default_timezone)
    return thing

  @property
  def text(self):
    return self.era and self.era.WhenText(self) or ''

  @property
  def smol(self):
    return self.era and self.era.SmolText(self) or ''

  @property
  def long(self):
    return self.era and self.era.LongText(self) or ''

  @property
  def weekday_option(self):
    if self.era and self.weekday is not None:
      return self.era.weekdays[self.weekday]

  @property
  def weekday_name(self):
    if self.era and self.weekday is not None:
      return self.era.weekdays[self.weekday].name

  @property
  def month_option(self):
    if self.era and self.month:
      return self.era.months[self.month-1]

  @property
  def month_name(self):
    if self.era and self.month:
      return self.era.months[self.month-1].name

  @property
  def days_since_epoch(self):
    if self.era and self.year and self.month and self.day:
      return self.era.DaysSinceEpoch(self.year, self.month, self.day)

  @property
  def zero(self):
    ''' True if no meaningful field is filled in '''
    return bool(
        self.special  is None and
        self.year     is None and
        self.month    is None and
        self.day      is None and
        self.weekday  is None and
        self.hour     is None and
        self.minute   is None and
        self.second   is None)

  @property
  def cosmic(self):
    ''' True if we represent the start or end of time itself '''
    return self.special in (base.whens.SPECIALWHEN_DAWN_OF_TIME, base.whens.SPECIALWHEN_END_OF_DAYS)

  @property
  def datetime(self):
    ''' constructs a datetime.datetime out of our parts '''
    if self.special == base.whens.SPECIALWHEN_DAWN_OF_TIME:
      return base.consts.DATETIME_MIN
    if self.special == base.whens.SPECIALWHEN_END_OF_DAYS:
      return base.consts.DATETIME_MAX
    date, time      = self.date, self.time
    if date and time:
      return datetime.datetime.combine(date, time)

  @property
  def date(self):
    ''' constructs a datetime.date out of our date parts '''
    if self.special == base.whens.SPECIALWHEN_DAWN_OF_TIME:
      return base.consts.DATE_MIN
    if self.special == base.whens.SPECIALWHEN_END_OF_DAYS:
      return base.consts.DATE_MAX
    if self.year is None or self.month is None or self.day is None:
      return
    return datetime.date(year=self.year, month=self.month, day=self.day)

  @property
  def time(self):
    ''' constructs a datetime.time out of our time parts '''
    if self.hour is None or self.minute is None:
      return
    second          = math.floor(self.second or 0)
    usecond         = math.floor(((self.second or 0) - second) * 1000000)
    return datetime.time(
        hour=self.hour, minute=self.minute, second=second, microsecond=usecond, tzinfo=self.TimeZone())

  SORTABLE_ENCODING = {
      'era':          4,
      'year':         4,
      'month':        2,
      'day':          2,
      'hour':         2,
      'minute':       2,
      'second':       (2,9),
      'tzname':       4,
  }

  __SORTABLE_REGEXP1  = re.compile('/w:' + Group('[a-z]', name='special') + '/')
  __SORTABLE_REGEXP2  = re.compile(
      '^/w:' +
      Group('[a-z]', name='special') +
      '\.' +
      Group('[ ~\w]' * SORTABLE_ENCODING['era'], name='era') +
      '\.' +
      Group('[ ~\d]' * SORTABLE_ENCODING['year'], name='year') +
      '\.' +
      Group('[ ~\d]' * SORTABLE_ENCODING['month'], name='month') +
      '\.' +
      Group('[ ~\d]' * SORTABLE_ENCODING['day'], name='day') +
      '\.' +
      Group('[ ~\d]' * SORTABLE_ENCODING['hour'], name='hour') +
      '\.' +
      Group('[ ~\d]' * SORTABLE_ENCODING['minute'], name='minute') +
      '\.' +
      Group('[ ~\d]+\.?\d*', name='second') +
      '\.' +
      Group('[ ~\w]' * SORTABLE_ENCODING['tzname'], name='tzname') +
      '/$'
  )

  @property
  def sortable(self):
    ''' returns our data as a single string, that can be used to sort whens, yet may also be reconstituted
        back into a when.  intended as the storage format for use in DBs
    '''
    if self.special == base.whens.SPECIALWHEN_DAWN_OF_TIME:
      cosmic        = 'a'
    elif self.special == base.whens.SPECIALWHEN_END_OF_DAYS:
      cosmic        = 'z'
    else:
      cosmic        = 'n'

    era             = base.utils.PadString(self.era and self.era.tag or '', 3, '>')[:3]

    duped           = self
    if self.datetime and (self.tzname or self.timezone) and self.timezone != base.consts.TIME_UTC:
      duped         = self.Dupe()
      duped.Utc()

    if cosmic in ('a', 'z'):
      encoded       = cosmic
    else:
      encoded       = '.'.join([cosmic] + [self.__SortEncode(x, getattr(duped, x), y) for x,y in self.SORTABLE_ENCODING.items()])

    return '/w:' + encoded + '/'

  def ClearDate(self):
    self.year       = None
    self.month      = None
    self.day        = None
    self.weekday    = None
    return self

  def ClearTime(self):
    self.hour       = None
    self.minute     = None
    self.second     = None
    self.tzname     = None
    self.timezone   = None
    return self

  def TimeZone(self):
    ''' returns the zoneinfo instance that should manage our timezone '''
    if not self.timezone and self.tzname:
      timezone      = self.tzname
      if timezone.isalpha():
        timezone    = base.utils.ZoneInfoByTzName()[timezone.strip().upper()]
      try:
        timezone    = zoneinfo.ZoneInfo(timezone)
      except:
        pass
      if not isinstance(timezone, zoneinfo.ZoneInfo):
        raise base.errors.BadWhen('unable to make sense of the timezone', self.tzname)
      self.timezone = timezone
    return self.timezone

  def Shift(self, timezone, default=None):
    ''' in-place adjusts us to a new timezone; may specify a default timezone to come from if we don't have one '''
    if not timezone or self.timezone == timezone:
      return self
    dt              = self.datetime
    if not dt:
      raise base.errors.IncompleteWhen('may only When.Shift() with a complete date and time')
    if not dt.tzinfo and default:
      dt            = dt.replace(tzinfo=default)
    dt              = dt.astimezone(timezone)
    self.year       = dt.year
    self.month      = dt.month
    self.day        = dt.day
    self.hour       = dt.hour
    self.minute     = dt.minute
    self.timezone   = timezone
    self.tzname     = dt.tzname()
    self.weekday    = self.era.DayOfWeek(self.year, self.month, self.day)
    return self

  def Localize(self, default=None):
    ''' shortcut for shifting to local zone '''
    if self.time:
      return self.Shift(base.consts.TIME_ZONE, default=default)
    return self

  def Utc(self, default=None):
    ''' shortcut for shifting to UTC '''
    if self.time:
      return self.Shift(base.consts.TIME_UTC, default=default)
    return self

  def __init__(self, **kwargs):
    base.utils.SetAttrs(self, **kwargs)

  def __str__(self):
    return self.text or ''

  def __len__(self):
    return len(self.text or '')

  def __bool__(self):
    return not self.zero

  def __hash__(self):
    return hash(self.text)

  def __eq__(self, other):
    if isinstance(other, str):
      return self.text == other or self._EqEnough(self.text, other)
    if isinstance(other, When):
      return self.text == other.text or self._EqEnough(self.text, other.text)
    return False

  def _EqEnough(self, text1, text2):
    while text1.endswith(':00') or ':00 ' in text1:
      text1         = text1.replace(':00', '')
    while text2.endswith(':00') or ':00 ' in text2:
      text2         = text2.replace(':00', '')
    return text1 == text2

  def __lt__(self, other):
    if isinstance(other, str):
      other         = self.era.MakeWhen(other)
    return isinstance(other, When) and self.sortable < other.sortable

  def __le__(self, other):
    if isinstance(other, str):
      other         = self.era.MakeWhen(other)
    return isinstance(other, When) and self.sortable <= other.sortable

  def __gt__(self, other):
    if isinstance(other, str):
      other         = self.era.MakeWhen(other)
    return isinstance(other, When) and self.sortable > other.sortable

  def __ge__(self, other):
    if isinstance(other, str):
      other         = self.era.MakeWhen(other)
    return isinstance(other, When) and self.sortable >= other.sortable

  def __add__(self, other):
    if isinstance(other, str):
      other         = self.era.MakeWhen(other)

    if isinstance(other, When):
      if other.era != self.era:
        raise base.errors.EraMismatch(self, other)
      if (self.date and self.time) or (other.date and other.time) or not (self.date and self.time) or not (other.date and other.time):
        raise base.errors.AddingWhens(self, other)
      merged        = self.Dupe()
      merged.Copy(other)
      return merged

    if isinstance(other, datetime.timedelta):
      return self.era.AddTimeDelta(self, other)

    raise TypeError(other)

  def __radd__(self, other):
    return self.__add__(other)

  def __iadd__(self, other):
    added           = self + other
    self.Copy(added)
    return self

  def __sub__(self, other):
    if isinstance(other, When):
      if other.era != self.era:
        raise base.errors.EraMismatch(self, other)
      return self.era.Subtract(self, other)
    if not isinstance(other, datetime.timedelta):
      raise TypeError(other)
    return self.era.AddTimeDelta(self, -other)

  def __isub__(self, other):
    added           = self - other
    self.Copy(added)
    return self

  __never_guess_again = False
  @classmethod
  def __GuessEra(klass, s):
    if not s or klass.__never_guess_again:
      return base.CommonEra

    eras            = base.registry.GetAll(Era)
    assert(base.CommonEra in eras)
    if len(eras) == 1:
      klass.__never_guess_again = True
      return base.CommonEra

    tags            = {x.tag: x for x in eras}
    for tag, era in tags.items():
      found         = re.search(f'(^|[- ,:\.~]){tag}([- ,:\.~]|$)', s, re.IGNORECASE)
      if found:
        return era

    tags            = {x.name: x for x in eras}
    for tag, era in tags.items():
      found         = re.search(f'(^|[- ,:\.~]){tag}([- ,:\.~]|$)', s, re.IGNORECASE)
      if found:
        return era

  @classmethod
  def __SortableParts(klass, s):
    def Klean(d):
      for x, y in d.items():
        y           = y.replace('~', '').strip()
        if y and y[0].isdigit():
          if '.' in y:
            y       = float(y)
          else:
            y       = int(y)
        elif not y:
          y         = None

        if x == 'era':
          tags      = {x.tag: x for x in base.registry.GetAll(Era)}
          for tag, era in tags.items():
            if tag.upper() == y.upper():
              y     = era
              break

        if x == 'special':
          if y == 'a':
            y       = SPECIALWHEN_DAWN_OF_TIME
          elif y == 'z':
            y       = SPECIALWHEN_END_OF_DAYS
          else:
            y       = None

        d[x]        = y
      return d

    found           = klass.__SORTABLE_REGEXP1.match(s)
    if found:
      return Klean(found.groupdict())
    found           = klass.__SORTABLE_REGEXP2.match(s)
    if found:
      return Klean(found.groupdict())

  @classmethod
  def __SortEncode(klass, attr, value, radix):
    if isinstance(radix, tuple):
      p0, p1        = radix
      if value is None:
        return ' ' * p1
      return f'{value: >{p0}.{p1}f}'[:p1]
    if value is None:
      return ' ' * radix
    if base.utils.IsA(value, Era):
      return f'{value.tag: >{radix}}'[:radix]
    return f'{value: >{radix}}'[:radix]



###
## Era
#

class Era(base.Thing, metaclass=base.registry.AutoRegister, skip=1):
  ''' abstract timeline for parsing and formatting Whens.
      Eras are always used in class form, never instantiated.
      see CommonEra for a concrete implementation
  '''

  tag               = None    # smolname of this timeline
  name              = None    # fullname of this timeline
  icon              = None    # symbol
  aliases           = None    # list of alternate tags

  backwards         = False   # do years run backwards?

  months            = None    # Enum
  weekdays          = None    # Enum

  WhenType          = None    # When or subclass

  @classmethod
  def MakeNow(klass, fractional=True):
    ''' return a When initialized to now '''

  @classmethod
  def MakeWhen(klass, thing, now=None, timezone=None):
    ''' convert the thing -- string, datetime, or dict -- into a When '''

  @classmethod
  def MakeWhenFromParts(klass, **d):
    ''' convert the dict of attributes into a functioning When '''

  @classmethod
  def WhenText(klass, when):
    ''' format a When back into a string '''

  @classmethod
  def SmolText(klass, when):
    ''' format a When into as tight and compact a format as possible '''

  @classmethod
  def LongText(klass, when):
    ''' format a When into as long and flowery a format as possible '''

  @classmethod
  def AddTimeDelta(klass, when, delta):
    ''' combine the when and the time offset '''

  @classmethod
  def Subtract(klass, when0, when1):
    ''' finds the difference between when0 - when1; CommonEra returns a timedelta '''

  @classmethod
  def DaysInYear(klass, year):
    ''' return an integer for the number of days in the given year '''

  @classmethod
  def DaysInMonth(klass, year, month):
    ''' return an integer for the number of days in the given month '''

  @classmethod
  def DaysInWeek(klass, year, month, day):
    ''' return an integer for the number of days in the week of the given day '''
    return len(klass.weekdays)

  @classmethod
  def DayOfWeek(klass, year, month, day):
    ''' return a integer from range(0, len(weekdays)) for what day of the week is the day given '''

  @classmethod
  def DaysNotInWeek(klass, year):
    ''' return a list of days in the given year that exist but are part of no week '''

  @classmethod
  def DateRangeFromWhens(klass, date0, date1):
    ''' attempts to match the given dates passed in with one of our DATERANGE enum options '''
    for kdr in base.whens.DateRanges:
      isit0, isit1  = klass.WhensFromDateRange(kdr)
      if isit0 == date0 and isit1 == date1:
        return kdr

  @classmethod
  def WhensFromDateRange(klass, daterange, today=None):
    ''' returns a pair of date-only Whens for the DATERANGE (or SPECIALWHEN) enum option given '''
    kdr             = daterange in base.whens.DateRanges and base.whens.DateRanges(daterange) or None
    ksw             = daterange in base.whens.SpecialWhens and base.whens.SpecialWhens(daterange) or None
    if not kdr and not ksw:
      return

    if ksw in (base.whens.SPECIALWHEN_DAWN_OF_TIME, base.whens.SPECIALWHEN_END_OF_DAYS):
      return base.When(era=self.era, special=ksw)
    if kdr == base.whens.DATERANGE_ALL_TIME:
      return (
          base.When(era=klass, special=base.whens.SPECIALWHEN_DAWN_OF_TIME),
          base.When(era=klass, special=base.whens.SPECIALWHEN_END_OF_DAYS),
      )

    today           = today and today.Dupe() or klass.MakeNow()
    today.Localize()
    today.ClearTime()

    oneday          = datetime.timedelta(days=1)
    dx, d0, d1      = None, None, None

    if kdr == base.whens.DATERANGE_YESTERDAY or ksw == base.whens.SPECIALWHEN_YESTERDAY:
      dx            = today - oneday
    elif kdr == base.whens.DATERANGE_TODAY or ksw == base.whens.SPECIALWHEN_TODAY or ksw == base.whens.SPECIALWHEN_NOW:
      dx            = today
    elif kdr == base.whens.DATERANGE_TOMORROW or ksw == base.whens.SPECIALWHEN_TOMORROW:
      dx            = today + oneday

    elif kdr in (base.whens.DATERANGE_LAST_WEEK, base.whens.DATERANGE_THIS_WEEK, base.whens.DATERANGE_NEXT_WEEK):
      d0            = today

      if kdr == base.whens.DATERANGE_LAST_WEEK:
        d0          -= datetime.timedelta(days=d0.weekday + 1)
      elif kdr == base.whens.DATERANGE_NEXT_WEEK:
        d0          += datetime.timedelta(days=len(klass.weekdays) - d0.weekday)

      if d0.weekday:
        d0          -= datetime.timedelta(days=d0.weekday)

      d1            = d0 + datetime.timedelta(days=len(klass.weekdays)) - oneday

    elif kdr in (base.whens.DATERANGE_LAST_MONTH, base.whens.DATERANGE_THIS_MONTH, base.whens.DATERANGE_NEXT_MONTH):
      d0            = today

      if kdr == base.whens.DATERANGE_LAST_MONTH:
        d0          -= datetime.timedelta(days=d0.day)
      elif kdr == base.whens.DATERANGE_NEXT_MONTH:
        d0          += datetime.timedelta(days=klass.DaysInMonth(d0.year, d0.month) - d0.day + 1)

      if d0.day > 1:
        d0          -= datetime.timedelta(days=d0.day - 1)

      d1            = d0 + datetime.timedelta(days=klass.DaysInMonth(d0.year, d0.month)) - oneday

    elif kdr in (base.whens.DATERANGE_LAST_YEAR, base.whens.DATERANGE_THIS_YEAR, base.whens.DATERANGE_NEXT_YEAR):
      d0            = today
      d0.month      = 1
      d0.day        = 1

      if kdr == base.whens.DATERANGE_LAST_YEAR:
        d0.year     -= 1
      elif kdr == base.whens.DATERANGE_NEXT_YEAR:
        d0.year     += 1

      d1            = d0.Dupe()
      d1.year       += 1
      d1            -= oneday

    d0              = d0 or dx
    d1              = d1 or dx

    if d0 and d1:
      return d0, d1
