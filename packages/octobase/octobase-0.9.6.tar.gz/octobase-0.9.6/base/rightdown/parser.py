#!/opt/local/bin/python

import base
import logging

from base                   import rightdown
from base.regexp            import *
from base.rightdown.enums   import *
from base.rightdown.tokens  import *


class Parser(base.Thing):
  ''' main parsing engine for rightdown text '''

  # How many spaces equals a tab?
  tab_width                   = 2

  # How many spaces equals an indented code block?  0 to turn off
  indented_code_width         = 4

  # How many levels of title should we extract as metadata?
  title_metadata_levels       = 3

  # Should metadata be stripped to plaintext?
  plaintext_metadata          = True
  plaintext_metadata_unless   = ('description', 'excerpt', 'style', 'url')

  # Allow fragment 0 metadata to override any parser options?
  allow_option_overrides      = ('tab_width', 'indented_code_width', 'title_metadata_levels')

  # What character should illegal characters be replaced with when we ingest text?
  illegal_char                = ' '

  # what character should illegal characters be replaced with when we emit text?
  barf_char                   = CHAR_DEL

  # Parse only through this stage, then break
  stop_after_stage            = STAGE_DONE

  ## Copy()-ing a Parser means copying just our configuration settings
  ATTRIBUTES        = (
      'tab_width', 'indented_code_width', 'title_metadata_levels',
      'plaintext_metadata', 'plaintext_metadata_unless',
      'allow_option_overrides', 'illegal_char', 'barf_char', 'stop_after_stage',
  )

  # these accumulators track if various weirdnesses happen during parsing
  has_illegal_chars = False   # reserved characters in text on the way in
  has_barf_chars    = False   # reserved characters in text on the way out (indicates we have bugs)
  has_squiguelgmas  = False   # an easter-egg that exists for testing was triggered

  def Parse(self, thing, *args, **kwargs):
    ''' builds a RightDown instance out of a string, iter of strings, or a file '''
    if isinstance(thing, str):
      return self._Parse(thing.split('\n'), *args, **kwargs)
    if hasattr(thing, 'readlines'):
      return self._Parse(thing.readlines(), *args, **kwargs)
    if hasattr(thing, '__iter__'):
      return self._Parse(thing, *args, **kwargs)
    raise rightdown.errors.UnParsable(thing)

  def __init__(self, **kwargs):
    base.utils.SetAttrs(self, **kwargs)
    # each of these is a singleton and will compile its patterns on first init
    self.linemaker  = LineMaker()
    self.blockmaker = BlockMaker()
    self.textmaker  = TextMaker()

  ###
  ## mechanics
  #

  def _TriggerIllegal(self):
    self.has_illegal_chars  = True

  def _TriggerBarf(self):
    self.has_barf_chars     = True

  def _Squiguelgmas(self, s):
    ''' most sane text editors strip ending whitespace on lines.  therefore, this tiny easter egg allows
        us to maintain test data that ensures we still respect traditional markdown way of forcing line breaks.
        specifically, if the word `SQUIGUELGMAS` ends a line, we replace it with two spaces.  that's all
    '''
    word          = 'SQUIGUELGMAS'
    if s.endswith(word):
      self.has_squiguelgmas = True
      return s[:-len(word)] + '  '
    return s

  def _PreFilter(self, s):
    ''' pre-filters every line of input text '''
    # this keeps us from exploding if you feed us documents that use the same reserved unicode characters we do
    s               = SpecialCharGen.WipeSpecialChars(s, self.illegal_char, self._TriggerIllegal)
    s               = self._Squiguelgmas(s)
    return s

  def _Parse(self, lst, _recursive=False):
    ''' builds a RightDown instance out of an iter of strings '''
    rd              = rightdown.RightDown()

    rd.children     = [self.linemaker(self, self._PreFilter(s)) for s in lst]

    for i in range(len(rd.children)-1, -1, -1):
      if rd.children[i].tokentype != LINETYPE_EMPTY:
        rd.children = rd.children[:i+1]
        break
    if self.stop_after_stage == STAGE_LINES:
      return rd

    rd.children     = self.blockmaker.Fragment(self, rd.children) or []
    if self.stop_after_stage == STAGE_FRAGMENTS:
      return rd
    if not rd.children:
      return rd

    rd.children[0].DigestMetadata(self)
    rd.metadata     = rd.children[0].metadata or {}
    if self.stop_after_stage == STAGE_EARLY_METADATA:
      return rd

    rd              = self._ConsiderReparse(rd, lst)
    if self.stop_after_stage == STAGE_REPARSED:
      return rd

    rd.children[0].DigestContent(self, _recursive=_recursive)
    rd.metadata     = rd.children[0].metadata or {}
    if self.stop_after_stage == STAGE_METADATA:
      return rd

    for fragment in rd.children[1:]:
      fragment.DigestLines(self)
    if self.stop_after_stage == STAGE_BLOCKS:
      return rd

    for fragment in rd.children:
      fragment.ProcessText(self)
    if self.stop_after_stage == STAGE_INLINES:
      return rd

    rd.Validate()
    self._SetWarnings(rd)
    return rd

  def _SetWarnings(self, rd):
    rd.has_illegal_chars  = self.has_illegal_chars
    rd.has_barf_chars     = self.has_barf_chars
    rd.has_squiguelgmas   = self.has_squiguelgmas

    if self.has_illegal_chars:
      base.utils.Log('RIGHTDOWN', 'reserved characters detected in input', level=logging.WARN)
    if self.has_barf_chars:
      base.utils.Log('RIGHTDOWN', 'reserved characters detected in output', level=logging.ERROR)
    if self.has_squiguelgmas:
      base.utils.Log('RIGHTDOWN', 'squiguelgmas', level=logging.INFO)

  def _ConsiderReparse(self, rd, lst):
    ''' if the frag0 metadata changes any of our parse settings, go ahead and reparse '''
    if not self.allow_option_overrides:
      return rd
    reparse         = False
    for attr in self.allow_option_overrides:
      if attr in rd.metadata:
        value       = rd.metadata[attr]
        if value.isdigit():
          value     = int(value)
          if value != getattr(self, attr):
            reparse = True
            setattr(self, attr, value)
    if reparse:
      base.utils.Log('RD', 'reparsing due to metadata overrides')
      oldterminus   = self.stop_after_stage
      self.stop_after_stage  = STAGE_EARLY_METADATA
      rd            = self._Parse(lst)
      self.stop_after_stage  = oldterminus
    return rd


