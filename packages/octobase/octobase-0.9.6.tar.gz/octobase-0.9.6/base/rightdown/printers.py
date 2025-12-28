#!/opt/local/bin/python

import base
import html

from base                   import rightdown
from base.regexp            import *
from base.rightdown.enums   import *
from base.rightdown.tokens  import *


def PrinterForMode(printmode):
  ''' returns the right printer for one of our PrintModes enums '''
  if printmode == PRINTMODE_NAKED:
    return Printer()
  if printmode == PRINTMODE_TEXT:
    return TextPrinter()
  if printmode == PRINTMODE_HTML:
    return HtmlPrinter()
  if printmode == PRINTMODE_DEBUG:
    return DebugPrinter()



class Printer(base.Thing):
  ''' default options cause us to emit naked text with neither formatting nor markup '''

  # Copy()-ing a Printer means copying all our settings
  ATTRIBUTES        = [
      'markup', 'formatting',
      'metadata', 'empties', 'pass_comments', 'pass_html', 'pass_templates', 'force_fence', 'double_space',
      'block_indent', 'unfenced_indent',
      #'wrap_width', 'wrap_indent',
      'stop_after_stage',
  ]

  # should we emit markup?
  markup                      = False

  # should we emit formatting text?
  formatting                  = False

  # Should we emit metadata?
  metadata                    = False

  # Should we emit empty blocks?
  empties                     = False

  # Should we pass through raw html, comments, and template syntax?
  pass_html                   = False
  pass_comments               = False
  pass_templates              = False

  # should we force indented code blocks to turn into fenced code blocks?
  force_fence                 = False

  # should we emit blank lines between blocks?
  double_space                = False

  # How many spaces to indent nested blocks?
  block_indent                = 0

  # How many spaces to indent un-fenced code blocks?
  unfenced_indent             = 4

  # How many characters to a line before we wrap?  0 to disable wrapping
  #wrap_width                  = 90

  # How many spaces to indent a wrapped line's continuations?
  #wrap_indent                 = 2

  # this is only meaningful if it's set to STAGE_IMPRINTS
  stop_after_stage            = STAGE_DONE

  # this affects whether this printer emits rich characters or text equivalents
  _test_substitution_column   = 1

  def Print(self, rd):
    ''' distills a RightDown instance to a single string '''
    if isinstance(rd, rightdown.tokens.Snip):
      imprints      = self._NormalizeImprints(rd.PrintOpen(self, None, None)) + self._NormalizeImprints(rd.PrintClose(self, None, None))
    elif isinstance(rd, rightdown.tokens.Block):
      imprints      = rd.Walk(self._WalkOpen, self._WalkClose) or []
    else:
      raise rightdown.errors.UnPrintable(rd)

    if self.stop_after_stage == STAGE_IMPRINTS:
      return ''.join(x.debug + '\n' for x in imprints).rstrip()

    filtered        = self.FilterImprints(imprints)

    if self.stop_after_stage == STAGE_FILTERED:
      return ''.join(x.debug + '\n' for x in filtered).rstrip()

    return self.MergeImprints(filtered).rstrip()

  ###
  ## callbacks
  #

  def MuteUntilClose(self, token):
    ''' causes us to suppress all output until the given token is in the rear view mirror '''
    self._muted     = token

  def PrefixUntilClose(self, token, imprint):
    ''' the given imprint should precede any line of output until the given token is closing '''
    if self._stack[-1][0] != token:
      raise rightdown.errors.TreeWalkBroken(list(repr(x[0]) for x in self._stack), repr(token))
    if self._stack[-1][1]:
      raise rightdown.errors.OnePrefixPerToken(token)
    self._stack[-1] = (token, imprint)

  ###
  ## child class hooks
  #

  def HandleTokenOpen(self, token, depth, first, last):
    ''' allows subclasses to override any token's PrintOpen() '''

  def HandleTokenClose(self, token, depth, first, last):
    ''' allows subclasses to override any token's PrintClose() '''

  def PrintIcon(self, snip):
    ''' allows subclasses to override icons '''

  def FilterImprints(self, imprints):
    ''' last chance to hack the imprint stream '''
    return imprints

  def MergeImprints(self, imprints):
    ''' merge the imprints into a single string '''
    NEWLINE         = '\n'
    substrings      = []
    for imprint in imprints:
      if imprint.imprinttype == IMPRINT_BREAK:
        substrings.append(NEWLINE)
      if imprint.text:
        substrings.append(imprint.text)
    return ''.join(substrings)

  ###
  ## mechanical
  #

  def __init__(self, **kwargs):
    base.utils.SetAttrs(self, **kwargs)
    self._muted     = None    # token
    self._stack     = []      # [ (token, prefix) ]
    self._broken    = True    # was the last emitted imprint a break?
    self._inlining  = False   # are we in the midst of emitting inline imprints?
    self._maybe     = None    # for double-spacing, a list of imprints we *might* want to apply

  def _NormalizeImprints(self, imprints):
    ''' convert a lone imprint to a tuple '''
    if not imprints:
      return []
    if isinstance(imprints, rightdown.tokens.Imprint):
      imprints      = [imprints]
    return imprints

  def _CollectPrefixes(self, depth):
    ''' accumulates the imprints that should begin a line, and augment each with its stack depth '''
    prefixes          = []
    for i in range(len(self._stack)):
      token, imprint  = self._stack[i]
      if imprint:
        imprint.depth = i
        prefixes.append(imprint)
    if self.block_indent and (not hasattr(self, 'minimize') or not self.minimize):
      prefixes.append(rightdown.tokens.Imprint(IMPRINT_FORMATTING, text=' '*depth*self.block_indent, depth=depth))
    return prefixes

  def _FixBreaks(self, imprints, breaker, prefixes, depth):
    ''' any non-inline imprints must be surrounded both sides by a break, and breaks should be followed by prefixes '''
    # self._broken is assumed to be accurate to the point *before* our first imprint
    results           = []
    doublespace       = self.double_space and (prefixes + [breaker])
    maybies           = self._maybe and [x for x in self._maybe if x.depth <= depth]
    for imprint in imprints:

      # imprint is a break; pass it through, maybe double it
      if imprint.imprinttype == IMPRINT_BREAK:
        if not self._broken:
          self._broken  = True
          results.append(breaker)
          if doublespace:
            if imprint is imprints[-1] and prefixes:
              self._maybe = prefixes
            else:
              results.extend(doublespace)

      # imprint is inline; we are now *not* broken
      elif imprint.inline:
        if self._broken:
          if self._maybe:
            results.extend(maybies)
            results.append(breaker)
            self._maybe = None
          results.extend(prefixes)
        results.append(imprint)
        self._broken  = False

      # imprint is not inline; make sure it's broken on both sides
      else:
        if self._maybe:
          results.extend(maybies)
          results.append(breaker)
          self._maybe = None
        if not self._broken:
          results.append(breaker)
          if doublespace:
            results.extend(doublespace)
        results.extend(prefixes)
        results.append(imprint)
        results.append(breaker)
        if doublespace:
          if imprint is imprints[-1] and prefixes:
            self._maybe = prefixes
          else:
            results.extend(doublespace)
        self._broken  = True

    return results

  def _WalkOpen(self, token, depth, first, last):
    ''' called on each token in the tree, before descending into that token's children '''
    # track who's called whom
    self._stack.append((token, None))

    # be silent if asked
    if self._muted:
      return

    # become silent if needed
    if not self.empties and token.empty:
      self.MuteUntilClose(token)
      return

    # gather prefixes before calling PrintOpen
    prefixes        = self._CollectPrefixes(depth)

    # get the token's imprints
    imprints        = self.HandleTokenOpen(token, depth, first, last)
    if imprints is None:
      imprints      = token.PrintOpen(self, first, last)
    imprints        = self._NormalizeImprints(imprints)

    # line-breaking
    breaker         = rightdown.tokens.Imprint(IMPRINT_BREAK)
    if imprints and imprints[0].inline and not self._inlining:
      self._inlining  = True
      if not self._broken:
        imprints    = [breaker] + imprints
    imprints        = self._FixBreaks(imprints, breaker, prefixes, depth)

    return imprints or None

  def _WalkClose(self, token, depth, first, last):
    ''' called on each token in the tree, after that token's children are finished '''
    # track who's called whom
    if self._stack[-1][0] != token:
      raise rightdown.errors.TreeWalkBroken(list(repr(x[0]) for x in self._stack), repr(token))
    self._stack     = self._stack[:-1]

    # might be finished with silence
    if self._muted:
      if self._muted == token:
        self._muted = None
      return

    # ask the token for its imprints
    prefixes        = self._CollectPrefixes(depth)
    imprints        = self.HandleTokenClose(token, depth, first, last)
    if imprints is None:
      imprints      = token.PrintClose(self, first, last)
    imprints        = self._NormalizeImprints(imprints)

    # break when exiting an inline context
    breaker         = Imprint(IMPRINT_BREAK)
    if not token.inline and self._inlining:
      self._inlining  = False
      if not self._broken:
        imprints.append(breaker)

    # fix up breaks
    imprints        = self._FixBreaks(imprints, breaker, prefixes, depth)

    return imprints or None



