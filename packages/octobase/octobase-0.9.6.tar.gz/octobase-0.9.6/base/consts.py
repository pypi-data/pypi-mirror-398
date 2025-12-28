#!/opt/local/bin/python

import base
import datetime
import os

try:
  import zoneinfo
except:
  zoneinfo      = None



### Length Limits

# Maximum character count in a slug-like string.
# For import order this is defined in another file, for sake of easy finding it we copy it here.
MAX_LENGTH_SLUG         = base.utils.strings.MAX_LENGTH_SLUG  # probably 64



### Timezones

def _TryToGetLocalTimeZone():
  ''' On unix-like systems this should return the pytz timezone for system local time. '''
  if os.path.islink('/etc/localtime'):
    parts         = os.readlink('/etc/localtime').split('/')[-2:]
    if parts:
      if parts[-1] == 'UTC':
        return datetime.timezone.utc
      try:
        return zoneinfo.ZoneInfo('/'.join(parts))
      except:
        pass


TIME_UTC                = datetime.timezone.utc
TIME_ZONE               = zoneinfo and _TryToGetLocalTimeZone() or None



### DateTime Limits

# We add/subtract one day from date min/max so they can be localized without overflowing
DATE_MIN                = datetime.date.min + datetime.timedelta(days=1)
DATE_MAX                = datetime.date.max - datetime.timedelta(days=1)
DATETIME_MIN            = datetime.datetime.min.replace(tzinfo=TIME_UTC) + datetime.timedelta(days=1)
DATETIME_MAX            = datetime.datetime.max.replace(tzinfo=TIME_UTC) - datetime.timedelta(days=1)



### Quotes

# All the standard unicode quote marks
base.Enum.Define(('QUOTE', 'Quotes'), (
    ('Quotation Mark',                '"'),
    ('Apostrophe',                    "'"),
    ('Grave Accent',                  '`'),
    ('Acute Accent',                  '´'),
    ('Left Single Quotation Mark',    '‘'),
    ('Right Single Quotation Mark',   '’'),
    ('Left Double Quotation Mark',    '“'),
    ('Right Double Quotation Mark',   '”'),
))