###
## early stage: LineMaker
#


class LineMaker(metaclass=base.utils.Singleton):
  ''' creates Lines from strings '''

  def __init__(self):
    self.linepats   = base.regexp.MultiGrouper(
        rightdown.patterns.LINE_PATTERNS, groupermode=GROUPERMODE_START, multigroupermode=MULTIGROUPERMODE_FIRST)
    self.nocomments = base.regexp.MultiGrouper(
        rightdown.patterns.LINE_PATTERNS_NO_COMMENT, groupermode=GROUPERMODE_START, multigroupermode=MULTIGROUPERMODE_FIRST)

  def __call__(self, parser, s):
    ''' creates the appropriate Line for a given string '''

    s               = s.rstrip('\r\n')
    line            = Line(original=s)

    s               = s.replace('\t', ' '*parser.tab_width)
    lens            = len(s)
    trailing        = 0
    for i in range(0, lens):
      if s[i] != ' ':
        line.leading_space  = i
        break
    else:
      if lens:
        line.leading_space  = lens

    for i in range(lens-1, line.leading_space, -1):
      if s[i] != ' ':
        trailing    = len(s)-1-i
        break

    s               = s[line.leading_space:len(s)-trailing]
    line.trimmed    = s
    line.mergable   = s

    if s and s[-1] == '\\':
      line.mergable = s[:-1] + '\n'
    elif trailing >= 2:
      line.mergable = s + '\n'

    line.tokentype  = self.LineType(parser, line)
    return line

  def LineType(self, parser, line, comments=True, indents=True):
    ''' runs our patterns to find the type of the line '''
    if not line.trimmed:
      return LINETYPE_EMPTY

    if indents and parser.indented_code_width and line.leading_space >= parser.indented_code_width:
      line.tokentype  = LINETYPE_INDENTED_CODE
      return LINETYPE_INDENTED_CODE

    if comments:
      multigroup        = self.linepats(line.trimmed)
    else:
      multigroup        = self.nocomments(line.trimmed)
    if multigroup:
      tokentype, _    = multigroup
      return tokentype

    if indents and line.leading_space >= parser.tab_width:
      line.tokentype  = LINETYPE_ALMOST_INDENTED
      return LINETYPE_ALMOST_INDENTED

    line.tokentype    = LINETYPE_TEXT
    return LINETYPE_TEXT


