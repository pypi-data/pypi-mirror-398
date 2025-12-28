#!/opt/local/bin/python

import base

from base                   import rightdown
from base.regexp            import *
from base.rightdown.enums   import *
from base.rightdown.tokens  import *


class Text(Block):

  UNICODE_USER_MIN    = chr(SpecialCharGen.UNICODE_USER_MIN)
  UNICODE_USER_MAX    = chr(SpecialCharGen.UNICODE_USER_MAX)

  tokentype         = BLOCKTYPE_TEXT
  text_after_inline = True
  inline            = True
  subchars          = None    # SpecialCharGen
  subdict           = None    # { special char: what it replaces }

  align             = ALIGN_DEFAULT

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.subchars   = self.subchars or SpecialCharGen()
    if self.subdict is None:
      self.subdict  = {}

  def Spawn(self, **kwargs):
    ''' returns a new, empty Text, with the same subdict and subchars as ourself '''
    return type(self)(subchars=self.subchars, subdict=self.subdict, **kwargs)

  def AddSub(self, thing):
    '''
    for inline tokenizing, tokens we substitute into strings need to be something we can differentiate
    from the original string.  to this end, we'll use single-character strings drawn from the unicode
    range reserved for "private use"
    '''
    c               = self.subchars()
    self.subdict[c] = thing
    if isinstance(thing, Token):
      self.children.append(thing)
    return c

  def ProcessText(self, parser, parenttext=None):
    if self.processed:
      raise rightdown.errors.DoubleProcess(self)
    self.processed  = True

    # look for paragraph alignment marks
    self.AdjustAlign()

    # detect and turn off format up/dn with nothing in the middle
    self.PassivateEmptyFormats()

    # let all our children process
    for child in self.children:
      if isinstance(child, Block) and not child.processed:
        child.ProcessText(parser, parenttext=self)

    # give each format snip a comingler
    cominglers      = []
    for c in self.text:
      if c >= self.UNICODE_USER_MIN and c <= self.UNICODE_USER_MAX:
        child       = self.subdict.get(c)
        if isinstance(child, Token) and child.tokentype in (SNIPTYPE_FORMAT_UP, SNIPTYPE_FORMAT_MIDDLE, SNIPTYPE_FORMAT_DOWN):
          comingler = Comingler(child)
          cominglers.append(comingler)
          child.snipprinter = comingler

    # let all the cominglers count how much heat they have
    state           = (0, False, False, False)    # heat, striking, scoring, marking
    for comingler in cominglers[::-1]:
      state         = comingler.WalkStateBack(*state)

    # let all the cominglers note corrections for overflow
    if state != (0, False, False, False):
      state         = (state[0], False, False, False)
      for comingler in cominglers:
        state       = comingler.WalkOverflowFore(state)
        if state == (0, False, False, False):
          break

  def AdjustAlign(self):
    if not self.children or len(self.children) < 2:
      return

    # snips are extracted in some order, where left/right pushes are near the end.
    # this means we don't actually know where in self.children our push tokens are.
    # all we really know is if there's two (or more) of them, they appear in relative order

    pushtokes       = [x for x in self.children if x.tokentype in (SNIPTYPE_FORMAT_LEFT, SNIPTYPE_FORMAT_RIGHT)]

    lpushl, lpushr  = False, False
    rpushl, rpushr  = False, False

    if pushtokes:
      lpushr        = pushtokes[0].tokentype == SNIPTYPE_FORMAT_RIGHT
      lpushl        = pushtokes[0].tokentype == SNIPTYPE_FORMAT_LEFT
      rpushr        = pushtokes[-1].tokentype == SNIPTYPE_FORMAT_RIGHT
      rpushl        = pushtokes[-1].tokentype == SNIPTYPE_FORMAT_LEFT

    if lpushr and rpushl:
      self.align    = ALIGN_CENTER
    elif lpushl and rpushr:
      self.align    = ALIGN_JUSTIFY
    elif lpushr or rpushr:
      self.align    = ALIGN_RIGHT
    elif lpushl or rpushl:
      self.align    = ALIGN_LEFT

  def PassivateEmptyFormats(self):
    for i in range(len(self.text)-1):
      c             = self.text[i]
      if c < self.UNICODE_USER_MIN or c > self.UNICODE_USER_MAX:
        continue

      d             = self.text[i+1]
      if d < self.UNICODE_USER_MIN or d > self.UNICODE_USER_MAX:
        continue

      c             = self.subdict.get(c)
      d             = self.subdict.get(d)
      if isinstance(c, Snip) and isinstance(d, Snip):
        if c.tokentype == SNIPTYPE_FORMAT_UP and d.tokentype == SNIPTYPE_FORMAT_DOWN:
          c.tokentype = SNIPTYPE_PLAIN
          d.tokentype = SNIPTYPE_PLAIN

  def PrintOpen(self, printer, first, last):
    printer.MuteUntilClose(self)
    if self.text:
      return list(self._IterImprints(printer))

  def _IterImprints(self, printer):
    ''' yields a stream of Imprints from rendering our text with the given printer '''
    chunk           = []

    for result in self._IterChars(printer):
      if not result:
        continue
      if isinstance(result, str):
        chunk.append(result)
        continue

      if isinstance(result, Imprint):
        if chunk:
          flush     = ''.join(chunk)
          chunk     = []
          yield Imprint(IMPRINT_NARRATIVE, flush, inline=True)
        yield result
      elif isinstance(result, list):
        if chunk:
          flush     = ''.join(chunk)
          chunk     = []
          yield Imprint(IMPRINT_NARRATIVE, flush, inline=True)
        for imprint in result:
          yield imprint

    if chunk:
      flush         = ''.join(chunk)
      chunk         = []
      yield Imprint(IMPRINT_NARRATIVE, flush, inline=True)

  def _IterChars(self, printer):
    ''' iterates through our raw text one character at a time, returning either that char, or that special char's expansion '''
    # one char at a time
    for c in self.text:
      # normal character?
      if c < self.UNICODE_USER_MIN or c > self.UNICODE_USER_MAX:
        yield c

      # substitution indicator?
      c             = self.subdict.get(c)

      # decode what we found
      if not c:
        continue

      if isinstance(c, str) or isinstance(c, list) or isinstance(c, Imprint):
        yield c
        continue

      if isinstance(c, Snip):
        yield c.Print(printer)
        continue

      if isinstance(c, Block):
        printed     = printer.Dupe().Print(c)
        if printed:
          yield Imprint(IMPRINT_INERT, printed, inline=True)
        continue

      if isinstance(c, tuple):
        # (pattern, naked, text, html)
        lenc        = len(c)
        k           = printer._test_substitution_column
        # if html is missing, naked will be used
        if k == 3 and lenc < 4:
          k         = 1
        # if text is missing, pattern will be used
        elif k == 2 and lenc < 3:
          k         = 0
        if k < lenc:
          if k == 3:
            yield Imprint(IMPRINT_INERT, c[k], inline=True)
          else:
            yield c[k]
        continue

      yield str(c)



