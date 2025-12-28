#!/opt/local/bin/python
''' ** At a Glance **

    use Define() to make an enum, like so:

        base.Enum.Define(('MYENUM', 'MyEnums'), (
            'Bare String',                        #  name
            ('1-Tuple', ),                        # (name, )
            ('2-Tuple', 'two'),                   # (name, tag)
            ('3-Tuple', 'three', 'THREE'),        # (name, tag, code)
            ('cat', '4-Tuple', 'four', 'FOUR'),   # (icon, name, tag, code)
            ('My None Option', None, 'MYNONE'),   # (name, tag, code)
        ))

    this results in the caller's module getting the following definitions:

        MyEnums               =  an instance of Enum

        MYENUM_BARE_STRING    =  an instance of Option, that is also the string 'B'
        MYENUM_1_TUPLE        =  an instance of Option, that is also the string '1'
        MYENUM_2_TUPLE        =  an instance of Option, that is also the string 'two'
        MYENUM_THREE          =  an instance of Option, that is also the string 'three'
        MYENUM_FOUR           =  an instance of Option, that is also the string 'four'
        MYENUM_MYNONE         =  an instance of Option, that tries to act like None

    ** Data Types **

      we work with enums where all the tags are strings, or all the tags are integers.  mixing
      types in the same enum is not allowed

      exception to this rule: in any enum, one single tag may be None


    ** Use in templates **

      the main advantage of Options is they are very easy to display.  continuing the example:

          MYENUM_FOUR.name    == '4-tuple'
          MYENUM_FOUR.icon    == 'cat'


    ** Adding to Existing Enums **

          MyEnum.Add('5th Option', 'five', 'FIVE')


    ** Extra Attributes **

      in the list of options, any entry may be a dict instead of a tuple, and extra attributes may be given

          { 'name': '5th Option', 'tag': 'five', 'codename': 'FIVE', 'extra': something }

      yields:

          MYENUM_FIVE.extra   == something


    ** Nested enums **

      see tests.py for a live example
'''

import base
import copy
import string