###
## middle stage:  BlockMaker and its helper, TokenList
#


class TokenList:
  ''' indexes a list of tokens by a comma-separated list of their tags.  as each tag is
      exactly the same length, we can use pattern matching against the summary string to
      identify ranges of tokens
  '''

  TOKENLEN          = 4

  def __init__(self, tokens):
    self.tokens     = tokens
    self.summary    = ''.join(x.tokentype.tag for x in tokens)

  def ChunkOnce(self, pattern, tokenclass):
    ''' search for a pattern among our tokens, and if found, replace it with a single new token '''
    self._ProcessSplit(self._SplitSummary(pattern), tokenclass)

  def ChunkRepeatedly(self, pattern, tokenclass):
    ''' like ChunkOnce(), but loops until the pattern stops matching '''
    split           = self._SplitSummary(pattern)
    while split:
      self._ProcessSplit(split, tokenclass)
      split         = self._SplitSummary(pattern, split)

  def _SplitSummary(self, pattern, lastsplit=None):
    ''' returns (start, end, captured) if the pattern matches our summary, or None otherwise '''
    # try to search from the last point we left off
    ibase           = 0
    if lastsplit and pattern.mode == base.regexp.GROUPERMODE_SEARCH:
      ibase         = lastsplit[0] + self.TOKENLEN

    # bang
    rem           = pattern.Match(self.summary[ibase:])
    if not rem:
      return

    # clean up the split range
    i0, i1          = rem.span()
    i0, i1          = i0 + ibase, i1 + ibase
    if i0 % self.TOKENLEN:
      raise rightdown.errors.MisalignedPattern(pattern.pattern, i0, i1, self.summary[i0:i1])
    if i1 % self.TOKENLEN:
      i1            = i1 + self.TOKENLEN - (i1 % self.TOKENLEN)

    # allow a single Capture() group in the pattern to refine what tokens get kept out of the split range
    captured        = None
    groups          = rem.groups()
    if groups and len(groups) == 1:
      captured      = groups[0]

    return i0, i1, captured

  def _ProcessSplit(self, split, tokenclass):
    ''' creates an instance of tokenclass and replaces the split's range in our tokens and summary with it '''
    if split:
      i0, i1, cap   = split                       # i == index into self.summary of split range
      j0, j1        = int(i0 / self.TOKENLEN), int(i1 / self.TOKENLEN)
      cuttokens     = self.tokens[j0:j1]          # j == index into self.tokens of split range
      if cap:
        k0          = int((''.join(x.tokentype.tag for x in cuttokens).index(cap)) / self.TOKENLEN)
        k1          = int(k0 + (len(cap)/self.TOKENLEN))
        cuttokens   = cuttokens[k0:k1]            # k == index into cuttokens of the capture range
      newtoken      = tokenclass(children=cuttokens)
      self.tokens   = self.tokens[:j0] + [newtoken] + self.tokens[j1:]
      self.summary  = self.summary[:i0] + newtoken.tokentype.tag + self.summary[i1:]


