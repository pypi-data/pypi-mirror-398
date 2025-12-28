#!/opt/local/bin/python

import base
import calendar
import datetime
import math
import random
import re
import zoneinfo

from base.regexp              import *


base.Enum.Define(('MONTH', 'Months'), (
    ('January',       'jan'),
    ('February',      'feb'),
    ('March',         'mar'),
    ('April',         'apr'),
    ('May',           'may'),
    ('June',          'jun'),
    ('July',          'jul'),
    ('August',        'aug'),
    ('September',     'sep'),
    ('October',       'oct'),
    ('November',      'nov'),
    ('December',      'dec'),
))


base.Enum.Define(('WEEKDAY', 'Weekdays'), (
    ('Sunday',        'sun'),
    ('Monday',        'mon'),
    ('Tuesday',       'tue'),
    ('Wednesday',     'wed'),
    ('Thursday',      'thu'),
    ('Friday',        'fri'),
    ('Saturday',      'sat'),
))



###
## CommonCompletionist
#


class TzInfoByOffset(datetime.tzinfo):
  ''' simple implementation of tzinfo for when we know the numeric offset but not the timezone name '''

  def __init__(self, plusminus, hours, minutes):
    self.plusminus  = plusminus
    self.hours      = hours
    self.minutes    = minutes

  def utcoffset(self, dt):
    td              = datetime.timedelta(hours=self.hours, minutes=self.minutes)
    return self.plusminus < 0 and -td or td

  def dst(self, dt):
    pass

  def tzname(self, dt=None):
    hours         = self.plusminus < 0 and -self.hours or self.hours
    return '{:+03d}:{:02d}'.format(hours, self.minutes)

  def __str__(self):
    return self.tzname()

  def __repr__(self):
    return base.utils.ClassName(self) + '(' + self.tzname() + ')'


class CommonCompletionist:
  ''' logic that knows how to validate a When and fill in gaps '''

  def __init__(self, era):
    self.era        = era

  def Complete(self, when):
    ''' cleans and validates the when.  raises on error '''
    if not when:
      return

    # cosmic whens should have no other details filled in
    if when.cosmic:
      filled        = self._GetNotNone(when,
          'year', 'month', 'day', 'hour', 'minute', 'second', 'weekday')
      if filled:
        raise base.errors.BadWhen('cosmic Whens should not have any other attributes set', filled)

    # clean up our month
    self._CleanEnum(when, 'month', addone=True)

    # validate our numbers
    for attr in ('year', 'day', 'hour', 'minute', 'second'):
      self._CleanNumber(when, attr)

    # weekday can now be calculated
    if self._HasAll(when, 'year', 'month', 'day'):
      when.weekday  = self.era.DayOfWeek(when.year, when.month, when.day)

    # timezone should only be set if we have a time
    self._CleanTimezone(when)

    # we now own this when
    when.era        = self.era
    return when

  def _CleanTimezone(self, when):
    ''' in-place sanitizes our timezone '''
    if not self._HasAll(when, 'hour', 'minute'):
      when.timezone = None
      when.tzname   = None
      return
    if not when.tzname:
      return
    if when.tzname.isalpha():
      if when.tzname in ('z', 'Z'):
        when.timezone = base.consts.TIME_UTC
        when.tzname = 'UTC'
      else:
        when.tzname = when.tzname.strip().upper()
      return
    if when.timezone:
      return

    offset          = re.match('([-+])(\d\d?):?(\d\d)?', when.tzname)
    if not offset:
      raise base.errors.BadWhen('When.tzname could not be understood', when.tzname)
    plusminus, hours, minutes = offset.groups()
    try:
      plusminus     = plusminus == '+' and 1 or -1
      hours         = int(hours)
      minutes       = int(minutes or 0)
    except:
      raise base.errors.BadWhen('When.tzname could not be understood', when.tzname)
    when.timezone   = TzInfoByOffset(plusminus, hours, minutes)

  def _CleanEnum(self, when, attr, addone):
    ''' in-place sanitizes one of the enum attributes on our self '''
    value           = getattr(when, attr)
    enum            = getattr(self.era, attr+'s')
    if addone:
      minv, maxv    = 1, len(enum) + 1
    else:
      minv, maxv    = 0, len(enum)
    if value is not None:
      if isinstance(value, base.Option):
        if value.enum != enum:
          raise base.errors.BadWhen('When.' + attr + ' value is not in the correct enum', value, enum)
        value       = value.index
        if addone:
          value     += 1
        setattr(when, attr, value)
      elif isinstance(value, str):
        if value.isdigit():
          try:
            value   = int(value)
          except:
            raise base.errors.BadWhen('When.' + attr + ' could not be cast to an int', value)
        elif value in enum:
          value     = enum(value).index + (addone and 1 or 0)
        else:
          raise base.errors.BadWhen('When.' + attr + ' value is not in the enum', value, enum)
        setattr(when, attr, value)
      elif not isinstance(value, int):
        raise base.errors.BadWhen('When.' + attr + ' is not an int', value)
      if value < minv or value >= maxv:
        raise base.errors.BadWhen('When.' + attr + ' is not in the valid range', value)

  def _CleanNumber(self, when, attr):
    ''' in-place sanitizes one of the numeric attributes on our self '''
    value           = getattr(when, attr)
    if value is None:
      return

    cast            = self._CastToNumber(value, attr, attr == 'second')
    if cast != value:
      setattr(when, attr, cast)
      value         = cast

    if value < 0:
      raise base.errors.BadWhen('When.' + attr + ' may not be less than 0', value)
    if attr == 'day' and when.year is not None and when.month is not None:
      maxday        = self.era.DaysInMonth(when.year, when.month)
      if value < 1 or value > maxday:
        raise base.errors.BadWhen('that month only has {} days'.format(maxday), value)
    if attr == 'hour' and (value < 0 or value >= 24):
      raise base.errors.BadWhen('When.' + attr + ' must be within 0 and 23', value)
    if attr in ('minute', 'second') and (value < 0 or value >= 60):
      raise base.errors.BadWhen('When.' + attr + ' must be within 0 and 59', value)

  def _CastToNumber(self, x, attr, allow_float):
    ''' returns x, having cast x to either an int or a float if allowed and needed '''
    if isinstance(x, str):
      x           = x.strip().strip('.:')
    if isinstance(x, int) or (allow_float and isinstance(x, float)):
      return x
    try:
      return int(x)
    except:
      if allow_float:
        try:
          return float(x)
        except:
          raise base.errors.BadWhen('When.' + attr + ' could not be cast to a number', x)
      else:
        raise base.errors.BadWhen('When.' + attr + ' could not be cast to an int', x)

  def _HasAll(self, when, *attrs):
    ''' returns True if all of the named attributes have values '''
    return len(self._GetNotNone(when, *attrs)) == len(attrs)

  def _GetNotNone(self, when, *attrs):
    ''' returns a list of the non-None values for the named attributes '''
    return [x for x in (getattr(when, attr) for attr in attrs) if x is not None]



