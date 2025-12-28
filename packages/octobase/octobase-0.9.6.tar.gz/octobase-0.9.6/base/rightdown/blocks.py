#!/opt/local/bin/python

import base
import re

from base                     import rightdown
from base.regexp              import *
from base.rightdown.enums     import *
from base.rightdown.tokens    import *
from base.rightdown.textblock import Text


_block_cache        = {}
def BlockForType(blocktype):
  ''' searches this module for the first Block subclass that accepts our blocktype '''
  global _block_cache
  if blocktype in _block_cache:
    return _block_cache[blocktype]
  for x in globals().values():
    if base.utils.IsA(x, Block) and x.tokentype == blocktype:
      _block_cache[blocktype] = x
      return x
  raise rightdown.errors.BadTokenType(blocktype)



###
## for ease of human access, and lacking any code requirements otherwise, blocks are in alphabetic order.
#  block Text is defined in textblock.py



class Code(VerbatimBlock):

  tokentype         = BLOCKTYPE_CODE
  sniptype          = SNIPTYPE_CODE

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<pre>', inline=True))
    if printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, '```', inline=True))
      printer.PrefixUntilClose(self, Imprint(IMPRINT_FORMATTING, ' '*printer.unfenced_indent, inline=True))
    return imprints

  def PrintClose(self, printer, first, last):
    imprints        = []
    if printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, '```', inline=True))
      printer.PrefixUntilClose(self, Imprint(IMPRINT_FORMATTING, ' '*printer.unfenced_indent, inline=True))
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '</pre>', inline=True))
    return imprints



class Blank(Block):

  tokentype         = BLOCKTYPE_BLANK
  empty             = False

  def DigestLines(self, parser):
    self.children   = []
    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<p>', inline=True))
    if printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, '.', inline=True))
    else:
      imprints.append(Imprint(IMPRINT_NARRATIVE, CHAR_NO_BREAK_SPACE, inline=True))
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '</p>', inline=True))
    return imprints



class Comment(VerbatimBlock):

  tokentype         = BLOCKTYPE_COMMENT
  sniptype          = SNIPTYPE_COMMENT



class Heading(Block):

  tokentype         = BLOCKTYPE_HEADING
  level             = 0

  @property
  def debug_sep(self):
    return str(self.level)

  @property
  def tag0(self):
    return '<h' + str(self.level) + '>'

  @property
  def tag1(self):
    return '</h' + str(self.level) + '>'

  def DigestLines(self, parser):
    if not self.children:
      super().DigestLines(parser)
      return

    if self.children[0].tokentype != LINETYPE_HEADER:
      raise rightdown.errors.InvalidChild(self.children[0])

    text            = self.children[0].trimmed
    hashless        = text.lstrip('#')
    self.level      = max(len(text) - len(hashless), 1)
    self.text       = hashless.strip()
    self.children   = []
    self.metadata   = {'title' + str(self.level-1): self.text}

    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, self.tag0, inline=True))
    if printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, '#'*self.level + ' ', inline=True))
    return imprints

  def PrintClose(self, printer, first, last):
    if printer.markup:
       return Imprint(IMPRINT_MARKUP, self.tag1, inline=True)



class Field(Block):

  tokentype         = BLOCKTYPE_FIELD
  attr              = None
  value             = None

  @property
  def empty(self):
    return not self.attr and not self.value and not self.text

  @property
  def debug(self):
    if self.metadata:
      attr, value   = list(self.metadata.items())[0]
      if not value:
        return attr
      if isinstance(value, bool):
        return '{}: {}'.format(attr, str(value))
      return '{}: {}'.format(attr, value)

  def DigestLines(self, parser):
    if not self.children:
      super().DigestLines(parser)
      return

    attrline, rest  = self.children[0], self.children[1:]
    if attrline.tokentype != LINETYPE_ATTRIBUTE:
      raise rightdown.errors.InvalidChild(attrline)
    attr, slop      = attrline.trimmed.split(':', 1)

    attr            = base.utils.Slugify(attr)
    slop            = slop.strip()
    rest            = [x.trimmed for x in rest if x.trimmed]
    if slop:
      rest          = [slop] + rest
    text            = ' '.join(rest)

    self.children   = []
    self.metadata   = {}
    self.metadata[attr] = text or True
    self.value      = text or True
    self.attr       = attr
    self.text       = text

    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<p>', inline=True))
    imprints.append(Imprint(IMPRINT_NARRATIVE, self.attr + ': ', inline=True))
    return imprints

  def PrintClose(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '</p>', inline=True)