class Comingler(base.Thing):

  on                = None    # True if we're turning on some kind of marking, False if we're turning it off

  striking          = False
  scoring           = False
  marking           = False
  heat              = 0
  heat0             = 0

  # how many overflow characters we need to emit
  stars             = 0
  equals            = 0
  scores            = 0
  tildes            = 0

  @property
  def debug(self):
    parts           = []
    if self.heat or self.heat0:
      parts.append(str(self.heat0))
      parts.append('->')
      heat1         = self.heat0 + self.heat * (self.on and 1 or -1)
      parts.append(str(heat1))
    if self.striking or self.scoring or self.marking:
      parts.append(self.on and '+' or '-')
    if self.striking:
      parts.append('st')
    if self.scoring:
      parts.append('sc')
    if self.marking:
      parts.append('mk')
    return ' '.join(parts)

  def __init__(self, snip, **kwargs):
    super().__init__(**kwargs)

    if snip.tokentype == SNIPTYPE_FORMAT_UP:
      self.on       = True
    elif snip.tokentype == SNIPTYPE_FORMAT_DOWN:
      self.on       = False

    text            = snip.text or ''

    stars           = text.count('*')
    equals          = text.count('=')
    scores          = text.count('_')
    tildes          = text.count('~')

    self.striking   = bool(tildes)
    self.scoring    = bool(scores)
    self.marking    = bool(equals)
    self.heat       = min(3, stars)

    self.stars      = max(0, stars - 3)
    self.equals     = max(0, equals - 2)
    self.scores     = max(0, scores - 2)
    self.tildes     = max(0, tildes - 2)

  def WalkStateBack(self, heat, striking, scoring, marking):
    if self.heat:
      delta         = self.heat * (self.on and 1 or -1)
      heat          = heat - delta
      self.heat0    = heat

    if self.striking:
      if self.on is None:
        self.on     = striking
        striking    = not striking
      elif self.on and not striking:
        self.striking  = False
        self.tildes += 1
      else:
        striking    = not striking

    if self.scoring:
      if self.on and not scoring:
        self.scoring  = False
        self.scores += 1
      else:
        scoring     = not scoring

    if self.marking:
      if self.on and not marking:
        self.marking  = False
        self.equals += 1
      else:
        marking     = not marking

    return (heat, striking, scoring, marking)

  def WalkOverflowFore(self, state):
    heat, striking, scoring, marking  = state

    if heat < 0:    # too many ON stars
      capture       = min(self.heat, -heat)
      self.heat     -= capture
      self.heat0    += capture
      if self.on:
        self.stars  += capture
        heat        -= capture

    elif heat > 0:  # too many OFF stars
      capture       = min(self.heat, heat)
      self.heat0    -= capture
      if not self.on:
        self.stars  += capture
        heat        -= capture

    if self.striking:
      if not self.on and not striking:
        self.striking  = False
        self.tildes += 1
      else:
        striking    = not striking

    if self.scoring:
      if not self.on and not scoring:
        self.scoring  = False
        self.scores += 1
      else:
        scoring     = not scoring

    if self.marking:
      if not self.on and not marking:
        self.marking  = False
        self.equals += 1
      else:
        marking     = not marking

    return (heat, striking, scoring, marking)

  def Print(self, snip, printer):
    imprints        = []
    if printer.markup:
      self.OpenOurMarkup(imprints)
    self.Narrative(imprints)
    if printer.markup:
      self.CloseOurMarkup(imprints)
    return imprints

  def OpenOurMarkup(self, imprints):
    if not self.on:
      return

    if self.heat:
      if self.heat0 == 0:
        if self.heat == 1:      # 0 --> 1
          imprints.append(Imprint(IMPRINT_MARKUP, '<i>', inline=True))
        elif self.heat == 2:    # 0 --> 2
          imprints.append(Imprint(IMPRINT_MARKUP, '<b>', inline=True))
        elif self.heat == 3:    # 0 --> 3
          imprints.append(Imprint(IMPRINT_MARKUP, '<b><i>', inline=True))
      elif self.heat0 == 1:
        if self.heat == 1:      # 1 --> 2
          imprints.append(Imprint(IMPRINT_MARKUP, '</i><b>', inline=True))
        elif self.heat >= 2:    # 1 --> 3
          imprints.append(Imprint(IMPRINT_MARKUP, '</i><b><i>', inline=True))
      elif self.heat0 == 2:     # 2 --> 3
        imprints.append(Imprint(IMPRINT_MARKUP, '<i>', inline=True))

    if self.scoring:
      imprints.append(Imprint(IMPRINT_MARKUP, '<u>', inline=True))

    if self.marking:
      imprints.append(Imprint(IMPRINT_MARKUP, '<mark>', inline=True))

    if self.striking:
      imprints.append(Imprint(IMPRINT_MARKUP, '<s>', inline=True))

  def CloseOurMarkup(self, imprints):
    if self.on:
      return

    if self.striking:
      imprints.append(Imprint(IMPRINT_MARKUP, '</s>', inline=True))

    if self.marking:
      imprints.append(Imprint(IMPRINT_MARKUP, '</mark>', inline=True))

    if self.scoring:
      imprints.append(Imprint(IMPRINT_MARKUP, '</u>', inline=True))

    if self.heat:
      if self.heat0 == 1:       # 1 --> 0
        imprints.append(Imprint(IMPRINT_MARKUP, '</i>', inline=True))
      elif self.heat0 == 2:
        if self.heat == 1:      # 2 --> 1
          imprints.append(Imprint(IMPRINT_MARKUP, '</b><i>', inline=True))
        elif self.heat >= 2:    # 2 --> 0
          imprints.append(Imprint(IMPRINT_MARKUP, '</b>', inline=True))
      elif self.heat0 == 3:
        if self.heat == 1:      # 3 --> 2
          imprints.append(Imprint(IMPRINT_MARKUP, '</i>', inline=True))
        elif self.heat == 2:    # 3 --> 1
          imprints.append(Imprint(IMPRINT_MARKUP, '</i></b><i>', inline=True))
        elif self.heat == 3:    # 3 --> 0
          imprints.append(Imprint(IMPRINT_MARKUP, '</i></b>', inline=True))

  def Narrative(self, imprints):
    # tildes must come after equals because ~= is a text substitution that binds
    # before formatting marks do.  other marks we reverse the order for on/off
    if self.on:
      if self.scores:
        imprints.append(Imprint(IMPRINT_NARRATIVE, '_'*self.scores, inline=True))
      if self.stars:
        imprints.append(Imprint(IMPRINT_NARRATIVE, '*'*self.stars, inline=True))
      if self.equals:
        imprints.append(Imprint(IMPRINT_NARRATIVE, '='*self.equals, inline=True))
      if self.tildes:
        imprints.append(Imprint(IMPRINT_NARRATIVE, '~'*self.tildes, inline=True))
    else:
      if self.equals:
        imprints.append(Imprint(IMPRINT_NARRATIVE, '='*self.equals, inline=True))
      if self.tildes:
        imprints.append(Imprint(IMPRINT_NARRATIVE, '~'*self.tildes, inline=True))
      if self.stars:
        imprints.append(Imprint(IMPRINT_NARRATIVE, '*'*self.stars, inline=True))
      if self.scores:
        imprints.append(Imprint(IMPRINT_NARRATIVE, '_'*self.scores, inline=True))




  def OldWay(self):
    if self.striking:
      imprints.append(Imprint(IMPRINT_MARKUP, Frame('s'), inline=True))

    if self.scoring:
      imprints.append(Imprint(IMPRINT_MARKUP, Frame('u'), inline=True))

    if self.marking:
      imprints.append(Imprint(IMPRINT_MARKUP, Frame('mark'), inline=True))

    if self.heat:

      if self.heat0 == -2 and self.on and self.heat == 3:       # -2 --> 1
        imprints.append(Imprint(IMPRINT_MARKUP, '<i>', inline=True))

      if self.heat0 == -1 and self.on:
        if self.heat == 2:      # -1 --> 1
          imprints.append(Imprint(IMPRINT_MARKUP, '<i>', inline=True))
        if self.heat == 3:      # -1 --> 2
          imprints.append(Imprint(IMPRINT_MARKUP, '<b>', inline=True))

      if self.heat0 == 0 and self.on:
        if self.heat == 1:      # 0 --> 1
          imprints.append(Imprint(IMPRINT_MARKUP, '<i>', inline=True))
        elif self.heat == 2:    # 0 --> 2
          imprints.append(Imprint(IMPRINT_MARKUP, '<b>', inline=True))
        elif self.heat == 3:    # 0 --> 3
          imprints.append(Imprint(IMPRINT_MARKUP, '<b><i>', inline=True))

      elif self.heat0 == 1 and self.on:
        if self.heat == 1:      # 1 --> 2
          imprints.append(Imprint(IMPRINT_MARKUP, '</i><b>', inline=True))
        elif self.heat >= 2:    # 1 --> 3
          imprints.append(Imprint(IMPRINT_MARKUP, '</i><b><i>', inline=True))

      elif self.heat0 == 1 and not self.on and self.heat:       # 1 --> 0
        imprints.append(Imprint(IMPRINT_MARKUP, '</i>', inline=True))

      elif self.heat0 == 2 and self.on and self.heat:           # 2 --> 3
        imprints.append(Imprint(IMPRINT_MARKUP, '<i>', inline=True))

      elif self.heat0 == 2 and not self.on:
        if self.heat == 1:      # 2 --> 1
          imprints.append(Imprint(IMPRINT_MARKUP, '</b><i>', inline=True))
        elif self.heat >= 2:    # 2 --> 0
          imprints.append(Imprint(IMPRINT_MARKUP, '</b>', inline=True))

      elif self.heat0 == 3 and not self.on:
        if self.heat == 1:      # 3 --> 2
          imprints.append(Imprint(IMPRINT_MARKUP, '</i>', inline=True))
        elif self.heat == 2:    # 3 --> 1
          imprints.append(Imprint(IMPRINT_MARKUP, '</i></b><i>', inline=True))
        elif self.heat == 3:    # 3 --> 0
          imprints.append(Imprint(IMPRINT_MARKUP, '</i></b>', inline=True))

    return imprints or None