###
## CommonParser
#     but first, some regexps...


WORD1           = r'[a-zA-Z]'
WORD2           = WORD1+WORD1
WORD3           = WORD1+WORD1+WORD1
WORD4           = WORD1+WORD1+WORD1+WORD1
DIGIT1          = r'(\d)'
DIGIT2          = r'(\d\d)'
DIGIT12         = r'(\d\d?)'
DIGIT3          = r'(\d\d\d)'
DIGIT4          = r'(\d\d\d\d)'
DECIMAL         = r'(\.\d+)'

SPACE           = r'\s+'
OPTSPACE        = r'\s*'
COMMA           = r',\s*'
OPTCOMMA        = r',?\s*'
PLUSMINUS       = r'[+-]'
TIMESEP         = r'\s*[:\.]\s*'
DATESEP         = r'\s*[-/]\s*'
LOOKAHEADSEP    = Group('[t\s_:+=/\-\.]|$', GROUPTYPE_LOOK_AHEAD)
NODIGITBEHIND   = Group('\d', GROUPTYPE_NOT_BEHIND)

DAWNDUSK        = Group(Or('dawn', 'be[gin]+g', 'dusk', 'end'), name='dawndusk') + '[\s_]*of[\s_]*' + Group(Or('days', 'time'))
SPECIAL         = Group(Or('yesterday', 'today', 'now', 'tomorrow'), name='special')

HOUR            = Group(DIGIT12, name='hour')
HOUR2           = Group(DIGIT2, name='hour')
MINUTE          = Group(DIGIT12, name='minute')
MINUTE2         = Group(DIGIT2, name='minute')
SECOND          = Group(DIGIT12 + Optional(DECIMAL), name='second')
TIGHTSECOND     = Group(r'\d\d+', name='tightsecond')
AMPM            = Group('(a|p)m?', name='ampm') + LOOKAHEADSEP
OFFSET          = Group(PLUSMINUS + DIGIT12 + ':?' + Optional(DIGIT2), name='offset')
TIMEZONE        = Group(Or(r'z', WORD3, WORD4, OFFSET), name='tzname')

YEAR            = Group(DIGIT4, name='year')
MONTH2          = Group(DIGIT2, name='month')
MONTH12         = Group(DIGIT12, name='month')
MONTHNAME       = Group('{months}', name='month')
DAY2            = Group(DIGIT2, name='day')
DAY12           = Group(DIGIT12, name='day')