class Fragment(Block):

  tokentype         = BLOCKTYPE_FRAGMENT
  index             = 0

  @property
  def debug(self):
    return str(self.index)

  def DigestMetadata(self, parser):
    ''' early stage metadata only '''
    if self.children:
      self.children = parser.blockmaker.Metadata(parser, self.children)
    if self.children and self.children[0].tokentype == BLOCKTYPE_METADATA:
      self.children[0].DigestLines(parser)
      self.metadata = self.children[0].metadata.copy()

  def DigestContent(self, parser, _recursive=False):
    ''' parse the rest of our content '''
    if self.children[0].tokentype == LINETYPE_HARD_BREAK:
      self.children = self.children[1:]

    # it's an extremely esoteric case, but javascript-style comment-end looks exactly like a right arrow.
    # so if we see any COMMENT_END lines in our children, let's retype them with comment-patterns off
    for child in self.children:
      if child.tokentype == LINETYPE_COMMENT_END:
        child.tokentype = parser.linemaker.LineType(parser, child, comments=False)

    if self.children:
      self.children = parser.blockmaker.Content(parser, self.children)

    # this aggregates metadata first child through last
    Block.DigestLines(self, parser)

    # let the metadata block override later metadata once more
    if self.children and self.children[0].tokentype == BLOCKTYPE_METADATA:
      self.metadata.update(self.children[0].metadata)

    # then let our calculated metadata override that
    self.FinalizeMetadata(parser, _recursive=_recursive)

  def DigestLines(self, parser):
    ''' fragments after the first don't get separate calls to D.Metadata and D.Content, just this '''
    self.DigestMetadata(parser)
    self.DigestContent(parser)

  def FinalizeMetadata(self, parser, _recursive=False):
    ''' cleans up our extracted metadata '''
    # titles should populate from title0 onward with no gaps
    when            = None
    titles          = [(key, val) for (key, val) in self.metadata.items() if key.startswith('title')]
    titles.sort(key=lambda x: x[0])
    for key, val in titles:
      del self.metadata[key]
    i               = 0
    if parser.title_metadata_levels:
      for key, val in titles:
        # test for Whens while we're at it
        when        = when or base.When.From(val)
        # keep only N titles
        self.metadata['title'+str(i)] = val
        i           += 1
        if i >= parser.title_metadata_levels:
          break
    if when:
      self.metadata['when'] = when

    # first paragraph should be turned into an excerpt (it hasn't yet been inline-parsed)
    for child in self.children:
      if child.tokentype == BLOCKTYPE_PARAGRAPH and child.text:
        self.metadata['excerpt']  = child.text
        break

    # strip everything to plaintext
    if parser.plaintext_metadata and not _recursive:
      for key, val in self.metadata.items():
        if parser.plaintext_metadata_unless and key in parser.plaintext_metadata_unless:
          continue
        if isinstance(val, str) and val:
          self.metadata[key]  = self._StripStringToPlainText(parser, val) or None
        elif isinstance(val, tuple) or isinstance(val, list):
          self.metadata[key]  = [y for y in [self._StripStringToPlainText(parser, x) for x in val] if y]

  @staticmethod
  def _StripStringToPlainText(parser, val):
    reparsed        = parser.Parse(val, _recursive=True)
    reprinted       = reparsed and rightdown.printers.Printer().Print(reparsed)
    return reprinted or None

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if not first and printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<hr>'))
    if not first and printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, '---'))
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<section>'))
    return imprints

  def PrintClose(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '</section>')



