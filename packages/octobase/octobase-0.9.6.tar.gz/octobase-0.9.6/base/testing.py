#!/usr/bin/env python3

import argparse
import base
import fnmatch
import functools
import logging
import math


NAME_WIDTH          = 42


class TestCase(metaclass=base.Registry.AutoRegister, skip=1):
  ''' One single test case, though you may log as many test results as you want within it. '''

  # specify a TestContext you want to your test case to be run within
  TEST_CONTEXT      = None

  # give a list/tuple of method names on this class that you want us to be able to call
  COMMANDS          = ('Run', )

  @property
  def context(self):
    ''' returns the finest-grain context we're inside '''
    return self.contexts and self.contexts[-1] or None

  def Run(self):
    ''' do your actual testing by overriding this method.  in order to pass you must return None
        or something that's boolean True.  returning a direct boolean False will fail
    '''
    return True

  def LogResult(self, passed, message=None, namewidth=NAME_WIDTH):
    ''' you may also fail by calling LogResult(False) at least once during your Run() '''
    self.results    = self.results + 1
    if not passed:
      self.fails    = self.fails + 1
    if message:
      name          = base.utils.PadString(base.utils.ObjectName(self) + ':', namewidth)
      message       = message and ' '.join((name, str(message))) or name
      base.utils.Log(passed and ' PASS ' or '!FAIL ', message)

  def Try(self, expression):
    ''' given a pythonic expression string that should eval() to True, we try it,
        and call LogResult with what happens
    '''
    if not expression:
      return
    globs           = base.utils.GetGlobalsOfCaller()
    locs            = base.utils.GetLocalsOfCaller()
    try:
      passed        = bool(eval(expression, globs, locs))
    except Exception as e:
      passed        = False
      expression    += '  # ' + base.utils.ClassName(e)
    self.LogResult(passed, expression)
    return passed

  def TryAndExpectException(self, expression, expected):
    ''' like Try(), but only passes if the expected exception is raised '''
    if not expression:
      return
    globs           = base.utils.GetGlobalsOfCaller()
    locs            = base.utils.GetLocalsOfCaller()
    try:
      eval(expression, globs, locs)
      passed        = False
    except Exception as e:
      passed        = base.utils.IsA(e, expected)
      expression    += '  # ' + base.utils.ClassName(e)
    self.LogResult(passed, expression)
    return passed

  ###
  ## mechanical
  #

  def __init__(self, runner=None, contexts=None):
    self.runner     = runner
    self.contexts   = contexts
    self.results    = 0
    self.fails      = 0

  def GetMethodForCommand(self, command):
    ''' returns the method on ourself for the command that's requested; probably "Run" '''
    things          = self.contexts + [self]
    for thing in things[::-1]:
      commandlist   = thing.COMMANDS
      if not commandlist:
        commandlist = []
      elif isinstance(commandlist, str):
        commandlist = [commandlist]
      if command in commandlist:
        if thing != self:
          method    = functools.partial(getattr(type(thing), command), self)
        else:
          method    = getattr(thing, command)
        return method



class TestContext(metaclass=base.Registry.AutoRegister, skip=1):
  ''' An environment that your test case needs to run within, can be shared between cases.
      Each test case can access the context it's in through a self.context property.
  '''

  # give a list/tuple of method names on this class that you want us to be able to call
  COMMANDS          = ('Interact',)

  def __init__(self):
    self.next       = None

  def __enter__(self):
    self.next       = self.SetUp()
    return self.next or self

  def __exit__(self, _1, exception, _2):
    self.CleanUp()
    if self.next:
      self.next.__exit__(_1, exception, _2)
    elif exception:
      raise

  def SetUp(self):
    ''' Load whatever resources your test case needs.  You may return a context manager object if desired. '''

  def CleanUp(self):
    ''' Release any resources that need manual cleanup. '''

  def Interact(self, **kwargs):
    ''' opens an interactive console within the context '''
    base.utils.GoInteractive(**kwargs)



class TestModuleContext(TestContext, skip=1):
  ''' If a TestModuleContext subclass exists in the same module as any of your test cases, it will
      be used to wrap all the test cases in that module.
  '''