TIME_PATTERNS   = (
    # 5:06:07 PM PDT
    NODIGITBEHIND + HOUR + TIMESEP + MINUTE + Optional(TIMESEP + SECOND) + OPTSPACE + Optional(AMPM) + OPTSPACE + Optional(TIMEZONE) + LOOKAHEADSEP,
    # 'T010203.456Z'
    't' + HOUR + MINUTE + Optional(SECOND) + Optional(TIMEZONE) + LOOKAHEADSEP,
    # slugified
    '_' + HOUR2 + MINUTE2 + TIGHTSECOND + '_' + TIMEZONE + LOOKAHEADSEP,
    # hypen-slugified
    '-' + HOUR2 + MINUTE2 + TIGHTSECOND + '-' + TIMEZONE + LOOKAHEADSEP,
)

DATE_PATTERNS   = (
    # slugified
    YEAR + '_' + MONTH2 + '_' + DAY2 + LOOKAHEADSEP,
    # 20230820
    YEAR + MONTH2 + Optional(DAY2) + LOOKAHEADSEP,
    # June 27th, 2049
    MONTHNAME + SPACE + DAY12 + Optional(WORD2) + Optional(OPTCOMMA + YEAR) + LOOKAHEADSEP,
    # 20th of June, 2023
    DAY12 + Optional(WORD2) + SPACE + 'of' + SPACE + MONTHNAME + Optional(OPTCOMMA + YEAR),
    # 2023-08-20
    YEAR + Optional(DATESEP + MONTH12 + Optional(DATESEP + DAY12)) + LOOKAHEADSEP,
    # 14/Dec/2023
    DAY12 + DATESEP + MONTHNAME + DATESEP + YEAR + LOOKAHEADSEP,
    # 6-27 and 7/24/2023
    MONTH12 + DATESEP + DAY12 + Optional(DATESEP + YEAR) + LOOKAHEADSEP,
    # colons
    YEAR + ':' + MONTH2 + ':' + DAY2 + LOOKAHEADSEP,
)


class _CachedCommonParser(metaclass=base.utils.Singleton):
  ''' wraps the CommonParser so we can reuse it without having to reinit '''

  @base.utils.cached_method
  def __call__(self, **kwargs):
    ''' this is a cached method, so one instance should be init per version of kwargs we see '''
    return CommonParser(**kwargs)

CachedCommonParser  = _CachedCommonParser()