class TextPrinter(Printer):
  ''' this printer emits normalized rightdown text '''

  formatting                  = True
  metadata                    = True
  pass_html                   = True
  pass_comments               = True
  pass_templates              = True
  double_space                = True
  _test_substitution_column   = 2



class HtmlPrinter(Printer):
  ''' this printer emits HTML similar to any other markdown engine '''

  markup                      = True
  pass_html                   = True
  pass_templates              = True
  double_space                = False
  block_indent                = 2
  _test_substitution_column   = 3

  REGEXP_CLOSING_WHITE        = Grouper(Group(r'[^\s]', grouptype=GROUPTYPE_LOOK_BEHIND) + Capture(r'\s+') + '$')
  REGEXP_CLOSING_HTMLTAG      = Grouper(Capture(r'</\w+>'), groupermode=GROUPERMODE_START)

  def FilterImprints(self, imprints):
    imprints        = self._SwizleImprints(imprints)
    imprints        = self._EscapeImprints(imprints)
    return imprints

  def _EscapeImprints(self, imprints):
    for imprint in imprints:
      if imprint.imprinttype == IMPRINT_NARRATIVE:
        imprint.text  = html.escape(imprint.text)
    return imprints

  def _SwizleImprints(self, imprints):
    ''' browsers do a stupid where "<i>yip </i><b>yap</b>" loses white space but "<i>yip</i> <b>yap</b>" is fine '''
    results         = []
    stash           = None
    for imprint in imprints:
      if stash and imprint.imprinttype == IMPRINT_MARKUP and stash.inline and imprint.inline:
        remwhite    = self.REGEXP_CLOSING_WHITE(stash.text)
        remtag      = self.REGEXP_CLOSING_HTMLTAG(imprint.text)
        if remwhite and remtag:
          results.extend(self._SwizleImprintsInner(stash, imprint, remwhite, remtag))
          stash     = None
          continue
      if stash:
        results.append(stash)
      if imprint.imprinttype == IMPRINT_NARRATIVE:
        stash       = imprint
      else:
        results.append(imprint)
        stash       = None
    if stash:
      results.append(stash)
    return results

  def _SwizleImprintsInner(self, narrative, markup, remwhite, remtag):
    poswhite        = remwhite.start()
    if poswhite == 0:
      return (narrative, markup)

    white           = Imprint(IMPRINT_NARRATIVE, narrative.text[poswhite:], inline=True)
    narrative.text  = narrative.text[:poswhite]

    postag          = remtag.end()
    if postag == len(markup.text):
      return (narrative, markup, white)

    second          = Imprint(IMPRINT_MARKUP, markup.text[postag:], inline=True)
    markup.text     = markup.text[:postag]
    return (narrative, markup, white, second)