class Enum:

  globs             = None        # module that we create ourselves into

  name              = None        # 'MyEnum'
  appname           = None        # 'myapp'
  objname           = None        # 'myapp.MyEnum'
  codename          = None        # 'MyEnum'
  constname         = None        # 'MYENUM'

  parent            = None        # for nested Enums: our parent Option

  datatype          = None        # either str or int, depending on what kind of tags we hold
  noneoption        = None        # defaults to NoneOption
  stroption         = None        # defaults to StrOption
  intoption         = None        # defaults to IntOption

  by_name           = None        # dictionary of our options, by each option's name
  by_iname          = None        # dictionary of our options, by each option's name.lower()
  by_tag            = None        # dictionary of our options, by each option's tag

  @classmethod
  def Define(klass, names, optionlist):
    ''' creates a new Enum into some module's scope '''
    globs           = isinstance(names, Option) and names.enum.globs or base.utils.GetGlobalsOfCaller()
    enum            = klass(globs, names)
    for option in optionlist:
      option        = Option._FromDefinition(enum, option)
      enum._AddOption(option)
    return enum

  def Add(self, *args, **kwargs):
    ''' adds a new option to an enum; returns the option '''
    option          = Option._FromDefinition(self, args or kwargs)
    if args and kwargs:
      base.utils.SetAttrsSilently(option, **kwargs)
    self._AddOption(option)
    return option

  def DefineNested(self, option, suboptions):
    ''' adds a new option to an enum, and a whole sub-enum of options under it '''
    option          = Option._FromDefinition(self, option)
    self._AddOption(option)
    enum            = self.Define(option, suboptions)
    option.nesting  = enum
    if self.parent:
      if self.parent.children == None:
        self.parent.children      = []
      self.parent.children.append(enum)

  def Tag(self, x, silent=False):
    ''' searches by tag and name for an Option, raises if not successful; useful for sanitizing inputs '''
    if x == None:
      if None in self.by_tag:
        return self.by_tag[None]
    if x in self.by_tag:
      return self.by_tag[x]
    if isinstance(x, str):
      if x.isdigit() and self.datatype == int:
        y           = int(x)
        if y in self.by_tag:
          return self.by_tag[y]
      y             = x.lower()
      if y in self.by_iname:
        return self.by_iname[y]
      if y == 'none' and None in self.by_tag:
        return self.by_tag[None]
    if not silent:
      raise base.errors.EnumOptionNotFound(self.objname + ' does not contain ' + repr(x))

  def Name(self, x):
    ''' returns the name of Option x '''
    option          = self.Tag(x)
    return option and option.name

  def Icon(self, x):
    ''' returns the icon of Option x '''
    option          = self.Tag(x)
    return option and option.icon or None

  ###
  ## Django
  #

  def Choices(self, filter=None):
    # We once did a nice thing here to return the whole hierarchy, but it turns out
    # Django filters can't handle a hierarchy, and Django form widgets can only handle
    # a hierarchy to a depth of 2, so these days we'll just return a flat list here...
    filter          = filter or (lambda x: True)
    return [(x, x.name) for x in self.by_tag.values() if filter(x)]

  def MaxTagLength(self):
    absolute        = max((isinstance(x, str) and len(x) or 1) for x in self.by_tag)
    rounded         = 1
    while rounded < absolute:
      rounded       *= 2
    return rounded

  ###
  ## pythonic
  #

  def __init__(self, globs, names):
    self.globs      = globs
    self._UnderstandNames(names)
    self.by_name    = {}
    self.by_iname   = {}
    self.by_tag     = {}
    globs[self.codename]  = self
    base.registry.Register(self, self.objname)

  def __call__(self, x='_UNSET'):
    ''' calling our instance is a shortcut for calling .Tag() '''
    # while it is terribly convenient in Python to use our Enum instance as a sanitizer for Options within us,
    # template context tends to see we're callable and call us, and we need to still be us afterwards
    if x == '_UNSET':
      return self
    return self.Tag(x)

  def __repr__(self):
    return self.objname

  def __len__(self):
    return len(self.by_tag)

  def __contains__(self, x):
    option          = self.Tag(x, silent=True)
    return option is not None

  def __getitem__(self, x):
    ''' allows retrieval of any of our options by index (string enums only), tag, or name.
        on failure we return None instead of raising like .Tag() does
    '''
    # process Nones and NoneOptions the same
    if x == None:
      if None in self.by_tag:
        return self.by_tag.get(None)
      return

    # allow integer indexing into string enums
    if self.datatype == str:
      i             = None
      if isinstance(x, int):
        i           = x
      elif x.isdigit():
        i           = int(x)
      if i is not None and i >= 0 and i < len(self):
        byindex     = list(self)
        return byindex[i]

    # string ints are possibly ints
    if self.datatype == int and isinstance(x, str) and x.isdigit():
      y             = int(x)
      if y in self.by_tag:
        return self.by_tag[y]

    # common case
    if x in self.by_tag:
      return self.by_tag[x]
    if x in self.by_iname:
      return self.by_iname[x]

  def __iter__(self):
    ''' a string enum iterates in the order defined; an int enum iterates in order of the ints; None is always first '''
    if None in self.by_tag:
      yield self.by_tag[None]
    if self.datatype == int:
      keys          = list(self.by_tag.keys())
      keys.sort(key=lambda x: x or 0)
      for key in keys:
        if key != None:
          yield self.by_tag[key]
    elif self.datatype == str:
      for tag in self.by_tag:
        if tag != None:
          yield self.by_tag[tag]

  ###
  ## mechanical
  #

  def _AddOption(self, option, _skipstuff=False):
    ''' adds a fully-defined Option to the end of ourself '''
    if not _skipstuff:
      if self.datatype is None:
        if isinstance(option, str):
          self.datatype   = str
        elif isinstance(option, int):
          self.datatype   = int
        elif isinstance(option, NoneOption):
          pass
        else:
          raise base.errors.EnumDefinitionError('an Enum may hold only ints, strs, or a None', self.objname, option)
      elif not isinstance(option, self.datatype) and not isinstance(option, NoneOption):
        raise base.errors.EnumDefinitionError('the {} Enum {} may hold only {}s, or a single None, nothing else'.format(
            self.datatype.__name__, self.objname, self.datatype.__name__), option)

    tag                             = option.tag
    if tag in self.by_tag:
      raise base.errors.EnumDefinitionError('Enum option tag is not unique.', self.objname, option, self.by_tag[tag], tag)
    self.by_tag[tag]                = option

    iname                           = option.name.lower()
    if iname in self.by_iname:
      raise base.errors.EnumDefinitionError('Enum option name is not unique.', self.objname, option, self.by_iname[iname])
    self.by_name[option.name]       = option
    self.by_iname[iname]            = option

    if not _skipstuff:
      self.globs[option.constname]  = option

    if self.parent:
      self.parent.enum._AddOption(option, _skipstuff=True)

  def _UnderstandNames(self, names):
    ''' sets self.name, .appname, .objname, .codename, .constname, and maybe .parent '''
    if isinstance(names, Option):     # from DefineNested()
      self.parent   = names
      self.name     = self.parent.enum.name + ' ' + names.name
      self.appname  = self.parent.enum.appname
      self.codename = self.parent.enum.codename + base.utils.CollapseWhitespace(names.shortname.title(), to='')
      self.constname    = '_'.join(x for x in (self.parent.enum.constname, names.shortconst) if x)
    else:                             # from normal Define()
      if isinstance(names, str):
        self.name       = str(names)
        self.constname  = base.utils.Slugify(names, case=string.ascii_uppercase)
      else:
        self.name       = names[len(names) > 1 and 1 or 0]
        self.constname  = base.utils.Slugify(names[0], case=string.ascii_uppercase)
      self.codename = base.utils.CollapseWhitespace(self.name, to='')
    self.appname    = self.appname or (self.globs and self.globs.get('__package__')) or None
    self.objname    = self.appname and '.'.join((self.appname, self.codename)) or self.codename