class BlockMaker(metaclass=base.utils.Singleton):
  ''' refines lists of line tokens into block tokens '''

  def __init__(self):
    self.metapat    = Grouper(rightdown.patterns.METADATA_PATTERN, GROUPERMODE_START)
    self.fragpats   = [(rightdown.blocks.BlockForType(x), Grouper(z, groupermode=y)) for x,y,z in rightdown.patterns.FRAGMENT_PATTERNS]
    self.fldlstpats = [(rightdown.blocks.BlockForType(x), Grouper(z, groupermode=y)) for x,y,z in rightdown.patterns.FIELDLIST_PATTERNS]
    self.mainpats   = [(rightdown.blocks.BlockForType(x), Grouper(z, groupermode=y)) for x,y,z in rightdown.patterns.CONTENT_PATTERNS]

  def Fragment(self, parser, tokens):
    ''' distills our initial list of lines into a minimal list of fragments '''
    # make comments, code blocks, and fragments
    tokes           = TokenList(tokens)
    for tokenklass, pattern in self.fragpats:
      tokes.ChunkRepeatedly(pattern, tokenklass)

    # number each fragment
    counter         = base.utils.Counter()
    for token in tokes.tokens:
      token.index   = counter()

    return tokes.tokens

  def Metadata(self, parser, tokens):
    ''' parses the metadata block that leads a fragment '''
    tokes           = TokenList(tokens)
    tokes.ChunkOnce(self.metapat, rightdown.blocks.BlockForType(BLOCKTYPE_METADATA))
    if tokes.tokens and tokes.tokens[0].tokentype == BLOCKTYPE_METADATA:
      metadata      = tokes.tokens[0]
      subtokes      = TokenList(metadata.children)
      for tokenclass, pattern in self.fldlstpats:
        subtokes.ChunkRepeatedly(pattern, tokenclass)
      metadata.children = subtokes.tokens
    return tokes.tokens

  def Content(self, parser, tokens):
    ''' parses the rest of our block types '''
    tokes           = TokenList(tokens)
    for tokenklass, pattern in self.mainpats:
      tokes.ChunkRepeatedly(pattern, tokenklass)

    # strip empty lines, and turn any remaining runs of unblocked non-empty lines into paragraphs
    tokens          = []
    paragraph       = []
    for token in tokes.tokens:
      if isinstance(token, Block):
        if paragraph:
          tokens.append(rightdown.blocks.Paragraph(children=paragraph))
          paragraph = []
        tokens.append(token)
        continue
      if isinstance(token, Line):
        if token.tokentype  == LINETYPE_EMPTY:
          if paragraph:
            tokens.append(rightdown.blocks.Paragraph(children=paragraph))
            paragraph = []
        else:
          paragraph.append(token)
    if paragraph:
      tokens.append(rightdown.blocks.Paragraph(children=paragraph))

    return tokens


###
## late stage: TextMaker
#