class CommonParser:
  ''' the basic parsing engine for Whens '''

  WHENCLASS         = base.When

  _inits            = 0

  def __init__(self, era=None, now=None, timezone=None):
    self.era        = era or CommonEra
    self.now        = now
    self.timezone   = timezone or base.consts.TIME_ZONE
    self.dawndusk   = Grouper(DAWNDUSK)
    self.special    = Grouper(SPECIAL)
    self.times      = MultiGrouper(TIME_PATTERNS, groupermode=GROUPERMODE_SEARCH, multigroupermode=MULTIGROUPERMODE_BEST)
    months          = Or(*base.utils.Flatten(*(x.name.lower() for x in era.months), *(x.tag.lower() for x in era.months)))
    patterns        = [x.format(months=months) for x in DATE_PATTERNS]
    self.dates      = MultiGrouper(patterns, groupermode=GROUPERMODE_SEARCH, multigroupermode=MULTIGROUPERMODE_BEST)
    weekdays        = base.utils.Flatten(*(x.name.lower() for x in era.weekdays), *(x.tag.lower() for x in era.weekdays))
    prefix          = Group(Or('last', 'next'), name='prefix') + SPACE
    self.weekdays   = Grouper(Optional(prefix) + Group(Or(*weekdays), name='weekday'))
    CommonParser._inits += 1

  def Parse(self, s):
    ''' attempts to generate a meaningful When from a string, given that we are attached to an era '''
    if isinstance(s, base.When):
      return s
    if not s or not isinstance(s, str):
      return
    s               = s.lower()
    when            = self.WHENCLASS(era=self.era)

    # times
    matched         = self.times and self.times.Match(s)
    timerem         = matched and matched[1]

    # dates
    matched         = self.dates and self.dates.Match(s)
    daterem         = matched and matched[1]

    # if date and time ranges overlap...
    timerange       = timerem and timerem.span()
    daterange       = daterem and daterem.span()
    if timerange and daterange and set(range(*timerange)).intersection(set(range(*daterange))):
      #  keep whichever is larger, trim it from the string, and try the other side again
      if (daterange[1] - daterange[0]) > (timerange[1] - timerange[0]):
        trims       = s[:daterange[0]] + ' ' + s[daterange[1]:]
        matched     = self.times.Match(trims)
        timerem     = matched and matched[1]
      else:
        trims       = s[:timerange[0]] + ' ' + s[timerange[1]:]
        matched     = self.times.Match(trims)
        daterem     = matched and matched[1]

    if timerem:
      self._GroupResults(timerem, when)
    if daterem:
      self._GroupResults(daterem, when)

    if not when.zero:
      return when

    # special things
    for specialthing in ('dawndusk', 'special', 'weekdays'):
      pattern       = getattr(self, specialthing)
      matched       = pattern(s)
      if matched:
        return getattr(self, '_' + specialthing.title())(matched)

  def _GroupResults(self, rem, when):
    ''' given a regexp match, populate a When '''
    pm              = False
    groups          = rem.groupdict()
    for attr, value in groups.items():
      if value:
        if attr == 'tightsecond':
          attr      = 'second'
          value     = value[:2] + '.' + (value[2:] or '0')
        elif attr == 'offset':
          attr      = 'tzname'
        elif attr == 'ampm':
          pm        = value[0] == 'p'
          continue
        setattr(when, attr, value)

    if pm and when.hour:
      try:
        when.hour   = int(when.hour) + 12
      except:
        pass

  ## handlers for enum matches

  def _Dawndusk(self, matched):
    ''' given a match to our DAWNDUSK possibilites, return a populated When '''
    value           = matched.get('dawndusk', '')
    if value.startswith('dawn') or value.startswith('beg'):
      return base.When(era=self.era, special=base.whens.SPECIALWHEN_DAWN_OF_TIME)
    if value.startswith('dusk') or value.startswith('end'):
      return base.When(era=self.era, special=base.whens.SPECIALWHEN_END_OF_DAYS)

  def _Special(self, matched):
    ''' given a match to any of our specials besides dawn and dusk, return a populated When '''
    special         = base.whens.SpecialWhens(matched.get('special'))
    return self._PopulateNow(base.When(era=self.era, special=special))

  def _Weekdays(self, matched):
    ''' given a match to our weekdays, return a populated When '''

    weekday         = matched.get('weekday')
    if not weekday in self.era.weekdays:
      return
    weekday         = self.era.weekdays(weekday).index
    prefix          = matched.get('prefix')

    now             = self.now or base.utils.Now()
    when            = base.When(era=self.era)
    weekdays        = len(self.era.weekdays)
    current         = now.weekday() + 1
    count           = 0
    nextlast        = (prefix or '').strip()
    one             = nextlast == 'last' and -1 or 1

    while current != weekday:
      count         += one
      current       = (current + one) % weekdays

    if count:
      now           = now + datetime.timedelta(days=count)

    when.year     = now.year
    when.month    = now.month
    when.day      = now.day
    return when

  ## support structures

  def _PopulateNow(self, when):
    ''' given our sense of now, try to translate enum-only defined whens '''
    now             = self.now or base.utils.Now()
    if when.special == base.whens.SPECIALWHEN_YESTERDAY:
      now           = now - datetime.timedelta(days=1)
    elif when.special == base.whens.SPECIALWHEN_TOMORROW:
      now           = now + datetime.timedelta(days=1)
    elif when.special == base.whens.SPECIALWHEN_NOW:
      return base.When.From(now)
    when.year     = now.year
    when.month    = now.month
    when.day      = now.day
    return when



###
## CommonEra
#