class Option:
  ''' additional properties and methods on each constant defined or returned by an Enum '''

  enum              = None      # which Enum instance this option belongs to

  nesting           = None      # for nested Enums: the Enum instance that is equivalent to us
  children          = None      # for nested Enums: the Enums that live under us

  name              = None      # 'My Option'
  shortname         = None      #     same as name, except for nested enums, where name contains the parent's name too
  constname         = None      # 'MYENUM_MYOPTION'
  shortconst        = None      # 'MYOPTION'

  icon              = None      # icon that represents us

  def __repr__(self):
    if self.enum and self.constname:
      return '.'.join((x for x in (self.enum.appname, self.constname) if x))
    return base.utils.ObjectName(self)

  def __deepcopy__(self, memo):
    ''' Django loves to copy fields, and EnumFields with choices get deepcopy()-ed with impunity when rendering forms.
        the Enum itself tries to copy then, including its cached methods and properties, which can't pickle, and *boom!*
        i have found no good reason to need any actual copy of an Option, deep or shallow.  i will compromise and allow
        that if we get asked for a deepcopy then we will return a shallow copy instead.  less efficient than i want, but
        more safe than just returning self
    '''
    memo[id(self)]  = self
    return copy.copy(self)    # shallow-copy

  def __contains__(self, x):
    ''' string options "contain" ourself and our children, and also handle normal string comparison '''
    if self == x:
      return True
    try:
      y             = self.enum(x)
    except base.errors.EnumOptionNotFound:
      return isinstance(self, str) and isinstance(x, str) and str(x) in str(self)
    if self == y:
      return True
    return self.nesting and y in self.nesting

  @property
  def tag(self):
    ''' returns the atomic equivalent of our payload '''
    return self.enum.datatype(self)

  @property
  def index(self):
    ''' returns our position in our parent enum, which is often in the order options were defined;
        unreliable with nested enums, because options exist in multiple enums at once
    '''
    byindex         = list(self.enum)
    return byindex.index(self)

  @property
  def rank(self):
    ''' returns our position in our parent enum as a float between 0 and 1;
        unreliable with nested enums, because options exist in multiple enums at once
    '''
    count           = len(self.enum)
    if count-1:
      return self.index / (count-1)
    return 0.5

  @staticmethod
  def _FromDefinition(enum, definition):
    ''' given any of our definition formats, returns a fully defined Option '''
    if isinstance(definition, dict):
      return Option._FromDictDefinition(enum, definition)

    if isinstance(definition, str):
      name, tag, const, icon = definition, definition[0], None, None
    elif len(definition) == 1:
      name, tag, const, icon = definition[0], definition[0][0], None, None
    elif len(definition) == 2:
      name, tag, const, icon = definition[0], definition[1], None, None
    elif len(definition) == 3:
      name, tag, const, icon = definition[0], definition[1], definition[2], None
    elif len(definition) == 4:
      name, tag, const, icon = definition[1], definition[2], definition[3], definition[0]
    else:
      raise base.errors.EnumDefinitionError('Unable to understand an Enum option definition', definition)

    if tag is None:
      zelf          = (enum.noneoption or NoneOption)()
    elif isinstance(tag, str):
      if enum.parent:
        tag         = (enum.parent or '') + tag
      zelf          = (enum.stroption or StrOption)(tag)
    elif isinstance(tag, int):
      zelf          = (enum.intoption or IntOption)(tag)
    else:
      raise base.errors.EnumDefinitionError('an Enum may only contain tags that are strings, ints, or None', tag)

    const           = base.utils.Slugify(const or name, case=string.ascii_uppercase)

    shortname       = name
    if enum.parent:
      name          = ' '.join(x for x in (name, enum.parent.name) if x)

    zelf.enum       = enum
    zelf.name       = name
    zelf.shortname  = shortname
    zelf.constname  = '_'.join(x for x in (enum.constname, const) if x)
    zelf.shortconst = const
    zelf.icon       = icon

    return zelf

  @staticmethod
  def _FromDictDefinition(enum, definition):
    ''' given specifically a dictionary definition for an option, returns a fully defined Option '''
    name            = definition.get('name')
    tag             = definition.get('tag')
    code            = definition.get('code')
    icon            = definition.get('icon')
    if name and not 'tag' in definition:
      tag           = name[0]
    zelf            = Option._FromDefinition(enum, (icon, name, tag, code))
    for attr in definition:
      if attr not in ('name', 'tag', 'code', 'icon'):
        setattr(zelf, attr, definition[attr])
    return zelf