class Link(Block):

  tokentype         = BLOCKTYPE_LINK
  inline            = True
  protocol          = None      # filled if we're a naked url; e.g.:  http://example.com
  email             = None      # filled if we're a naked email; e.g.:  office@octoboxy.com
  flags             = None      # filled if we're: [[flag flag]](alias)
  url               = None
  image             = False

  def __init__(self, **kwargs):
    super().__init__(**kwargs)

  @property
  def debug(self):
    return self.AsText()

  @property
  def empty(self):
    return not self.text and not self.url and not self.email

  @base.utils.cached_property
  def naked(self):
    ''' returns our inner text, fully naked '''
    return self.children and rightdown.printers.Printer().Print(self.children[0]) or ''

  @base.utils.cached_property
  def clothed(self):
    ''' returns our inner text, for output as markdown '''
    return self.children and rightdown.printers.TextPrinter().Print(self.children[0]) or ''

  def AsText(self):
    if self.protocol:
      return self.protocol + (self.url or '')
    if self.email:
      return self.email
    if self.flags:
      return (self.image or '') + '[[' + self.flags + ']](' + (self.url or '') + ')'
    if self.clothed:
      return (self.image or '') + '[' + (self.clothed or '') + '](' + (self.url or '') + ')'
    if self.url:
      return '[(' + self.url + ')]'
    return self.clothed or ''

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if not self.url and not self.email:
      return imprints

    if printer.markup:
      flags         = self.flags and ' '.join(base.utils.Slugify(x) for x in self.flags.split(' '))
      classes       = flags and f' class="{flags}' or ''
      url           = self.url and base.utils.UnifyQuotes(self.url, "'")
      if not url and self.email:
        url         = f'mailto:{self.email}'
      if self.image:
        printer.MuteUntilClose(self)
        naked       = self.naked and base.utils.UnifyQuotes(self.naked, "'")
        alts        = naked and f' alt="{naked}"' or ''
        link        = f'<img{alts}{classes} src="{url}">'
        imprints.append(Imprint(IMPRINT_MARKUP, link, inline=True))
      else:
        link        = f'<a{classes} href="{url}">'
        imprints.append(Imprint(IMPRINT_MARKUP, link, inline=True))
        if not self.clothed:
          imprints.append(Imprint(IMPRINT_NARRATIVE, self.url or self.email, inline=True))
    elif printer.formatting:
      imprings.append(Imprint(IMPRINT_FORMATTING, self.AsText(), inline=True))
    return imprints

  def PrintClose(self, printer, first, last):
    imprints        = []
    if printer.markup and (self.url or self.email) and not self.image:
      imprints.append(Imprint(IMPRINT_MARKUP, '</a>', inline=True))
    return imprints