#   ATTRIBUTES        = Printer.ATTRIBUTES + ['dress', 'minimize']
#
#   # Normally we emit naked HTML, but let us know if you want <HTML>, <HEAD>, and <BODY> tags with that
#   dress                       = False
#
#   # Should the HTML be compacted down to one line?
#   minimize                    = False
#
#   def _MergeImprints(self, imprints):
#     if self.minimize:
#       return ''.join(x.text or '' for x in imprints)
#     return super()._MergeImprints(imprints)



class DebugPrinter(Printer):
  ''' emits a plaintext summary of the token tree '''

  ATTRIBUTES        = ('truncate_width', 'token_width')

  # How many characters when printing lines to the console?
  truncate_width              = 60

  # How many characters to allocate for the name of a token?
  token_width                 = 24

  def Print(self, rd):
    ''' distills a RightDown instance to a single string '''
    return '\n'.join(rd.Walk(self._WalkOpen, self._WalkClose) or [])

  def _WalkOpen(self, token, depth, first, last):
    tokensymbol     = token.tokentype.enum == LineTypes and '-' or ''
    tokentag        = '  ' * depth + tokensymbol + token.tokentype.name
    tokentext       = token.debug
    if tokentext:
      content       = base.utils.PadString(tokentag, self.token_width) + token.debug_sep + ' ' + tokentext
    else:
      content       = tokentag
    if self.truncate_width and len(content) > self.truncate_width:
      content       = content[:self.truncate_width-1] + '…'
    if content:
      return content

  def _WalkClose(self, token, depth, first, last):
    ''' this method intentionally left blank '''
