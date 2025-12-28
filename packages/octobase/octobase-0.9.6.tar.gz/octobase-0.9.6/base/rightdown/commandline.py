#!/opt/local/bin/python
'''
a command-line tool to process rightdown documents

often i keep an alias defined in my .profile like thus:

    alias rd='${OCTOCODE}/../octobase/base/rightdown/commandline.py'

(which of course means we must maintain executable bit on this file)
'''

import argparse
import base
import os
import sys

from base                   import rightdown
from base.rightdown.enums   import *


class RightDownCommandLineTool:

  @classmethod
  def Run(klass, timer=None):
    ''' transforms a RightDown document into HTML '''
    zelf            = klass()
    timer           = timer or base.utils.Stopwatch('RightDown')
    zelf.ProcessArgs()
    timer.Lap('command line arguments')
    zelf.ConfigureThings()
    timer.Lap('warming the parser')
    zelf.MoveInputToOutput(timer)
    if zelf.time:
      timer.LogAllLaps()
    print(zelf.printed or '(no results)')

  def __init__(self):
    self.filepath   = None
    self.output     = None
    self.options    = None
    self.parser     = None
    self.printer    = None
    self.printed    = None
    self.time       = False

  def MoveInputToOutput(self, timer):
    # read input
    if self.filepath == '-':
      input         = sys.stdin.read()
    else:
      if not os.path.exists(self.filepath):
        sys.stderr.write('Can not find the input file: ' + self.filepath + '\n')
        sys.exit(1)
      with open(self.filepath, 'rt') as file:
        input       = file.read()
    timer.Lap('reading input')

    # parse
    rd              = self.parser.Parse(input)
    timer.Lap('parsing input')

    # print
    self.printed    = self.printer.Print(rd)
    timer.Lap('formatting output')

  def ConfigureThings(self):
    ''' sets up our parser and printer '''
    self.parser     = rightdown.parser.Parser()
    self.printer    = rightdown.printers.PrinterForMode(self.output)
    for thing in (self.parser, self.printer):
      for attr, value in self.options.items():
        if hasattr(thing, attr):
          setattr(thing, attr, value)

  def ProcessArgs(self):
    ''' gently mauls the pythonic argparse library until it does what we want '''
    if self.options:
      return

    class HelpFormatter(argparse.HelpFormatter):
      ''' allows us to use a wider-than-normal column width in our help text '''
      def __init__(self, *args, max_help_position=24, **kwargs):
        super().__init__(*args, max_help_position=36, **kwargs)

    # this is the main argument parser
    args0           = argparse.ArgumentParser(
        description = self.Run.__doc__,
        epilog      = ('some options will be set automatically, or rendered irrelevant, by each '
            'different output format'),
        usage       = '%(prog)s [[options]] FILEPATH [OUTPUT]',
        formatter_class = HelpFormatter,
    )
    version         = 'octobase v' + str(base.VERSION)
    args0.add_argument('--version',  action='version', version=version)

    # this one lets us tell apart options that were set from their defaults
    args1           = argparse.ArgumentParser()

    # add our positional args
    args1.add_argument('filepath')
    args0.add_argument('filepath', metavar='FILEPATH',
        help='path to the file to read; use a single dash - to read stdin')

    args1.add_argument('output', nargs='?')
    args0.add_argument('output', nargs='?', metavar='OUTPUT',
        default=PRINTMODE_HTML, type=PrintModes,
        help=(
            'desired output format; ' +
            self._HelpTextForEnum(PRINTMODE_HTML, PrintModes)))

    args1.add_argument('--time', action=argparse.BooleanOptionalAction)
    args0.add_argument('--time', action=argparse.BooleanOptionalAction, default=False,
        help='report how much wall time is taken by the tool')

    # add all the many parser and printer options
    seen            = set()
    self._SetUpArgParseForThing(args0, args1, seen, rightdown.parser.Parser)
    self._SetUpArgParseForThing(args0, args1, seen, rightdown.printers.Printer)
    self._SetUpArgParseForThing(args0, args1, seen, rightdown.printers.TextPrinter)
    self._SetUpArgParseForThing(args0, args1, seen, rightdown.printers.HtmlPrinter)
    self._SetUpArgParseForThing(args0, args1, seen, rightdown.printers.DebugPrinter)

    # parse the args with both
    withdefaults    = args0.parse_args()
    nodefaults      = args1.parse_args()

    self.filepath   = withdefaults.filepath
    self.output     = withdefaults.output
    self.time       = withdefaults.time

    # include in our final options only flags which were explicitly set
    self.options    = {}
    for attr in seen:
      val0          = vars(withdefaults).get(attr)
      val1          = vars(nodefaults).get(attr)
      if val1 is not None:
        self.options[attr] = val0

  def _HelpTextForEnum(self, default, enum):
    default         = default and ('default=\'' + default.name + '\'') or ''
    choices         = 'choices=(' + ', '.join(x.name for x in enum) + ')'
    return '; '.join(x for x in (default, choices) if x)

  def _SetUpArgParseForThing(self, args0, args1, seen, thing):
    ''' adds the Thing's attributes as flags to our argument parsers '''
    for attr in thing.attributes:
      if attr in seen:
        continue
      seen.add(attr)
      help0         = '(' + base.utils.ClassName(thing) + ')'
      default       = getattr(thing, attr)
      if isinstance(default, base.Option):
        help1       = help0 + ' ' + self._HelpTextForEnum(default, default.enum)
        args1.add_argument('--' + attr)
        args0.add_argument('--' + attr,
            default=default, help=help1, metavar=default.enum.constname, type=default.enum)
      elif isinstance(default, bool):
        help1       = help0 + ' default: --' + (default and attr or ('no-' + attr))
        args1.add_argument('--' + attr, action=argparse.BooleanOptionalAction)
        args0.add_argument('--' + attr, action=argparse.BooleanOptionalAction, default=default, help=help1)
      elif isinstance(default, int):
        help1       = help0 + ' default: ' + str(default)
        args1.add_argument('--' + attr)
        args0.add_argument('--' + attr, default=default, metavar='INT', type=int, help=help1)
      elif isinstance(default, list) or isinstance(default, tuple):
        default     = ','.join(default)
        help1       = help0 + ' default: ' + default
        args1.add_argument('--' + attr)
        args0.add_argument('--' + attr, default=default, metavar='LIST', help=help1)

if __name__ == '__main__':
  RightDownCommandLineTool.Run()