class List(Block):

  tokentype         = BLOCKTYPE_LIST

  @property
  def empty(self):
    if self.text:
      return False
    if not self.children:
      return True
    if all(x.empty for x in self.children):
      return True
    return False

  @property
  def symbol(self):
    if self.children and self.children[0].tokentype == BLOCKTYPE_ITEM:
      return self.children[0].symbol
    return '-'

  @property
  def debug(self):
    return '{} item{}, start="{}"'.format(len(self.children), len(self.children) != 1 and 's' or '', self.symbol)

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if self.children:
      self.leading_space  = self.children[0].leading_space

  def DigestLines(self, parser):
    if not self.children:
      super().DigestLines(parser)
      return

    # any indented lines should be re-tested to see if they're really list items in disguise
    lines           = [self._ReToken(parser, x) for x in self.children]
    self.children   = []

    item            = None
    for i in range(len(lines)):
      # lines may shrink as we go
      if i >= len(lines):
        break
      line          = lines[i]

      # if it's not a list item type, then it's an indented text, which just adds on to the last item
      if not line.tokentype in (LINETYPE_LIST_BULLET, LINETYPE_LIST_NUMBER, LINETYPE_LIST_ALPHA):
        if item:
          item.children.append(line)
        continue

      # if we don't have a last item, we do now
      if not item:
        item        = ListItem(children=[line])
        self.children.append(item)
        continue

      # if our new item is at the same indent depth as our last item, it's the next item in line
      if line.leading_space == item.leading_space:
        item        = ListItem(children=[line])
        self.children.append(item)
        continue

      # nope, it's starting a whole new list
      list          = List()
      item.children.append(list)

      # find the run of lines that are part of it
      for j in range(i, len(lines)):
        test        = lines[j]
        if test.leading_space >= line.leading_space:
          list.children.append(test)
        else:
          break
      else:
        j           = len(lines) + 1

      # trim those out of our own list
      lines         = lines[:i+1] + lines[j:]

    super().DigestLines(parser)

  def _ReToken(self, parser, line):
    ''' if a line has leading space and was detected as indented, see if it can be turned into a list item '''
    if line.tokentype in (LINETYPE_INDENTED_CODE, LINETYPE_ALMOST_INDENTED):
      testtype      = parser.linemaker.LineType(parser, line, indents=False)
      if testtype in (LINETYPE_LIST_BULLET, LINETYPE_LIST_NUMBER, LINETYPE_LIST_ALPHA):
        line.tokentype  = testtype
    return line

  def PrintOpen(self, printer, first, last):
    symbol          = self.symbol
    imprints        = []
    if printer.markup:
      if symbol.isdigit():
        imprints.append(Imprint(IMPRINT_MARKUP, '<ol start="{}">'.format(symbol)))
      elif symbol.isalpha():
        if symbol.isupper():
          imprints.append(Imprint(IMPRINT_MARKUP, '<ol type="A" start="{}">'.format(ord(symbol) - ord('A') + 1)))
        else:
          imprints.append(Imprint(IMPRINT_MARKUP, '<ol type="a" start="{}">'.format(ord(symbol) - ord('A') + 1)))
      else:
       imprints.append(Imprint(IMPRINT_MARKUP, '<ul>'))
    else:
      imprints.append(Imprint(IMPRINT_BREAK))
    return imprints

  def PrintClose(self, printer, first, last):
    symbol          = self.symbol
    if printer.markup:
      if symbol.isdigit() or symbol.isalpha():
        return Imprint(IMPRINT_MARKUP, '</ol>')
      return Imprint(IMPRINT_MARKUP, '</ul>')


class ListItem(Block):

  tokentype         = BLOCKTYPE_ITEM
  leading_space     = 0
  symbol            = '-'

  @property
  def debug_sep(self):
    return '    '

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if self.children:
      self.leading_space  = self.children[0].leading_space

  def DigestLines(self, parser):
    self.text       = ''
    for child in self.children:
      if not isinstance(child, Line):
        break       # we've reached the sub-lists

      if child.tokentype == LINETYPE_LIST_BULLET:
        self.symbol = child.mergable[0]
        mergable  = child.mergable[1:]
      elif child.tokentype == LINETYPE_LIST_NUMBER:
        self.symbol, mergable  = child.mergable.split('.', 1)
      elif child.tokentype == LINETYPE_LIST_ALPHA:
        self.symbol, mergable  = child.mergable.split('.', 1)
      else:
        mergable  = child.mergable
      mergable      = mergable.lstrip()

      if mergable:
        if self.text:
          self.text += ' '
        self.text   += mergable

    self.children   = [x for x in self.children if isinstance(x, List)]
    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    symbol          = self.symbol
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<li>', inline=True))
    if printer.formatting:
      if symbol.isdigit() or symbol.isalpha():
        imprints.append(Imprint(IMPRINT_FORMATTING, symbol + '. ', inline=True))
      else:
        imprints.append(Imprint(IMPRINT_FORMATTING, symbol + ' ', inline=True))
    return imprints

  def PrintClose(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '</li>', inline=True)



class Metadata(Block):

  tokentype         = BLOCKTYPE_METADATA

  def PrintOpen(self, printer, first, last):
    if not printer.metadata:
      printer.MuteUntilClose(self)
      return
    if printer.formatting:
      return Imprint(IMPRINT_FORMATTING, '---')

  def PrintClose(self, printer, first, last):
    if printer.formatting:
      return Imprint(IMPRINT_FORMATTING, '...')