class CommonEra(base.whens.Era):
  tag               = 'CE'
  name              = 'Common Era'
  icon              = 'calendar'
  aliases           = ('AD',)
  months            = Months
  weekdays          = Weekdays
  parser            = CachedCommonParser    # set to CommonParser to fail a test case
  cleaner           = CommonCompletionist
  WhenType          = base.When

  @classmethod
  def DaysInYear(klass, year, month):
    return calendar.isleap(year) and 366 or 365

  @classmethod
  def DaysInMonth(klass, year, month):
    return calendar.monthrange(year, month)[1]

  @classmethod
  def DayOfWeek(klass, year, month, day):
    date            = datetime.date(year=year, month=month, day=day)
    return (date.weekday() + 1) % 7

  @classmethod
  def MakeNow(klass, fractional=True):
    ''' returns a When initialized from datetime now '''
    now             = base.utils.Now()
    if not fractional:
      now           = now.replace(microsecond=0)
    return klass.MakeWhenFromDateTime(base.utils.LocalTime(now))

  @classmethod
  def MakeWhen(klass, thing, now=None, timezone=None):
    ''' convert the thing -- string or datetime -- into a When '''
    if isinstance(thing, str):
      return klass.MakeWhenFromString(thing, now=now, timezone=timezone)
    elif isinstance(thing, datetime.datetime) or isinstance(thing, datetime.time) or isinstance(thing, datetime.date):
      return klass.MakeWhenFromDateTime(thing)
    elif isinstance(thing, dict):
      return klass.MakeWhenFromParts(**thing)

  @classmethod
  def MakeWhenFromString(klass, s, now=None, timezone=None):
    parser          = klass.parser(era=klass, now=now, timezone=timezone)
    return klass.cleaner(era=klass).Complete(parser.Parse(s))

  @classmethod
  def MakeWhenFromDateTime(klass, dt):
    if not dt:
      return

    when            = base.When()

    if isinstance(dt, datetime.datetime) or isinstance(dt, datetime.time):
      when.hour     = dt.hour
      when.minute   = dt.minute
      when.second   = dt.second
      if dt.microsecond:
        when.second += dt.microsecond / 1000000
      if dt.tzinfo:
        when.timezone = dt.tzinfo
        if isinstance(dt, datetime.datetime):
          when.tzname = dt.tzname()

    if isinstance(dt, datetime.datetime) or isinstance(dt, datetime.date):
      when.year     = dt.year
      when.month    = dt.month
      when.day      = dt.day

    return klass.cleaner(era=klass).Complete(when)

  @classmethod
  def MakeWhenFromParts(klass, **d):
    when            = klass.cleaner(era=klass).Complete(klass.WhenType(**d))
    if when and when.datetime and when.tzname:
      when.Localize()
    return when

  @classmethod
  def SmolText(klass, when):
    return base.utils.Slugify(klass.WhenText(when).replace('-', '')) or ''

  @classmethod
  def LongText(klass, when):
    if when.cosmic:
      return when.special.name

    year            = when.year and str(when.year) or ''
    month           = when.month and when.month_name or ''
    day             = when.day and (str(when.day) + klass._Suffix(when.day)) or ''

    combined        = month and day and ' '.join((month, day)) or month or day
    if year and day:
      combined      = combined + ','
    if year:
      combined      = ' '.join((combined, year))

    if day and when.weekday_name:
      combined      = when.weekday_name + ' ' + combined

    if when.hour or when.minute or when.second:
      dupe          = when.Dupe()
      dupe.ClearDate()
      combined      = '; '.join((combined, dupe.text))

    return combined

  @staticmethod
  def _Suffix(i):
    if not i:
      return 'st'
    if i > 10 and i < 21:
      return 'th'
    i               = i % 10
    if not i:
      return 'th'
    if i == 1:
      return 'st'
    if i == 2:
      return 'nd'
    if i == 3:
      return 'rd'
    return 'th'

  @classmethod
  def WhenText(klass, when):
    if when.cosmic:
      return when.special.name

    text            = ''
    if when.year is not None or when.month is not None:
      text          = when.year is not None and str(when.year) or ''
      if when.month is not None:
        if text:
          text      += '-'
        text        += '{:02}'.format(when.month)
        if when.day is not None:
          text        += '-{:02}'.format(when.day)

    if when.hour is not None and when.minute is not None:
      if text:
        text        += ' '
      text          += '{:02}'.format(when.hour)
      text          += ':{:02}'.format(when.minute)
      if when.second is not None:
        second      = math.floor(when.second)
        text        += ':{:02}'.format(second)
        usecond     = round((when.second - second) * 1000000)
        if usecond:
          text      += '.{:06}'.format(usecond).rstrip('0').rstrip('.')

      if when.timezone or when.tzname:
        if when.tzname:
          text      += ' ' + when.tzname
        elif when.timezone == base.consts.TIME_UTC:
          text      += ' UTC'
        else:
          dt        = when.datetime
          if dt:
            text    += ' ' + dt.tzname()
          else:
            # i think this should only happen if we were built from a timezone-aware datetime.time
            raise base.errors.IncompleteWhen('unable to name the timezone unless the datetime is complete')

    return text

  @classmethod
  def AddTimeDelta(klass, when, delta):
    if when.date and not when.time:
      # datetime.date can be added to timedelta, it just ignores sub-day units
      if delta.seconds or delta.microseconds:
        raise base.errors.TimeDeltaHasTime(when, delta, delta.total_seconds())
      return klass.MakeWhen(when.date + delta)

    elif when.time and not when.date:
      # negative timedeltas come in looking like they have a date component, so let's go to seconds before checking
      deltasecs   = delta.total_seconds()
      if deltasecs <= -86400 or deltasecs > 86400:
        raise base.errors.TimeDeltaHasDate(when, delta, delta.total_seconds())
      seconds     = (when.hour or 0) * 3600 + (when.minute or 0) * 60 + (when.second or 0)
      seconds     += delta.total_seconds()
      seconds     = seconds % (60 * 60 * 24)  # 86400; also, this will always be positive

      res         = when.Dupe()
      res.hour    = int(seconds / 60 / 60)
      seconds     -= res.hour * 60 * 60
      res.minute  = int(seconds / 60 )
      seconds     -= res.minute * 60
      if seconds == int(seconds):
        seconds   = int(seconds)
      res.second  = seconds

      if when.second is None and not res.second:
        res.second    = None
        if when.minute is None and not res.minute:
          res.minute  = None

      return res

    elif when.datetime:
      return klass.MakeWhen(when.datetime + delta)

    raise base.errors.IncompleteWhen(when)

  @classmethod
  def Subtract(klass, when0, when1):
    if when0.datetime and when1.datetime:
      return when0.datetime - when1.datetime
    if when0.date and when1.date:
      return when0.date - when1.date
    raise base.errors.IncompleteWhen(when0, when1)