class TextMaker(metaclass=base.utils.Singleton):
  ''' refines a string into a text block '''

  def __init__(self):
    self.codesnippat  = Grouper(rightdown.patterns.CODE_SNIP_PATTERN)
    self.whackwhack   = Grouper(r'\\\\')
    self.whacktick    = Grouper(r'\\`')
    self.whackdot     = Grouper(r'\\.')
    self.whackspace   = (Grouper(rightdown.patterns.SIMPLE_PATTERN_NBSP[0]), rightdown.patterns.SIMPLE_PATTERN_NBSP)
    self.blockpats    = [(x, Grouper(y)) for x,y in rightdown.patterns.TEXTBLOCK_PATTERNS]
    self.updowns      = [(x, Grouper(y)) for x,y in rightdown.patterns.UPDOWN_PATTERNS]
    self.leftrights   = [(x, Grouper(y)) for x,y in rightdown.patterns.LEFTRIGHT_PATTERNS]
    self.simplesubs   = self._CompileSimpleSubs()   # [ ( grouper, patterntuple ) ]

  def _CompileSimpleSubs(self):
    results           = []
    for submode, patternlist in rightdown.patterns.TEXT_SUBSTITUTIONS.items():
      for patterntuple in patternlist:
        pattern       = patterntuple[0]
        decorated     = rightdown.patterns.TEXT_SUB_DECORATORS[submode](pattern)
        results.append((Grouper(decorated), patterntuple))
    return results

  def __call__(self, s, parenttext, **kwargs):
    if not s:
      return

    text              = parenttext and parenttext.Spawn(text=s) or rightdown.textblock.Text(text=s)

    # backslash backslash
    self.SubOut(text, self.whackwhack)

    # backslash backtick
    self.SubOut(text, self.whacktick)

    # backtick ranges
    self.ChunkToken(text, SNIPTYPE_CODE, self.codesnippat, **kwargs)

    # backslash space
    self.Chunk(text, self.whackspace[0], self.whackspace[1])

    # backslashed other characters
    self.SubOut(text, self.whackdot)

    # blocks and snips
    self.ChunkTokenAll(text, self.blockpats, **kwargs)

    # simple substitutions
    for grouper, patterntuple in self.simplesubs:
      self.Chunk(text, grouper, stash=patterntuple)

    # more snips
    self.ChunkTokenAll(text, self.updowns, entire=False, **kwargs)
    self.ChunkTokenAll(text, self.leftrights, **kwargs)

    # if through all this we did nothing, just return a simple snip instead
    if not text.subdict:
      return Snip(SNIPTYPE_PLAIN, text=text.text)
    return text

  def Chunk(self, text, pattern, stash=None, replace=None, strip=None):
    ''' match a pattern -- that may have unnamed groups -- and (usually) stash it for later '''
    howmany         = 0
    rem             = pattern.Match(text.text)
    while rem:
      howmany       += 1
      i0, i1        = rem.span()
      old           = text.text[i0:i1]
      groups        = rem.groups()
      if groups:
        captured    = groups[-1]
        i0          = i0 + old.index(captured)
        i1          = i0 + len(captured)
        old         = captured
      loopstash     = stash or old
      if strip and loopstash.startswith(strip):
        loopstash   = loopstash[len(strip):]
      new           = replace or text.AddSub(loopstash)
      text.text     = text.text[:i0] + new + text.text[i1:]
      rem           = pattern.Match(text.text)
    return howmany

  def ChunkToken(self, text, tokentype, pattern, entire=True, **kwargs):
    ''' match a pattern -- that may have named groups -- create a token from it, and stash that '''
    howmany         = 0
    rem             = pattern.Match(text.text)
    while rem:
      howmany       += 1
      oldtext       = None
      groups        = rem.groupdict()
      if entire or len(groups) != 1:
        i0, i1      = rem.span()
      else:
        i0, i1      = rem.span(1)
      if tokentype in SnipTypes:
        thing       = Snip(tokentype, **groups, **kwargs)
      else:
        thing       = rightdown.blocks.BlockForType(tokentype)(**groups)
      new           = text.AddSub(thing)
      text.text     = text.text[:i0] + new + text.text[i1:]
      rem           = pattern.Match(text.text)
    return howmany

  def ChunkTokenAll(self, text, patternlist, **kwargs):
    ''' match all patterns and replace them with a Snip of the given type '''
    for blocktype, pattern in patternlist:
      self.ChunkToken(text, blocktype, pattern, **kwargs)

  def SubOut(self, text, pattern):
    ''' replace backslashed characters so they can't match our patterns '''
    self.Chunk(text, pattern, strip='\\')