class TestRunner:
  ''' Engine that calls TestCases for you. '''

  def AddOnlySkip(self, only, skip):
    ''' adds additional only or skip patterns to our setup '''
    self.only       = ((self.only or []) + (only and [x.strip() for x in only.split(',') if x.strip()] or [])) or None
    self.skip       = ((self.skip or []) + (skip and [x.strip() for x in skip.split(',') if x.strip()] or [])) or None

  def RunFromCommandLine(self):

    parser          = argparse.ArgumentParser()

    parser.add_argument('command', nargs='?', default='',
        help=(
            'do something special besides just running a test.  the only available global command '
            'is "list", however individual test cases or test contexts may accept additional '
            'commands.  use "list" to see what commands any test will take'
        ))

    parser.add_argument('--only', metavar='LIST',
        help='comma-delimited list of tests to run; wildcards are allowed')
    parser.add_argument('--skip', metavar='LIST',
        help='comma-delimited list of tests to not run; wildcards are allowed')

    args            = parser.parse_args()
    self.AddOnlySkip(args.only, args.skip)

    self.Run(args.command)

  def Run(self, command):
    ''' Runs every registered TestCase within the proper TestContexts. '''
    if isinstance(command, str):
      command       = base.utils.Slugify(command or 'run').title()
      if command in self.COMMANDS:
        return getattr(self, command)()

    self._RunContextStacks(self._GetTestCasesByContext(), command)

    if self.cases:
      status        = self.fails and 'FAILED' or 'PASSED'
    elif not self.results and not self.fails:
      base.utils.Log('EMPTY', 'No test cases were run.')
      return
    else:
      status        = 'CONFUSED'

    base.utils.Log(status, '{} TestCase{} run, {} result{} logged, {} failure{}'.format(
        self.cases,   self.cases    != 1 and 's' or '',
        self.results, self.results  != 1 and 's' or '',
        self.fails,   self.fails    != 1 and 's' or ''
    ))


  ###
  ## Special commands besides just running tests
  #

  COMMANDS          = ('List',)

  def List(self, namewidth=NAME_WIDTH):
    ''' Lists to console all available TestCases and the TestContexts they run within. '''
    print(base.utils.PadString('Name', namewidth, align='^') + 'Commands')

    def FormatCommands(x):
      if not x:
        return
      if isinstance(x, str):
        if x == 'Run':
          return
        return x
      return '  '.join(y for y in x if y != 'Run')

    for modcon, subthings in self._GetTestCasesByContext().items():
      name          = (modcon and base.utils.ObjectName(modcon) or 'No Module Context')
      commands      = modcon and FormatCommands(modcon.COMMANDS) or ''
      print(base.utils.PadString('  ' + name, namewidth) + commands)
      for context, caselist in subthings.items():
        name        = (context and base.utils.ObjectName(context) or 'No Test Context')
        commands    = context and FormatCommands(context.COMMANDS) or ''
        print(base.utils.PadString('    ' + name, namewidth) + commands)
        for case in caselist:
          name      = base.utils.ObjectName(case)
          commands  = FormatCommands(case.COMMANDS) or ''
          print(base.utils.PadString('      ' + name, namewidth) + commands)


  ###
  ## Mechanics
  #

  @staticmethod
  def _MatchGlobList(thing, globlist):
    charm           = base.utils.ObjectName(thing).lower()
    strange         = base.utils.ClassName(thing).lower()
    globlist        = [x.lower() for x in globlist]
    if charm in globlist or thing in globlist:
      return True
    for pattern in globlist:
      if fnmatch.fnmatch(charm, pattern):
        return True
      if fnmatch.fnmatch(strange, pattern):
        return True

  def __init__(self, basetest=False, **kwargs):
    self.cases      = 0
    self.results    = 0
    self.fails      = 0
    self.only       = None
    self.skip       = None
    self.command    = None
    base.utils.SetAttrs(self, **kwargs)

    if not basetest:
      self.AddOnlySkip(None, 'base.*')
      self.AddOnlySkip(None, 'rightdown.*')

  def _GetTestCasesByContext(self):
    ''' Returns { module context: { test context: [ test case, ... ] } }, where None is a valid key '''
    def first(iter):
      if iter:
        for x in iter:
          return x

    def GetModuleContext(testcase):
      if testcase:
        for modcon in base.registry.GetAll(TestModuleContext):
          if modcon.__module__ == testcase.__module__:
            return modcon

    by_module       = {}
    for testcase in base.registry.GetAll(TestCase):
      if not self.only or self._MatchGlobList(testcase, self.only):
        if not self.skip or not self._MatchGlobList(testcase, self.skip):
          by_module.setdefault(GetModuleContext(testcase), {}).setdefault(testcase.TEST_CONTEXT, []).append(testcase)

    return by_module

  def _RunContextStacks(self, thing, command, contexts=[]):
    if isinstance(thing, dict):
      # recurse through two levels of dictionary
      for context, subthing in thing.items():
        if context:
          # we have a module context, recurse with it
          if isinstance(context, type):
            context   = context()
          with context:
            contexts  = list(x for x in contexts)
            contexts.append(context)
            self._RunContextStacks(subthing, command, contexts)
        else:
          # no module context, recurse without
          self._RunContextStacks(subthing, command, contexts)
    else:
      # land finally on a list of test cases
      for testcase in thing:
        self._RunTestCase(testcase, command, contexts)

  def _RunTestCase(self, testclass, command, contexts):
    ''' Runs one single TestCase subclass, increments our counters for the result. '''
    self.cases      = self.cases + 1
    testcase        = None
    success         = False
    result          = None
    name            = base.utils.ObjectName(testclass)

    try:
      base.utils.Log(base.utils.PadString(command.upper(), 6), name)
      testcase      = testclass(runner=self, contexts=contexts)
      method        = testcase.GetMethodForCommand(command)
      if method:
        result      = method()
        success     = result != False
      else:
        base.utils.Log('TEST', 'Command "{}" is meaningless for test case {}'.format(command, name))
        success     = False
    except Exception as e:
      base.utils.Log('TEST', 'Uncaught Exception: ' + str(e), level=logging.WARN)
      self.fails    = self.fails + 1
      raise

    self.results    += 1 + testcase.results
    if not success:
      self.fails    += 1
    self.fails      += testcase.fails
    if testcase.fails:
      success       = False

    if result and isinstance(result, str) and result.strip():
      base.utils.Log(success and 'PASS  ' or 'FAIL  ', name + ': ' + result)
    else:
      base.utils.Log(success and 'PASS  ' or 'FAIL  ', name)
