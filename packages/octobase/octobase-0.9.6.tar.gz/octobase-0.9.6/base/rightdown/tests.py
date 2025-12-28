#!/usr/bin/env python3

import base
import itertools
import logging
import os

from base                   import rightdown
from base.rightdown.enums   import *


###
## test context and base class
#


base.Enum.Define(('PATH', 'TestDataPaths'), ('INPUTS', 'OUTPUTS'))


class ReferenceDocumentContext(base.TestContext):
  ''' common code for our tests that want to use reference files from our testdata '''

  def __init__(self, source='input.md', expect=None, **kwargs):
    super().__init__(**kwargs)
    self.source             = []
    self.source_filename    = source
    self.expected           = []
    self.expected_filename  = expect

  def TestDataPath(self, whichpath):
    if whichpath == PATH_INPUTS:
      return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'documentation/rightdown/examples/')
    if whichpath == PATH_OUTPUTS:
      return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'documentation/rightdown/results/')

  def SetUp(self):
    dirpath       = self.TestDataPath(PATH_INPUTS)
    filepath      = dirpath + self.source_filename
    if os.path.exists(filepath):
      with open(filepath, 'rt') as file:
        text      = file.read().rstrip()
        text      = text.replace('SQUIGUILGMAS ', 'SQUIGUILGMAS  \n')
        text      = text.replace('SQUIGUILGMAS\n', 'SQUIGUILGMAS  \n')
        self.source  = [x.rstrip('\n') for x in text.split('\n')]
    else:
      base.utils.Log('TEST', 'file not found: {}'.format(filepath), level=logging.WARN)
    if self.expected_filename:
      dirpath     = self.TestDataPath(PATH_OUTPUTS)
      filepath    = dirpath + self.expected_filename
      if os.path.exists(filepath):
        with open(filepath, 'rt') as file:
          text    = file.read().rstrip()
          self.expected = [x.rstrip('\n') for x in text.split('\n')]
      else:
        base.utils.Log('TEST', 'file not found: {}'.format(filepath), level=logging.WARN)


class ReferenceDocumentTestCase(base.TestCase, skip=1):
  ''' common code for our tests that want to use reference files from our testdata '''

  COMMANDS          = ('Run', 'Compare', 'Write', 'Dump')

  TEST_PRINTER      = PRINTMODE_DEBUG
  TERMINUS          = None

  def Compare(self):
    return self.Run(command='compare')

  def Write(self):
    return self.Run(command='write')

  def Dump(self):
    return self.Run(command='dump')

  def Run(self, **kwargs):
    ''' runs the rightdown engine over the input file, then compares Results() with the expected results '''
    source          = '\n'.join(self.context.source)
    rd              = rightdown.RightDown.From(source, stop_after_stage=self.TERMINUS)
    results         = self.Results(rd)
    return self.CompareWithReference(results, **kwargs)

  def Results(self, rd):
    ''' hook allowing a test case to format the specific results it's trying to test '''
    printer         = rightdown.printers.PrinterForMode(self.TEST_PRINTER)
    return printer.Print(rd)

  def CompareWithReference(self, actual, command='run'):
    ''' Given a test result, compares it to the expected list of strings and logs errors on mismatch '''

    if not actual:
      actual        = []
    elif isinstance(actual, str):
      actual        = actual.split('\n')

    if command in ('write', 'dump'):
      return self._Write(actual, command)

    expected        = self.context.expected or []
    errors          = 0
    for exp, act in itertools.zip_longest(expected, actual):
      if exp != act:
        errors      = errors + 1

    if errors:
      self.LogResult(False, '{} line{}, {} error{}'.format(
          len(actual), len(actual) != 1 and 's' or '', errors, errors != 1 and 's' or '', ))
      if command == 'compare':
        minwidth    = 16
        maxwidth    = rightdown.printers.DebugPrinter.truncate_width
        width       = min(maxwidth, max(base.utils.Flatten(minwidth, [len(x) for x in expected], [len(x) for x in actual])))
        dashinglie  = '-'*width
        lines       = [
            '+-{dashinglie}-+----+-{dashinglie}-+'.format(dashinglie=dashinglie),
            '| {:^{width}s} | == | {:^{width}s} |'.format('Expected', 'Actual', width=width),
            '+-{dashinglie}:+:--:+:{dashinglie}-+'.format(dashinglie=dashinglie),
        ]
        for exp, act in itertools.zip_longest(expected, actual, fillvalue='(None)'):
          ex        = (len(exp) > maxwidth) and (exp[:maxwidth-1] + '…') or exp
          ac        = (len(act) > maxwidth) and (act[:maxwidth-1] + '…') or act
          lines.append('| {:{width}s} | {} | {:{width}s} |'.format(ex, exp == act and '  ' or '!=', ac, width=width))
        lines.append('+-{dashinglie}-+----+-{dashinglie}-+'.format(dashinglie=dashinglie))
        base.utils.Log('DETAIL', '\n  ' + '\n  '.join(lines))
      else:
        print('   - run this test with the command "dump" to see the actual output')
        print('   - run this test with the command "compare" to see a line-by-line compare with expected output')
    else:
      self.LogResult(True, '{} line{}'.format(len(actual), len(actual) != 1 and 's' or ''))

    return not errors

  def _Write(self, actual, command):
    ''' overwrite our expected file with the actual results we got '''
    output          = '\n'.join(actual)
    if command == 'dump':
      print('\n'.join(x for x in ('```', output, '```') if x))
      return

    filepath        = self.context.TestDataPath(PATH_OUTPUTS) + self.context.expected_filename
    print('About to overwrite ' + filepath +
        ' with the {} line{} of results from this test'.format(len(actual), len(actual) != 1 and 's' or ''))
    if not base.utils.AskStdInForPermission('Is this okay (y/N)? '):
      self.LogResult(False, 'Write command aborted')
      return

    with open(filepath, 'wt') as file:
      file.write(output)

    self.LogResult(True, '{} chars written'.format(len(output)))