class MultiField(Block):

  tokentype         = BLOCKTYPE_MULTIFIELD
  attr              = None
  value             = None

  @property
  def debug(self):
    if self.metadata:
      attr, value   = list(self.metadata.items())[0]
      if not value:
        return attr
      if isinstance(value, bool):
        return '{}: {}'.format(attr, str(value))
      if len(value) == 1:
        return '{}: {}'.format(attr, value[0])
      return '{} ({})'.format(attr, len(value))

  def DigestLines(self, parser):
    if not self.children:
      super().DigestLines(parser)
      return

    attrline, data  = self.children[0], self.children[1:]
    if attrline.tokentype != LINETYPE_SLUG:
      raise rightdown.errors.InvalidChild(attrline)
    self.attr       = base.utils.Slugify(attrline.trimmed)

    DeColon         = lambda s: s and s[0] == ':' and s[1:] or s
    self.children   = [MultiFieldItem(text=DeColon(x.trimmed).strip()) for x in data]
    self.value      = [x.text for x in self.children] or True
    self.metadata   = {}
    self.metadata[self.attr] = self.value

    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<dl>'))
      imprints.append(Imprint(IMPRINT_MARKUP, '<dt>'))
    imprints.append(Imprint(IMPRINT_NARRATIVE, self.attr))
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '</dt>'))
    return imprints

  def PrintClose(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '</dl>'))
    return imprints


class MultiFieldItem(Block):

  tokentype         = BLOCKTYPE_MULTIFIELD_ITEM

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<dd>', inline=True))
    if printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, ': ', inline=True))
    return imprints

  def PrintClose(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '</dd>', inline=True)



class Paragraph(Block):

  tokentype         = BLOCKTYPE_PARAGRAPH

  def DigestLines(self, parser):
    if self.children:
      combined      = ' '.join(x.mergable for x in self.children)
      self.text     = combined
      self.children = []
    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    if printer.markup:
      textblock     = self.children and isinstance(self.children[0], Text) and self.children[0] or None
      align         = textblock and textblock.align
      if align:
        return Imprint(IMPRINT_MARKUP, '<p class="' + align.tag + '">', inline=True)
      return Imprint(IMPRINT_MARKUP, '<p>', inline=True)

  def PrintClose(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '</p>', inline=True)



class Quote(Block):

  tokentype         = BLOCKTYPE_QUOTE

  def DigestLines(self, parser):
    if self.children:
      def Strip(s):
        if s and s[:2] == '> ':
          return s[2:]
        if s and s[0] == '>':
          return s[1:]
        return s
      for line in self.children:
        trimmed         = Strip(line.trimmed)
        line.trimmed    = trimmed.strip()
        line.leading_space  += len(trimmed) - len(line.trimmed)
        line.mergable   = Strip(line.mergable).lstrip()
        line.tokentype  = parser.linemaker.LineType(parser, line)
      self.children = parser.blockmaker.Content(parser, self.children)
    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<blockquote>'))
    if printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, '> ', inline=True))
      printer.PrefixUntilClose(self, Imprint(IMPRINT_FORMATTING, '> ', inline=True))
    return imprints

  def PrintClose(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '</blockquote>')



class SoftBreak(Block):

  tokentype         = BLOCKTYPE_SOFT_BREAK
  empty             = False

  def DigestLines(self, parser):
    self.children   = []
    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<div class="center">', inline=True))
    imprints.append(Imprint(IMPRINT_NARRATIVE, '. . .', inline=True))
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '</div>', inline=True))
    return imprints



class SubSupScript(Block):

  tag               = None

  def PrintOpen(self, printer, first, last):
    imprints        = []
    if printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, '^(', inline=True))
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '<' + self.tag + '>', inline=True))
    return imprints

  def PrintClose(self, printer, first, last):
    imprints        = []
    if printer.markup:
      imprints.append(Imprint(IMPRINT_MARKUP, '</' + self.tag + '>', inline=True))
    if printer.formatting:
      imprints.append(Imprint(IMPRINT_FORMATTING, ')', inline=True))
    return imprints