###
## test cases
#


class TestWhenDateTime(base.TestCase):
  ''' minimal basic test that we can roundtrip a datetime through a When '''

  def Run(self):
    timezone      = zoneinfo.ZoneInfo('America/Denver')
    dt0           = datetime.datetime(2023, 8, 18, 20, 28, 25, 552447, tzinfo=timezone)
    when          = base.When.From(dt0)
    dt1           = when.datetime
    self.Try("dt0 == dt1")
    self.Try("str(when) == '2023-08-18 20:28:25.552447 MDT'")



# { input: expected }
WHEN_TEST_DATA    = {
    # special days
    'Beginining of Time':                                     'Dawn of Time',
    'End of Time':                                            'End of Days',
    'dawn_of_time':                                           'Dawn of Time',
    'end_of_days':                                            'End of Days',

    # these depend on the "now" that we pass in at time of parse
    'Yesterday':                                              '2023-08-17',
    'Today':                                                  '2023-08-18',
    'Now':                                                    '2023-08-18 21:12:34.123456 MDT',
    'Tomorrow':                                               '2023-08-19',
    'Monday':                                                 '2023-08-21',
    'Next Tuesday':                                           '2023-08-22',
    'Last Thursday':                                          '2023-08-17',

    # basic times
    '5:09p':                                                  '17:09',
    '17:09 pdt':                                              '17:09 PDT',
    '17:09:10 pdt':                                           '17:09:10 PDT',
    '11:19:27.209210':                                        '11:19:27.20921',

    # basic dates
    '2023':                                                   '2023',
    '2023-08':                                                '2023-08',
    '2023-08-20':                                             '2023-08-20',
    '202308':                                                 '2023-08',
    '20230820':                                               '2023-08-20',
    'June 27th, 2049':                                        '2049-06-27',
    'Sun June 27':                                            '06-27',
    'June 27':                                                '06-27',
    '06-27':                                                  '06-27',
    '6-27':                                                   '06-27',

    # AM/PM
    '2023-08-20 10:45 AM MDT':                                '2023-08-20 10:45 MDT',
    '2023-08-20 11:45:51 PM PDT':                             '2023-08-21 00:45:51 MDT',

    # offsets
    '2021-08-04 17:00:00+05:00':                              '2021-08-04 06:00:00 MDT',

    # month first
    'Feb 5, 2022 at 13:59':                                   '2022-02-05 13:59 MST',
    '20th of August, 2023 at 13:28':                          '2023-08-20 13:28 MDT',
    '7/24/2023':                                              '2023-07-24',

    # idempotency
    '2020-08-16 19:05:08.773308 MDT':                         '2020-08-16 19:05:08.773308 MDT',

    # ISO 8601 and things that look almost like it
    '2023-08-20T11:19:27.209210-06:00':                       '2023-08-20 11:19:27.20921 MDT',      # actual ISO 8601
    '2023-08-20 11:19:27.209210-06:00':                       '2023-08-20 11:19:27.20921 MDT',
    '2023-08-20 11:19:27.209210 -06:00':                      '2023-08-20 11:19:27.20921 MDT',
    '2023-08-20 11:19:27.209210 -0600':                       '2023-08-20 11:19:27.20921 MDT',
    '2023-08-20 11:19:27.209210-0600':                        '2023-08-20 11:19:27.20921 MDT',
    '2023-08-20 11:19:27.209210-06':                          '2023-08-20 11:19:27.20921 MDT',
    '2023-08-20 11:19:27.209210-6':                           '2023-08-20 11:19:27.20921 MDT',
    '2021-03-23T15:55:15.574494Z':                            '2021-03-23 09:55:15.574494 MDT',
    '2020-08-17T01:05:08.7733076Z':                           '2020-08-16 19:05:08.773308 MDT',

    # these formats come from our log files
    '20231224_095635_mst':                                    '2023-12-24 09:56:35 MST',            # When.smol
    '2023_12_14_200537039604_utc':                            '2023-12-14 13:05:37.039604 MST',     # Slugify(str(When)
    '14/Dec/2023:18:10:40 +0000':                             '2023-12-14 11:10:40 MST',            # Nginx default time format
    '20231203-162832-MST':                                    '2023-12-03 16:28:32 MST',            # old backup dir name

    # this is what timestamps look like in image metadata
    '2023:08:20':                                             '2023-08-20',
    '2023:08:20 11:12:13':                                    '2023-08-20 11:12:13 MDT',

    # filepaths
    'abcde:/Foo/20140225 - 8633 Miles/':                      '2014-02-25',
    'abcde:/Foo/2012/08/16-EventName.jpg':                    '2012-08-16',
    'abcde:/Foo/2012/08/16 - EventName.jpg':                  '2012-08-16',
    'abcde:/Foo/2012 - 08/16 - EventName.jpg':                '2012-08-16',
    'abcde:/Foo/Screen Shot 2012-9-4 at 1.6.44 AM.jpg':       '2012-09-04 01:06:44 MDT',
    'abcde:/Foo/Screen Shot 2012-9-4 at 1.13.44 PM.jpg':      '2012-09-04 13:13:44 MDT',
    'abcde:/Foo/2012-01-26 21.22.06.jpg':                     '2012-01-26 21:22:06 MST',
    'abcde:/Foo/2012-01-26/21.22.06.jpg':                     '2012-01-26 21:22:06 MST',
    'abcde:/Foo/20120816T010203.456Z.jpg':                    '2012-08-15 19:02:03.456 MDT',
    'abcde:/Foo/20120816T010203.jpg':                         '2012-08-16 01:02:03 MDT',
    'abcde:/Foo/20120816T0102.jpg':                           '2012-08-16 01:02 MDT',
    'abcde:/Foo/2012-004.jpg.lrbak':                          '2012',
    'abcde:/Foo/2012/16-004.jpg':                             'None',                               # some things are beyond us
    'History-03-08-2025-12-00-00.csv':                        'None',                               # some things are beyond us
}



