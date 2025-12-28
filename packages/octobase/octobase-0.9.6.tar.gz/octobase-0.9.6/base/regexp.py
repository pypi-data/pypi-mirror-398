#!/opt/local/bin/python

import base
import re

base.Enum.Define(('GROUPTYPE', 'GroupTypes'), (
    ('Capture',         ''),
    ('No-Capture',      '?:'),
    ('Sub-Expression',  '?>'),      # python 3.11; also, not sure how to use this yet
    ('Named',           '?P'),      # follow with '<name>'
    ('Look Ahead',      '?='),
    ('Not Ahead',       '?!'),
    ('Look Behind',     '?<='),
    ('Not Behind',      '?<!'),
))

base.Enum.Define(('GROUPERMODE', 'GrouperModes'), (
    ('Total',           'total'),
    ('Start',           'start'),
    ('Search',          'search'),
))

base.Enum.Define(('MULTIGROUPERMODE', 'MultiGrouperModes'), (
    ('First',           'first'),
    ('Best',            'best'),
))


###
## helpers
#

## grouping is the workhorse of regular expressions

def Group(s, grouptype=GROUPTYPE_NO_CAPTURE, name=None):
  ''' ensures a string is wrapped in the right kind of parens '''
  if not s:
    return s

  if name:
    grouptype     = GROUPTYPE_NAMED
  if grouptype == GROUPTYPE_NAMED:
    grouptype     = grouptype + '<' + name + '>'
  else:
    grouptype     = GroupTypes(grouptype)

  if s == '(' + grouptype + ')':
    return s

  if s[0] != '(' or s[-1] != ')':
    return '(' + grouptype + s + ')'

  slice           = s[1:-1]
  if '(' in slice or ')' in slice:
    return '(' + grouptype + s + ')'

  if s.startswith('(' + grouptype):
    return s

  if grouptype == GROUPTYPE_NO_CAPTURE:
    return s

  return '(' + grouptype + s + ')'


def Capture(s, name=None):
  if name:
    return Group(s, GROUPTYPE_NAMED, name)
  return Group(s, GROUPTYPE_CAPTURE)


def Optional(s, grouptype=GROUPTYPE_NO_CAPTURE, name=None):
  if name:
    grouptype     = GROUPTYPE_NAMED
  if len(s) > 1:
    s             = Group(s, grouptype=grouptype, name=name)
  return s + '?'


def BackRef(name):
  ''' emits a reference back to an earlier named group '''
  return '(?P=' + name + ')'


def Or(*lst):
  ''' emits a naked list of | -delimited non-capturing groups '''
  if len(lst) == 1 and (isinstance(lst[0], list) or isinstance(lst[0], tuple)):
    lst           = lst[0]
  MaybeGroup      = lambda x: len(x) > 1 and Group(x, GROUPTYPE_NO_CAPTURE) or x
  return '|'.join(MaybeGroup(s) for s in lst)


###
## smarter things
#


class Grouper:
  ''' class you init with a pattern, then acts like a function to turn strings into a dictionary
      of groups matched in those strings.  if the pattern contains no name groups, we return the
      re.match object instead
  '''

  def __init__(self, pattern, groupermode=GROUPERMODE_SEARCH):
    self.mode       = GrouperModes(groupermode)
    self.pattern    = re.compile(pattern)

  def __repr__(self):
    return base.utils.ClassName(self) + '(' + self.pattern.pattern + ')'

  def __hash__(self):
    return hash(self.pattern.pattern + '//' + str(self.mode))

  def __eq__(self, other):
    return hash(self) == hash(other)

  def __call__(self, s):
    ''' returns captured groups, True if we matched but didn't capture any groups, or None if we did not match '''
    rem             = self.Match(s)
    if rem:
      return rem.groupdict() or rem

  def Match(self, s):
    ''' returns a re.match if our pattern matches the string '''
    rem             = None
    if self.mode == GROUPERMODE_SEARCH:
      rem           = self.pattern.search(s)
    elif self.mode == GROUPERMODE_START:
      rem           = self.pattern.match(s)
    elif self.mode == GROUPERMODE_TOTAL:
      rem           = self.pattern.match(s)
      if rem and rem.end() != len(s):
        rem         = None
    if rem and rem.start() == rem.end():
      rem           = None
    return rem



class MultiGrouper:
  ''' class you init with a list or dict of patterns, and can act like a Grouper() over all of them at once '''

  def __init__(self, patterns, multigroupermode=MULTIGROUPERMODE_BEST, groupermode=GROUPERMODE_SEARCH):
    self.mode       = MultiGrouperModes(multigroupermode)
    self.patterns   = []    #  ( token, grouper ) ]

    if not patterns:
      return

    if isinstance(patterns, dict):
      self.patterns   = [(x, self._Grouper(y, groupermode=groupermode)) for x,y in patterns.items()]
    elif isinstance(patterns, list) or isinstance(patterns, tuple):
      if isinstance(patterns[0], list) or isinstance(patterns[0], tuple):
        self.patterns = [(x, self._Grouper(y, groupermode=groupermode)) for x,y in patterns]
      else:
        counter       = base.utils.Counter()
        self.patterns = [(counter(), self._Grouper(x, groupermode=groupermode)) for x in patterns]
    else:
      raise AttributeError('patterns must be a dict or a list')

  def _Grouper(self, x, groupermode=GROUPERMODE_START):
    if isinstance(x, Grouper):
      return x
    return Grouper(x, groupermode=groupermode)

  def __call__(self, s):
    ''' returns (token, groups) for whichever pattern among us matched '''
    matched         = self.Match(s)
    if matched:
      token, rem    = matched
      return token, rem.groupdict() or rem.groups()

  def Match(self, s):
    ''' returns (token, re.match) if our pattern matches the string '''
    if self.mode == MULTIGROUPERMODE_FIRST:
      for token, pattern in self.patterns:
        results     = pattern.Match(s)
        if results:
          return token, results
    elif self.mode == MULTIGROUPERMODE_BEST:
      results       = [(x, y.Match(s)) for x,y in self.patterns]
      results.sort(key=self._Score, reverse=True)
      token, result = results[0]
      if result:
        return token, result

  def _Score(self, xy):
    token, rem    = xy
    if not rem:
      return 0
    groups        = rem.groupdict()
    if not groups:
      return 0
    return sum(1 for x in groups.values() if x is not None)