###
## tests that run a document through parse and print
#


class TestSmol(ReferenceDocumentTestCase):
  ''' tests a one-line document '''

  TEST_CONTEXT      = ReferenceDocumentContext(source='smol.md', expect='smol.html')

  def Results(self, rd):
    return rightdown.printers.HtmlPrinter().Print(rd)


class TestParagraphs(ReferenceDocumentTestCase):
  ''' tests paragraphs and whitespace '''

  TEST_CONTEXT      = ReferenceDocumentContext(source='paragraphs.md', expect='paragraphs.html')
  TEST_PRINTER      = PRINTMODE_HTML


class TestFragmenting(ReferenceDocumentTestCase):
  ''' tests fragmenting, comments, and fenced code blocks '''

  TEST_CONTEXT      = ReferenceDocumentContext(source='fragmenting.md', expect='fragmenting.txt')
  TEST_PRINTER      = PRINTMODE_DEBUG


class TestSubblocks(ReferenceDocumentTestCase):
  ''' tests blocks that contain sub-blocks '''

  TEST_CONTEXT      = ReferenceDocumentContext(source='subblocks.md', expect='subblocks.html')
  TEST_PRINTER      = PRINTMODE_HTML


class TestInline(ReferenceDocumentTestCase):
  ''' tests inline formatting '''

  TEST_CONTEXT      = ReferenceDocumentContext(source='inline.md', expect='inline.html')
  TEST_PRINTER      = PRINTMODE_HTML


###
## tests around extracting structured content
#

class TestMetadata(ReferenceDocumentTestCase):
  ''' tests metadata extraction '''

  TEST_CONTEXT      = ReferenceDocumentContext(source='metadata.md', expect='metadata.txt')

  def Results(self, rd):
    results         = []
    attrs           = list(rd.metadata)
    attrs.sort()
    for attr in attrs:
      val           = rd.metadata[attr]
      results.append(base.utils.PadString(attr + ':', rightdown.printers.DebugPrinter.token_width) + str(val))
    return results


class TestLinks(ReferenceDocumentTestCase):
  ''' tests link extraction '''

  TEST_CONTEXT      = ReferenceDocumentContext(source='links.md', expect='links.txt')

  def Results(self, rd):
    return [x.debug or '' for x in rd.Links() or []]


###
## other things
#


class TestTokenTypes(base.TestCase):
  ''' ensures there's no overlaps between our tokentype enum tags '''

  def Run(self):
    linetypes       = set(x.tag for x in LineTypes)
    blocktypes      = set(x.tag for x in BlockTypes)
    sniptypes       = set(x.tag for x in SnipTypes)
    overlaps        = (linetypes & blocktypes) | (blocktypes & sniptypes) | (linetypes & sniptypes)
    if overlaps:
      self.LogResult(False, 'overlapping tags: ' + ', '.join(overlaps))
    for tag in linetypes | blocktypes:
      L             = rightdown.parser.TokenList.TOKENLEN
      if len(tag) != L or tag[L-1] != ',' or ',' in tag[:L-1]:
        self.LogResult(False, 'bad tag: ' + tag)





# class TestReference(ReferenceDocumentTestCase):
#   ''' tests that our input.md fully turns into reference.md '''
#
#   TEST_CONTEXT      = ReferenceDocumentContext(expect='reference.md')
#
#   def Results(self, rd):
#     return rd.Text()
#
#
#
# class TestIdempotence(ReferenceDocumentTestCase):
#   ''' tests that our reference.md turns into itself '''
#
#   TEST_CONTEXT      = ReferenceDocumentContext(source='reference.md', expect='reference.md')
#
#   def Results(self, rd):
#     return rd.Text()