class StrOption(Option, str):
  pass

class IntOption(Option, int):

  def __str__(self):
    return str(self.tag)

class NoneOption(Option):

  @property
  def tag(self):
    return None

  def __eq__(self, other):
    return other == None

  def __lt__(self, other):
    return other != None

  def __hash__(self):
    return hash(None)

  def __bool__(self):
    return False

  def __str__(self):
    return str(self.tag)



Enum.Define(('TEST_OPTION', 'TestEnumOptions'), (
    'Bare String',                        #  name
    ('1-Tuple', ),                        # (name, )
    ('2-Tuple', 'two'),                   # (name, tag)
    ('3-Tuple', 'three', 'THREE'),        # (name, tag, code)
    ('cat', '4-Tuple', 'four', 'FOUR'),   # (icon, name, tag, code)
    ('My None Option', None, 'MYNONE'),   # (name, tag, code)
))

TestEnumOptions.Add(name='5th Option', tag='five', code='FIVE', hello='kitty')

TestEnumOptions.DefineNested(('Six', '6'), (
    ('Alpha',     'a'),
))

TestEnumOptionsSix.DefineNested(('Beta', 'b'), (
    {'name': 'Meow', 'hello': 'kitty'},
))

class TestEnumWithStrings(base.TestCase):
  ''' this test case stands as the official example of how Enum's interface should behave '''

  def Run(self):
    # Define()
    self.Try("TEST_OPTION_BARE_STRING in TestEnumOptions")
    self.Try("TEST_OPTION_1_TUPLE in TestEnumOptions")
    self.Try("TEST_OPTION_2_TUPLE in TestEnumOptions")
    self.Try("TEST_OPTION_THREE in TestEnumOptions")
    self.Try("TEST_OPTION_FOUR in TestEnumOptions")
    self.Try("TEST_OPTION_BARE_STRING == 'B'")
    self.Try("TEST_OPTION_1_TUPLE == '1'")
    self.Try("TEST_OPTION_2_TUPLE == 'two'")
    self.Try("TEST_OPTION_THREE == 'three'")
    self.Try("TEST_OPTION_FOUR == 'four'")
    self.Try("TEST_OPTION_BARE_STRING.name == 'Bare String'")
    self.Try("TEST_OPTION_1_TUPLE.name == '1-Tuple'")
    self.Try("TEST_OPTION_2_TUPLE.name == '2-Tuple'")
    self.Try("TEST_OPTION_THREE.name == '3-Tuple'")
    self.Try("TEST_OPTION_FOUR.name == '4-Tuple'")
    self.Try("TEST_OPTION_FOUR.icon == 'cat'")
    self.Try("TestEnumOptions.Tag('4-tUpLe') == TEST_OPTION_FOUR")

    # Add()
    self.Try("TEST_OPTION_FIVE in TestEnumOptions")
    self.Try("TEST_OPTION_FIVE == 'five'")
    self.Try("TEST_OPTION_FIVE.name == '5th Option'")
    self.Try("TEST_OPTION_FIVE.hello == 'kitty'")

    ## DefineNested()
    self.Try("TEST_OPTION_SIX in TestEnumOptions")
    self.Try("TEST_OPTION_SIX == '6'")
    self.Try("TEST_OPTION_SIX.name == 'Six'")
    self.Try("TEST_OPTION_SIX_ALPHA in TestEnumOptions")
    self.Try("TEST_OPTION_SIX_ALPHA in TestEnumOptionsSix")
    self.Try("TEST_OPTION_SIX_ALPHA == '6a'")
    self.Try("TEST_OPTION_SIX_ALPHA.name == 'Alpha Six'")
    self.Try("TEST_OPTION_SIX_BETA in TestEnumOptions")
    self.Try("TEST_OPTION_SIX_BETA in TestEnumOptionsSix")
    self.Try("TEST_OPTION_SIX_BETA == '6b'")
    self.Try("TEST_OPTION_SIX_BETA.name == 'Beta Six'")
    self.Try("TEST_OPTION_SIX_BETA_MEOW in TestEnumOptions")
    self.Try("TEST_OPTION_SIX_BETA_MEOW in TestEnumOptionsSix")
    self.Try("TEST_OPTION_SIX_BETA_MEOW in TestEnumOptionsSixBeta")
    self.Try("TEST_OPTION_SIX_BETA_MEOW == '6bM'")
    self.Try("TEST_OPTION_SIX_BETA_MEOW.name == 'Meow Beta Six'")
    self.Try("TEST_OPTION_SIX_BETA_MEOW.hello == 'kitty'")
    self.Try("TestEnumOptions.Tag('Meow Beta Six') == TEST_OPTION_SIX_BETA_MEOW")

    # Options should allow "in" testing as well
    self.Try("TEST_OPTION_SIX_BETA_MEOW in TEST_OPTION_SIX_BETA_MEOW")
    self.Try("TEST_OPTION_SIX_BETA_MEOW in TEST_OPTION_SIX_BETA")
    self.Try("TEST_OPTION_SIX_BETA_MEOW in TEST_OPTION_SIX")
    self.Try("TEST_OPTION_SIX_BETA_MEOW not in TEST_OPTION_SIX_ALPHA")
    self.Try("TEST_OPTION_SIX_ALPHA in TEST_OPTION_SIX")
    self.Try("'a' not in TEST_OPTION_SIX_BETA_MEOW")
    self.Try("'b' in TEST_OPTION_SIX_BETA_MEOW")

    # .index and .rank
    self.Try("TEST_OPTION_FOUR.index == 5")
    self.Try("TEST_OPTION_FOUR.rank == 0.5")
    self.Try("TEST_OPTION_SIX.index == 7")
    self.Try("TEST_OPTION_SIX.rank == 0.7")
    self.Try("TEST_OPTION_SIX_BETA.index == 1")
    self.Try("TEST_OPTION_SIX_BETA.rank == 0.5")
    self.Try("TEST_OPTION_SIX_BETA_MEOW.index == 0")
    self.Try("TEST_OPTION_SIX_BETA_MEOW.rank == 0.5")

    # None
    self.Try("not TEST_OPTION_MYNONE")
    self.Try("TEST_OPTION_MYNONE == None")
    self.Try("TEST_OPTION_MYNONE in TestEnumOptions")
    self.Try("None in TestEnumOptions")
    self.Try("TEST_OPTION_MYNONE.index == 0")
    self.Try("TEST_OPTION_MYNONE.rank == 0")

    # registry
    self.Try("base.registry.Get('base.TestEnumOptions')")
    self.Try("base.registry.Get('base.TestEnumOptionsSix')")
    self.Try("base.registry.Get('base.TestEnumOptionsSixBeta')")



Enum.Define(('TEST_INT_ENUM', 'TestIntEnum'), (
    ('life, the universe, and everything',    42,     'FORTYTWO'),
    ('high-Z',                              None,     'NONE'),
    ('the number of thy counting',             3,     'THREE'),
))

class TestEnumWithInts(base.TestCase):
  ''' tests that our integer enums come out in sorted order '''

  def Run(self):
    self.Try("list(TestIntEnum)            == [None, 3, 42]")

    self.Try("TEST_INT_ENUM_NONE           == None")
    self.Try("TEST_INT_ENUM_THREE          ==    3")
    self.Try("TEST_INT_ENUM_FORTYTWO       ==   42")

    self.Try("TEST_INT_ENUM_NONE.rank      == 0.0")
    self.Try("TEST_INT_ENUM_THREE.rank     == 0.5")
    self.Try("TEST_INT_ENUM_FORTYTWO.rank  == 1.0")