class SubScript(SubSupScript):

  tokentype         = BLOCKTYPE_SUBSCRIPT
  inline            = True
  tag               = 'sub'

class SuperScript(SubSupScript):

  tokentype         = BLOCKTYPE_SUPERSCRIPT
  inline            = True
  tag               = 'sup'



class Table(Block):

  tokentype         = BLOCKTYPE_TABLE
  alignments        = []

  def DigestLines(self, parser):
    # make row for each child
    self.children   = [TableRow(children=[x]) for x in self.children]

    # recurse into them
    super().DigestLines(parser)

    # figure out if we have an alignment row
    if self.children and self.children[0].is_alignment:
      self.alignments = [x.align for x in self.children[0].children]
    elif len(self.children) >= 2 and self.children[1].is_alignment:
      self.children[0].is_header = True
      self.children[0].SetHeaders()
      self.alignments = [x.align for x in self.children[1].children]

    # pass alignments on to all rows
    for child in self.children:
      child.SetAlignments(self.alignments)

  def PrintOpen(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '<table>')

  def PrintClose(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '</table>')


class TableRow(Block):

  tokentype         = BLOCKTYPE_TABLE_ROW

  is_alignment      = False   # True if we're filled with alignment items
  is_header         = False   # True if the row after us is filled with alignment items

  @property
  def debug_sep(self):
    return str(len(self.children))

  @property
  def debug(self):
    if self.is_header:
      return '(header)'
    if self.is_alignment:
      return '(alignments)'

  def DigestLines(self, parser):
    if self.children:
      text          = self.children[0].trimmed
      if text[0] == '|':
        text        = text[1:]
      if text[-1] == '|':
        text        = text[:-1]
      columns       = [s.strip() for s in text.split('|')]
      self.children = []
      for rawtext in columns:
        item        = TableItem()
        item.text   = rawtext
        self.children.append(item)

    super().DigestLines(parser)

    self.is_alignment = self.children and all(bool(x.align) for x in self.children)

  def SetAlignments(self, alignments):
    i               = 0
    for child in self.children:
      child.align   = i < len(alignments) and alignments[i] or ALIGN_DEFAULT
      i             += 1

  def SetHeaders(self):
    for child in self.children:
      child.header  = True

  def PrintOpen(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '<tr>')

  def PrintClose(self, printer, first, last):
    if printer.markup:
      return Imprint(IMPRINT_MARKUP, '</tr>')


class TableItem(Block):

  MULTIDASH         = Grouper(':?-+:?', groupermode=GROUPERMODE_TOTAL)
  MULTEQUAL         = Grouper(':?=+:?', groupermode=GROUPERMODE_TOTAL)
  tokentype         = BLOCKTYPE_TABLE_ITEM
  align             = None
  header            = False

  @property
  def debug(self):
    if self.align:
      return self.align.name

  def DigestLines(self, parser):
    short          = None
    if self.text:
      if self.MULTIDASH(self.text):
        short       = '-'
      elif self.MULTEQUAL(self.text):
        short       = '='
    if short:
      first         = self.text[0] == ':' and ':' or ''
      last          = self.text[-1] == ':' and ':' or ''
      tag           = first + short + last
      if tag in TableColumnAligns:
        self.align  = Aligns(TableColumnAligns(tag).name)
        self.text   = None
    super().DigestLines(parser)

  def PrintOpen(self, printer, first, last):
    if printer.markup:
      tag           = self.header and 'th' or 'td'
      align         = ''
      if self.align and self.align != ALIGN_DEFAULT:
        align       = ' class="' + self.align.tag + '"'
      return Imprint(IMPRINT_MARKUP, '<' + tag + align + '>', inline=True)

  def PrintClose(self, printer, first, last):
    if printer.markup:
      tag           = self.header and 'th' or 'td'
      return Imprint(IMPRINT_MARKUP, '</' + tag + '>', inline=True)