class TestWhenWithStrings(base.TestCase):
  ''' tests our ability to pick up dates from arbitrary strings, using every test case that had been
      written for our old time parsing code, plus a few others we've picked up along the way
  '''

  @staticmethod
  def _Sanitize(s):
    if '\n' in s:
      s             = s[:s.find('\n')]
    s               = s.strip()
    if len(s) > 35:
      s             = s[:34] + '…'
    return s

  def Run(self, whenclass=base.When, testdata=WHEN_TEST_DATA):
    timezone        = zoneinfo.ZoneInfo('America/Denver')
    now             = datetime.datetime(2023, 8, 18, 21, 12, 34, 123456, tzinfo=timezone)
    for input, expected in testdata.items():
      exception     = None
      try:
        when        = whenclass.From(input, now=now)
      except Exception as err:
        exception   = err
        result      = self._Sanitize(str(err))
      else:
        if isinstance(when, base.When):
          if when.datetime:
            when.Shift(timezone, timezone)
          result      = when.text
          if not(isinstance(result, str)):
            result    = repr(result) + ' (indirectly)'
        else:
          result      = repr(when)
      passed        = result == expected
      message       = '{}  -->  {}'.format(base.utils.PadString(input, 55), base.utils.PadString(self._Sanitize(result), 35))
      if not passed:
        message     = message + '  EXPECTED:  {}'.format(expected)
      message       = message.rstrip()
      self.LogResult(passed, message)
      if not passed and exception:
        print('Exception:\n'+str(exception))



class TestWhenSpeed(base.TestCase):
  def Run(self, whenclass=base.When, testdata=WHEN_TEST_DATA, primer='2000-01-01 12:34 EST'):
    if not testdata:
      return

    # prime the system
    stopwatch       = base.utils.Stopwatch()
    whenclass.From(primer)
    priming         = round(stopwatch.Lap().total_seconds() * 1000000)
    inits0          = CommonParser._inits
    fails           = 0

    # time the system
    for s in testdata:
      try:
        whenclass.From(s)
      except:
        fails       += 1
    usecs           = round(stopwatch.Lap().total_seconds() * 1000000)
    usecsper        = round(usecs / len(testdata))
    inits           = CommonParser._inits - inits0

    # log results
    mess0           = 'priming took {} microsecond{}'.format(priming, priming != 1 and 's' or '')
    print(' - ' + mess0)
    if priming < 1000:
      print('   - suspiciously low; try running with `--only={}` for a more trustworthy reading'.format(base.utils.ObjectName(self)))

    mess0           = '{} string{} parsed'.format(len(testdata), len(testdata) != 1 and 's' or '')
    mess1           = fails and '({} failure{})'.format(fails, fails != 1 and 's' or '') or ''
    mess2           = 'in {} microsecond{},'.format(usecs, usecs != 1 and 's' or '')
    mess3           = 'or {} microsecond{} per parse'.format(usecsper, usecsper != 1 and 's' or '')
    print(' - ' + ' '.join((mess0, mess1, mess2, mess3)))

    mess0           = 'CommonParser was instantiated {} time{} during this test'.format(inits, inits != 1 and 's' or '')
    mess1           = inits and '-- ERROR: expected 0' or '\n   - {} init{} total so far'.format(inits0, inits0 != 1 and 's' or '')
    print(' - ' + ' '.join((mess0, mess1)))

    return not inits



