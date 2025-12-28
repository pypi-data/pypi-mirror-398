#!/opt/local/bin/python
''' Functions for working with strings. '''

import base
import datetime
import hashlib
import html
import math
import re
import string
import time

from . import environment
environment.DeferImport('numpy', 'np')
environment.DeferImport('bleach')


# This should be at minimum the length of string that HashString() returns;
# currently we hash using SHA256, which fits within 64 hex digits.
MAX_LENGTH_SLUG   = 64


def Slugify(r, spaces='_', hyphens='_', case='unset', allowed=None, max_length=None):
  ''' Strips whitespace and other nasty characters. '''
  if not r:
    return ''
  if case == 'unset':
    case          = string.ascii_lowercase
  if not allowed:
    allowed       = case + string.digits
    if spaces:
      allowed     = allowed + spaces
    if hyphens and hyphens != spaces:
      allowed     = allowed + hyphens
  if not max_length:
    max_length    = MAX_LENGTH_SLUG
  if not isinstance(r, str):
    r             = str(r)
  if '&' in r and ';' in r:
    r             = html.unescape(r)
  r               = r.strip()
  if case == string.ascii_lowercase:
    r             = r.lower()
  elif case == string.ascii_uppercase:
    r             = r.upper()
  if hyphens:
    r             = r.replace('-', hyphens)
  if spaces:
    for c in string.whitespace:
      r           = r.replace(c, spaces)
  if allowed:
    r             = ''.join([c for c in r if c in allowed])
  if '-' in allowed:
    while '--' in r:
      r             = r.replace('--', '-')
  if '_' in allowed:
    while '__' in r:
      r             = r.replace('__', '_')
  if max_length and len(r) > max_length:
    r             = r[:max_length]
  return r


def DeSlugify(s):
  ''' Expands a snake-case slug into words. '''
  return s and s.replace('_', ' ').strip().title() or ''



def ToSnakeCase(s):
  ''' Transforms MixedCase to snake_case   (stackoverflow.com/questions/1175208)  '''
  global __re_tosnake_first, __re_tosnake_all
  s               = __re_tosnake_first.sub(r'\1_\2', s)
  s               = __re_tosnake_all.sub(r'\1_\2', s)
  return s.lower()
__re_tosnake_first  = re.compile('(.)([A-Z][a-z]+)')
__re_tosnake_all    = re.compile('([a-z0-9])([A-Z])')


def ToMixedCase(s):
  ''' Transforms snake_case to MixedCase '''
  return ''.join([x.capitalize() for x in s.split('_')])


def PadString(text, width, align='<', stepping=0):
  ''' Returns the text padded to width spaces
        - align should be one of <, ^, or > for left, center, right
        - stepping is number of characters to increase width by if the string is too long
  '''
  if stepping:
    truewidth     = max(width, len(text))
    if truewidth > width:
      width       = width + (int(math.floor((truewidth - width + stepping - 1) / stepping)) * stepping)
  return '{:{align}{width}s}'.format(text or '', align=align, width=width)


def HumanizeBytes(count, precision=2, short=False, kibi=True, kibinames=False):
  prefixes        = ('', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa')
  kibifixes       = ('', 'kibi', 'mebi', 'gibi', 'tibi', 'pebi', 'exbi')
  prefix          = 0
  multiplier      = kibi and (2**10) or 1000
  sizer           = multiplier
  divisor         = 1
  while count > sizer and prefix < len(prefixes) - 1:
    prefix        += 1
    sizer         *= multiplier
    divisor       *= multiplier
  value           = str(round(count / divisor, precision)).rstrip('0').rstrip('.')
  prefix          = (kibi and kibinames and kibifixes or prefixes)[prefix]
  if short:
    unit          = (prefix and prefix[0] or ' ') + 'b'
  else:
    unit          = prefix + 'byte' + (value != 1 and 's' or '')
  return value + ' ' + unit

def FindWhitespace(text):
  ''' Returns None or [index0, index1) for the first run of whitespace in the input string. '''
  if not text:
    return
  for i, c in enumerate(text):
    if c.isspace():
      for j, d in enumerate(text[i+1:]):
        if not d.isspace():
          return i, i+j+1
      return i, len(text)


def CollapseWhitespace(text, to=' '):
  ''' Returns a string with consecutive whitespace characters collapsed to a single space. '''
  if not text:
    return ''
  index0        = 0
  while index0 < len(text):
    match       = FindWhitespace(text[index0:])
    if not match:
      return text
    a, b        = match
    text        = text[:index0+a] + to + text[index0+b:]
    index0      = index0 + a + 1
  return text


def UnifyWhitespace(s, preferred=' '):
  ''' Replaces any standard whitespace character with a known type of space. '''
  return ''.join([(c.isspace() and preferred or c) for c in s])


def UnifyQuotes(s, preferred='"'):
  ''' Replaces any standard quote marks with a known type of quote mark. '''
  return ''.join([((c in base.consts.Quotes) and preferred or c) for c in s])


def HashString(s):
  ''' Returns a slug-compatible hash string from a given input string or bytes -- 64 hex chars. '''
  if not s:
    return None
  if isinstance(s, str):
    s             = s.encode('utf8', 'ignore')
  return hashlib.sha256(s).hexdigest().lower()


def UniqueString():
  ''' Returns a HashString() of enough entropy to be unique in all time/space. '''
  return HashString('{}//{}//{}'.format(base.utils.HostName(), base.utils.ThreadName(), time.time()))


def HashStringWithTimeWindow(s, dt=None):
  ''' Returns a HashString() that changes every 1-minute-ish. '''
  if not dt:
    dt            = base.utils.Now()
  dt              = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, tzinfo=dt.tzinfo)
  hashable        = '{}//{}'.format(dt.isoformat(), s or '')
  return HashString(hashable)


def Entropy(s):
  ''' Returns a numeric value for the shannon entropy of the input string. '''
  if not s:
    return 0
  _, counts       = np.unique(list(s), return_counts=True)
  counts          = counts / counts.sum()
  entropy         = (counts * np.log(counts)/np.log(math.e)).sum()
  return entropy and -entropy or 0


def StripHtml(s, fully_remove=None):
  ''' Strips from a string anything that looks like tags, leaving only the plain text.
      Entities are un-escaped; for example "&ndash;" is expanded into a unicode en-dash.

      'fully_remove' can contain a list of HTML tags that should have their contents
      stripped out entirely.  By default we'll do this with 'script' and 'style' tags.
  '''
  if not s:
    return ''
  tags            = set(('script', 'style')) | set(fully_remove or [])
  startends       = [('<' + tag, '</' + tag + r'\s*>') for tag in tags]
  startends.append(('{%', '%}'))
  startends.append(('{{', '}}'))
  for start, end in startends:
    pattern       = '{}.*?{}'.format(start, end)
    match         = re.search(pattern, s, (re.DOTALL | re.IGNORECASE))
    while match:
      s           = s[:match.start()] + s[match.end():]
      match       = re.search(pattern, s, (re.DOTALL | re.IGNORECASE))
  if '&' in s and ';' in s:
    s             = html.unescape(s)
  s               = bleach.clean(s, strip=True, tags=[]).strip()
  return s