###
## tests
#


class TestRegExpHelpers(base.TestCase):

  def Run(self):
    self.Try("Group('') == ''")

    self.Try("Group('x') == '(?:x)'")
    self.Try("Group('(x)') == '(x)'")
    self.Try("Group('(x)|(y)', GROUPTYPE_CAPTURE) == '((x)|(y))'")

    self.Try("Group('x', '?:') == '(?:x)'")
    self.Try("Group('(x)', '?:') == '(x)'")
    self.Try("Group('(?:x)', '?:') == '(?:x)'")
    self.Try("Group('(x)(y)', '?:') == '(?:(x)(y))'")

    self.Try("Group('x', GROUPTYPE_NAMED, 'y') == '(?P<y>x)'")

    self.Try("BackRef('y') == '(?P=y)'")

    self.Try("Capture(Or('x', 'y', 'z'), 'a') == '(?P<a>x|y|z)'")
    self.Try("Capture(Or('ax', 'ay'), 'a') == '(?P<a>(?:ax)|(?:ay))'")
    self.Try("Capture(Or(('ax', 'ay')), 'a') == '(?P<a>(?:ax)|(?:ay))'")

    self.Try("Capture(Or('ax', 'ay')) == '((?:ax)|(?:ay))'")
    self.Try("Optional(Or('ax', 'ay')) == '(?:(?:ax)|(?:ay))?'")


class TestRegExpGrouper(base.TestCase):

  ALPHA1          = '[a-zA-Z]'
  ALPHA2          = ALPHA1+ALPHA1
  ALPHA3          = ALPHA1+ALPHA1+ALPHA1
  ALPHA4          = ALPHA1+ALPHA1+ALPHA1+ALPHA1

  DIGIT1          = '\d'
  DIGIT2          = DIGIT1+DIGIT1
  DIGIT12         = DIGIT1+DIGIT1+'?'
  DIGIT3          = DIGIT1+DIGIT1+DIGIT1
  DIGIT4          = DIGIT1+DIGIT1+DIGIT1+DIGIT1
  DECIMAL         = '\.\d+'

  SPACE           = '\s+'
  OPTSPACE        = '\s*'
  COMMA           = ',\s*'
  OPTCOMMA        = ',?\s*'

  PLUSMINUS       = '[+-]'
  TIMESEP         = '\s*[:\.]\s*'
  DATESEP         = '\s*[-/]\s*'
  OFFSET          = PLUSMINUS + DIGIT12 + ':?' + Optional(DIGIT2)
  LOOKAHEADSEP    = Group('[t\s:+=/\-\.]|$', GROUPTYPE_LOOK_AHEAD)

  TIME0           = (
      Capture(DIGIT12, 'hour') + TIMESEP + Capture(DIGIT12, 'minute') +
      Optional(TIMESEP + Capture(DIGIT12 + Optional(DECIMAL), 'second')) +
      OPTSPACE + Optional('a|pm?' + LOOKAHEADSEP, name='ampm') +
      Optional(SPACE + Capture(Or(r'z', ALPHA3, ALPHA4, OFFSET), 'tzname')) +
      LOOKAHEADSEP
  )

  def Run(self):
    pattern         = Grouper(self.TIME0)
    expected        = {
        'hour':       '5',
        'minute':     '06',
        'second':     '07.1234',
        'ampm':       'pm',
        'tzname':     'pdt',
    }
    actual          = pattern('5:06:07.1234 PM PDT'.lower())
    if actual != expected:
      print('actual:\n{}\nexpected:\n{}'.format(actual, expected))
    return actual == expected


class TestRegExpMultiGrouper(base.TestCase):

  DIGIT1          = '\d'
  DIGIT12         = DIGIT1+DIGIT1+'?'
  TIMESEP         = '\s*[:\.]\s*'
  SIMPLETIME0       = Capture(DIGIT12, 'hour') + TIMESEP + Capture(DIGIT12, 'minute')

  def Run(self):
    best            = MultiGrouper([self.SIMPLETIME0, TestRegExpGrouper.TIME0], MULTIGROUPERMODE_BEST)
    first           = MultiGrouper({'a': self.SIMPLETIME0, 'b': TestRegExpGrouper.TIME0}, MULTIGROUPERMODE_FIRST)
    timestr         = '5:06:07.1234 PM PDT'.lower()

    self.Try("best(timestr)[0] == 1")
    self.Try("len(best(timestr)[1]) == 5")

    self.Try("first(timestr)[0] == 'a'")
    self.Try("len(first(timestr)[1]) == 2")