SORTED_WHENS        = (
    'Dawn of Time',
    '11:19:27.20921',
    '17:09',
    '17:09 PDT',
    '17:09:10 PDT',
    '06-27',
    '2012',
    '2012-01-26 21:22:06 MST',
    '2012-01-26 21:22:06 MST',
    '2012-08-16',
    '2012-08-15 19:02:03.456 MDT',    # 08-16 in UTC
    '2012-08-16 01:02 MDT',
    '2012-08-16 01:02:03 MDT',
    '2012-09-04 01:06:44 MDT',
    '2012-09-04 13:13:44 MDT',
    '2014-02-25',
    '2020-08-16 19:05:08.773308 MDT',
    '2020-08-16 19:05:08.773308 MDT',
    '2021-03-23 09:55:15.574494 MDT',
    '2021-08-04 06:00:00 MDT',
    '2022-02-05 13:59 MST',
    '2023',
    '2023-08',
    '2023-08-17',
    '2023-08-18',
    '2023-08-19',
    '2023-08-18 21:12:34.123456 MDT', # 08-19 in UTC
    '2023-08-20',
    '2023-08-20 10:45 MDT',
    '2023-08-20 11:19:27.20921 MDT',
    '2023-08-20 13:28 MDT',
    '2023-08-21',
    '2023-08-21 00:45:51 MDT',
    '2023-08-22',
    '2023-12-03 16:28:32 MST',
    '2023-12-14 11:10:40 MST',
    '2023-12-14 13:05:37.039604 MST',
    '2023-12-24 09:56:35 MST',
    '2049-06-27',
    'End of Days',
)


class TestWhenSort(base.TestCase):
  def Run(self, whenclass=base.When, testdata=SORTED_WHENS, primer='2000-01-01 12:34 EST'):
    whens           = [whenclass.From(x) for x in testdata]
    random.shuffle(whens)
    whens.sort()
    texts           = [x.text for x in whens]

    for result, expected in zip(texts, testdata):
      passed        = result == expected
      message       = base.utils.PadString(str(result), 55)
      if not passed:
        message     += '  EXPECTED:  ' + expected
      self.LogResult(passed, message.rstrip())


class TestWhenFromSortable(base.TestCase):
  def Run(self, whenclass=base.When, testdata=SORTED_WHENS, primer='2000-01-01 12:34 EST'):
    whens           = [whenclass.From(x) for x in testdata]
    for expected in whens:
      result        = whenclass.From(expected.sortable)
      passed        = result == expected
      message       = base.utils.PadString(str(result), 55)
      if not passed:
        message     += '  EXPECTED:  ' + str(expected)
      self.LogResult(passed, message.rstrip())



class TestWhenDayOfWeek(base.TestCase):
  def Run(self, whenclass=base.When, primer='2025-12-09 01:00 UTC'):
    when          = whenclass.From(primer)
    self.Try("when.weekday == 2")
    self.Try("when.Localize().weekday == 1")



class TestWhenMathBase(base.TestCase, skip=1):

  def InnerRun(self, when0, when1, delta):
    self.Try("when0 < when1")
    self.Try("when0 <= when1")
    self.Try("when0 == when0")
    self.Try("when0 != when1")
    self.Try("when1 >= when0")
    self.Try("when1 > when0")

    self.Try("when0 + delta == when1")
    self.Try("delta + when0 == when1")
    self.Try("when1 - delta == when0")

    when0 += delta
    self.Try("when0 == when1")
    when0 -= delta
    self.Try("when0 != when1")


class TestDateWhenMath(TestWhenMathBase):

  def Run(self):
    when0           = base.When.From('2025-06-04')
    when1           = base.When.From('2025-06-05')
    delta           = datetime.timedelta(days=1)
    self.InnerRun(when0, when1, delta)


class TestTimeWhenMath(TestWhenMathBase):

  def Run(self):
    when0           = base.When.From('12:34')
    when1           = base.When.From('13:45:06')
    delta           = datetime.timedelta(hours=1, minutes=11, seconds=6)
    self.InnerRun(when0, when1, delta)


class TestDateTimeWhenMath(TestWhenMathBase):

  def Run(self):
    when0           = base.When.From('2025-06-04 12:34')
    when1           = base.When.From('2025-06-05 13:45:06')
    delta           = datetime.timedelta(days=1, hours=1, minutes=11, seconds=6)
    self.InnerRun(when0, when1, delta)
