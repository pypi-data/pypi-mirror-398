#!/opt/local/bin/python

import base

from base                 import rightdown
from base.regexp          import *
from base.rightdown.enums import *


###
## Line patterns
#


LINE_PATTERNS       = (
    (LINETYPE_HARD_BREAK,        '---\s*$'),
    (LINETYPE_SOFT_BREAK,        '\.\s?\.\s?\.\s*$'),
    (LINETYPE_BLANK,             '\.\s*$'),
    (LINETYPE_FENCE,             '```'),

    (LINETYPE_COMMENT_LINE,      '//'),
    (LINETYPE_COMMENT_LINE,      '/\*.*\*/\s*$'),    # must come before COMMENT_STARTs and _ENDs
    (LINETYPE_COMMENT_LINE,      '<!--.*-->\s*$'),   # must come before COMMENT_STARTs and _ENDs
    (LINETYPE_COMMENT_START,     '/\*'),
    (LINETYPE_COMMENT_START,     '<!--'),
    (LINETYPE_COMMENT_END,       '.*\*/\s*$'),
    (LINETYPE_COMMENT_END,       '.*-->\s*$'),

    (LINETYPE_HEADER,            '#'),
    (LINETYPE_QUOTE,             '>'),
    (LINETYPE_VALUE,             ':'),
    (LINETYPE_TABLE,             '.*\|.+\|'),
    (LINETYPE_LIST_BULLET,       '[-+\*]' + Group(Or('$', '\s+[^\s]'))),
    (LINETYPE_LIST_NUMBER,       '\d+\.' + Group(Or('$', '\s+[^\s]'))),
    (LINETYPE_LIST_ALPHA,        '[a-zA-Z]\.' + Group(Or('$', '\s+[^\s]'))),
    (LINETYPE_SLUG,              '[a-z0-9_]+$'),
    (LINETYPE_ATTRIBUTE,         '[a-z0-9_]+:'),
)

LINE_PATTERNS_NO_COMMENT  = [
    (x,y) for x,y in LINE_PATTERNS if not x in (LINETYPE_COMMENT_LINE, LINETYPE_COMMENT_START, LINETYPE_COMMENT_END)]


###
## Block patterns
#


ANYTOKEN            = Group('\w\w\w,')
ANYINDENT           = Group(Or(LINETYPE_INDENTED_CODE, LINETYPE_ALMOST_INDENTED))
FRAGBREAK           = Group(Or(LINETYPE_HARD_BREAK, BLOCKTYPE_FRAGMENT, '$'), GROUPTYPE_LOOK_AHEAD)
BLOCKSTART          = Group(Or('^', LINETYPE_EMPTY))
BLOCKBREAK          = Group(Or(LINETYPE_EMPTY, '$'), GROUPTYPE_LOOK_AHEAD)


# this matches against the entire block of metadata at the top of a fragment
METADATA_PATTERN    = LINETYPE_HARD_BREAK + Capture(
    Group(Or(
        LINETYPE_SLUG, LINETYPE_ATTRIBUTE, LINETYPE_VALUE, LINETYPE_INDENTED_CODE, LINETYPE_ALMOST_INDENTED
    )) + '*?'
) + LINETYPE_SOFT_BREAK


# these are used to break a document into the highest level blocks
FRAGMENT_PATTERNS   = (
    (BLOCKTYPE_COMMENT,     GROUPERMODE_SEARCH,   (
        LINETYPE_COMMENT_LINE
    )),
    (BLOCKTYPE_COMMENT,     GROUPERMODE_SEARCH,   (
        LINETYPE_COMMENT_START + ANYTOKEN + '*?' + LINETYPE_COMMENT_END
    )),
    (BLOCKTYPE_CODE,        GROUPERMODE_SEARCH,   (
        LINETYPE_FENCE + ANYTOKEN + '*?' + LINETYPE_FENCE
    )),
    (BLOCKTYPE_CODE,        GROUPERMODE_SEARCH,   (
        Group(LINETYPE_EMPTY, GROUPTYPE_LOOK_BEHIND) +
        LINETYPE_INDENTED_CODE +
        Group(Or(LINETYPE_INDENTED_CODE, LINETYPE_EMPTY)) + '*' +
        Group(Or(LINETYPE_EMPTY, LINETYPE_HARD_BREAK, BLOCKTYPE_FRAGMENT, '$'), GROUPTYPE_LOOK_AHEAD)
    )),
    (BLOCKTYPE_FRAGMENT,    GROUPERMODE_SEARCH,   (
        ANYTOKEN + '+?' + FRAGBREAK
    )),
)


# these are the patterns for the items inside the metadata block
FIELDLIST_PATTERNS  = (
    (BLOCKTYPE_FIELD,       GROUPERMODE_SEARCH,   (
        LINETYPE_ATTRIBUTE + ANYINDENT + '*'
    )),
    (BLOCKTYPE_MULTIFIELD,  GROUPERMODE_SEARCH,   (
        LINETYPE_SLUG + Group(LINETYPE_VALUE) + '*'
    )),
)


# these are the patterns for the types of blocks that make up the general flow of content
CONTENT_PATTERNS    = (
    (BLOCKTYPE_HEADING,     GROUPERMODE_SEARCH,   (
        LINETYPE_HEADER
    )),
    (BLOCKTYPE_SOFT_BREAK,  GROUPERMODE_SEARCH,   (
        Group(LINETYPE_SOFT_BREAK) + '+' + BLOCKBREAK
    )),
    (BLOCKTYPE_BLANK,       GROUPERMODE_SEARCH,   (
        Group(LINETYPE_BLANK) + '+' + BLOCKBREAK
    )),
    (BLOCKTYPE_QUOTE,       GROUPERMODE_SEARCH,   (
        LINETYPE_QUOTE + Group(ANYTOKEN) + '*?' + BLOCKBREAK
    )),
    (BLOCKTYPE_TABLE,       GROUPERMODE_SEARCH,   (
        Group(LINETYPE_TABLE) + '+' + BLOCKBREAK
    )),
    (BLOCKTYPE_LIST,        GROUPERMODE_SEARCH,   (
        Group(Or(
            LINETYPE_LIST_BULLET, LINETYPE_LIST_NUMBER, LINETYPE_LIST_ALPHA
        )) + Group(Or(
            LINETYPE_LIST_BULLET, LINETYPE_LIST_NUMBER, LINETYPE_LIST_ALPHA,
            LINETYPE_INDENTED_CODE, LINETYPE_ALMOST_INDENTED
        )) + '*' + BLOCKBREAK
    )),
    (BLOCKTYPE_FIELD,       GROUPERMODE_SEARCH,   (
        BLOCKSTART + Capture(
            LINETYPE_ATTRIBUTE + ANYINDENT + '*'
        ) + BLOCKBREAK
    )),
    (BLOCKTYPE_MULTIFIELD,  GROUPERMODE_SEARCH,   (
        BLOCKSTART + Capture(LINETYPE_SLUG + Group(LINETYPE_VALUE) + '+') + BLOCKBREAK
    )),
)


###
## Text patterns
#

# pattern building helpers

SPACE               = r'\s'
SPACE0              = Group(Or('^', SPACE))
SPACE1              = Group(Or(SPACE, '$'))
LB_SPACE            = Group(Or('^', Group(SPACE, grouptype=GROUPTYPE_LOOK_BEHIND)))
LA_SPACE            = Group(Or('$', Group(SPACE, grouptype=GROUPTYPE_LOOK_AHEAD)))

NOTSPACE            = r'\S'
NOTSPACE0           = Group(Or('^', NOTSPACE))
NOTSPACE1           = Group(Or(NOTSPACE, '$'))
LB_NOTSPACE         = Group(Or('^', Group(NOTSPACE, grouptype=GROUPTYPE_LOOK_BEHIND)))
LA_NOTSPACE         = Group(Or('$', Group(NOTSPACE, grouptype=GROUPTYPE_LOOK_AHEAD)))

ALNUM               = r'\w'
ALNUM0              = Group(Or('^', ALNUM))
ALNUM1              = Group(Or(ALNUM, '$'))
LB_ALNUM            = Group(Or('^', Group(ALNUM, grouptype=GROUPTYPE_LOOK_BEHIND)))
LA_ALNUM            = Group(Or('$', Group(ALNUM, grouptype=GROUPTYPE_LOOK_AHEAD)))

NOTALNUM            = r'\W'
NOTALNUM0           = Group(Or('^', NOTALNUM))
NOTALNUM1           = Group(Or(NOTALNUM, '$'))
LB_NOTALNUM         = Group(Or('^', Group(NOTALNUM, grouptype=GROUPTYPE_LOOK_BEHIND)))
LA_NOTALNUM         = Group(Or('$', Group(NOTALNUM, grouptype=GROUPTYPE_LOOK_AHEAD)))

NOTALNUMSPC         = '[^\s\w]*?'

OPTIONAL_FORMATTING = r'[~_=\\*]*?'     # this needs to match any symbol in SNIPTYPE_FORMAT_UP / _DOWN

# decorators that help in TEXT_SUBSTITUTIONS

TEXT_SUB_DECORATORS = {
    SUBMODE_ALL:      lambda x: Capture(x),
    SUBMODE_SOLO:     lambda x: NOTALNUM0 + Capture(x) + NOTALNUM1,
    SUBMODE_OPEN:     lambda x: SPACE0 + OPTIONAL_FORMATTING + Capture(x),
    SUBMODE_CLOSE:    lambda x: Capture(x) + NOTALNUM1,
    SUBMODE_NOTOPEN:  lambda x: NOTSPACE + OPTIONAL_FORMATTING + Capture(x),
}

# couple patterns we match early

SIMPLE_PATTERN_NBSP = (r'\\ ', CHAR_NO_BREAK_SPACE)
CODE_SNIP_PATTERN   = '`' + Capture('.*?', name='text') + '`'

# pieces of a link

IMAGE               = Capture('!?', name='image')
FLAGS               = Capture('.*?', name='flags')
TITLE               = Capture('.*?', name='text')
URL                 = Capture('.*?', name='url')
PROTOCOL            = Capture(Or('https?:/', 'mailto:'), name='protocol')
EMAIL               = Capture('[-+._%a-zA-Z0-9]+@' + Group('[-a-zA-Z0-9]+\.') + '+[a-zA-Z]{2,}', name='email')

# HTML

HTMLATTR0           = '\\s*\\w+\\s*' + Optional('=' + '\\s*".*?"')
HTMLATTR1           = '\\s*\\w+\\s*' + Optional('=' + "\\s*'.*?'")
HTMLTAGOPEN         = '<\\w+' + Group(Or(HTMLATTR0, HTMLATTR1)) + '*\\s*/?>'
HTMLTAGCLOSE        = '</\\w+\s*>'
HTMLTAGCOMMENT      = '<!.*?>'

HTML_TH             = '<sup><u>th</u></sup>'
HTML_ST             = '<sup><u>st</u></sup>'
HTML_ND             = '<sup><u>nd</u></sup>'
HTML_RD             = '<sup><u>rd</u></sup>'

## these patterns identify range-based parts of text
#
# the entire pattern is extracted, meaning we must use lookaheads/behinds for any non-snipped content

TEXTBLOCK_PATTERNS  = (
    (BLOCKTYPE_LINK,            IMAGE + r'\[\[' + FLAGS + r'\]\]\(' + URL + r'\)'),
    (BLOCKTYPE_LINK,            IMAGE + r'\['   + TITLE +   r'\]\(' + URL + r'\)'),
    (BLOCKTYPE_LINK,            IMAGE + r'\[\(' + URL   + r'\)\]'),
    (BLOCKTYPE_LINK,            LB_SPACE + PROTOCOL + URL + LA_SPACE),
    (BLOCKTYPE_LINK,            LB_SPACE + EMAIL),
    (SNIPTYPE_ICON,             r'\(\(' + Capture('[-\w\d\s]+', name='text') + '\)\)'),
    (SNIPTYPE_TEMPLATE,         Capture(r'{%.*?%}', name='text')),
    (SNIPTYPE_TEMPLATE,         Capture(r'{{.*?}}', name='text')),
    (SNIPTYPE_COMMENT,          Capture(r'{#.*?#}', name='text')),
    (SNIPTYPE_HTML,             Capture(HTMLTAGOPEN, name='text')),
    (SNIPTYPE_HTML,             Capture(HTMLTAGCLOSE, name='text')),
    (SNIPTYPE_COMMENT,          Capture(HTMLTAGCOMMENT, name='text')),
    (BLOCKTYPE_SUBSCRIPT,       LB_NOTSPACE + '~' + r'\(' + Capture('.*?', name='text') + r'\)' + LA_SPACE),
    (BLOCKTYPE_SUPERSCRIPT,     LB_NOTSPACE + '\\^' + r'\(' + Capture('.*?', name='text') + r'\)' + LA_SPACE),
    (BLOCKTYPE_SUPERSCRIPT,     LB_NOTSPACE + '\\^' + Capture(r'.+?', name='text') + LA_SPACE),
    # *DISABLED BY INTENTION*
    #   because mid-word strikethrough is more useful
    # (BLOCKTYPE_SUBSCRIPT,     NOTSPACE + '~' + Capture(r'\w+', name='sub') + SPACE),
)

## these simple substitutions apply after the text blocks have been found
#
# tuples are:  (pattern, naked, text, html)
#   if html is missing, naked will be used
#   if text is missing, pattern will be used
TEXT_SUBSTITUTIONS  = {
    SUBMODE_ALL:    (
        SIMPLE_PATTERN_NBSP,
        ('\n',                  '\n',                   '\n',             '<br>'),
        (r'\.\.\.',             CHAR_ELLIPSIS,          '...'),
        ('<-->',                CHAR_BI_ARROW),
        ('-->',                 CHAR_RIGHT_ARROW),
        ('<--',                 CHAR_LEFT_ARROW),
        ('---',                 CHAR_EMDASH),
        ('--',                  CHAR_ENDASH),
        (r'\+/-',               CHAR_PLUS_MINUS),
        ('!=',                  CHAR_NOT_EQUAL),
        ('=/=',                 CHAR_NOT_EQUAL),
        ('~=',                  CHAR_ALMOST_EQUAL),
    ),
    SUBMODE_SOLO:   (
        ('1/2',                 CHAR_ONE_HALF),
        ('1/3',                 CHAR_ONE_THIRD),
        ('2/3',                 CHAR_TWO_THIRDS),
        ('1/4',                 CHAR_ONE_QUARTER),
        ('3/4',                 CHAR_THREE_QUARTERS),
        ('1/5',                 CHAR_ONE_FIFTH),
        ('2/5',                 CHAR_TWO_FIFTHS),
        ('3/5',                 CHAR_THREE_FIFTHS),
        ('4/5',                 CHAR_FOUR_FIFTHS),
        ('1/6',                 CHAR_ONE_SIXTH),
        ('5/6',                 CHAR_FIVE_SIXTHS),
        ('1/8',                 CHAR_ONE_EIGHTH),
        ('3/8',                 CHAR_THREE_EIGHTHS),
        ('5/8',                 CHAR_FIVE_EIGTHS),
        ('7/8',                 CHAR_SEVEN_EIGHTS),
        (r'\(c\)',              CHAR_COPYRIGHT,         '(c)'),
        (r'\(tm\)',             CHAR_TRADEMARK,         '(tm)'),
        (r'\(r\)',              CHAR_REGISTERED,        '(r)'),
        ( '0' + Capture('st'),  'st',                   'st',             HTML_ST),
    ),
    SUBMODE_OPEN:   (
        ("'",                   CHAR_LEFT_TICK),
        ('"',                   CHAR_LEFT_QUOTE),
    ),
    SUBMODE_CLOSE:  (
        ('11' + Capture('th'),  'th',                   'th',             HTML_TH),
        ('12' + Capture('th'),  'th',                   'th',             HTML_TH),
        ('13' + Capture('th'),  'th',                   'th',             HTML_TH),
        ( '0' + Capture('th'),  'th',                   'th',             HTML_TH),
        ( '1' + Capture('st'),  'st',                   'st',             HTML_ST),
        ( '2' + Capture('nd'),  'nd',                   'nd',             HTML_ND),
        ( '3' + Capture('rd'),  'rd',                   'rd',             HTML_RD),
        ( '4' + Capture('th'),  'th',                   'th',             HTML_TH),
        ( '5' + Capture('th'),  'th',                   'th',             HTML_TH),
        ( '6' + Capture('th'),  'th',                   'th',             HTML_TH),
        ( '7' + Capture('th'),  'th',                   'th',             HTML_TH),
        ( '8' + Capture('th'),  'th',                   'th',             HTML_TH),
        ( '9' + Capture('th'),  'th',                   'th',             HTML_TH),
    ),
    SUBMODE_NOTOPEN:  (
        ("'",           CHAR_RIGHT_TICK),
        ('"',           CHAR_RIGHT_QUOTE),
    ),
}


## penultimate patterns
#
# here we are NOT extracting the entire pattern, we're doing a substitution
# only on the captured content

C                   = Capture(Group(Or('~', '_', '=', '\\*')) + '+', name='text')
UPDOWN_PATTERNS    = (
    (SNIPTYPE_FORMAT_UP,        SPACE0 + NOTALNUMSPC + C + NOTALNUMSPC + ALNUM),
    (SNIPTYPE_FORMAT_DOWN,      ALNUM + NOTALNUMSPC + C + NOTALNUMSPC + SPACE1),
    (SNIPTYPE_FORMAT_MIDDLE,    Capture('~+', name='text')),
)


## these patterns apply last
#
# the entire pattern is extracted, meaning we must use lookaheads/behinds for any non-snipped content

LEFTRIGHT_PATTERNS  = (
#     (SNIPTYPE_FORMAT_UP,        LB_SPACE + Capture(Group(Or('~', '_', '=', '\\*')) + '+', name='text') + LA_NOTSPACE),
#     (SNIPTYPE_FORMAT_DOWN,      LB_NOTSPACE + Capture(Group(Or('~', '_', '=', '\\*')) + '+', name='text') + LA_SPACE),
    (SNIPTYPE_FORMAT_LEFT,      Capture(r'^<-', name='text') + LA_SPACE),
    (SNIPTYPE_FORMAT_RIGHT,     Capture(r'^->', name='text') + LA_SPACE),
    (SNIPTYPE_FORMAT_LEFT,      LB_SPACE + Capture(r'<-$', name='text')),
    (SNIPTYPE_FORMAT_RIGHT,     LB_SPACE + Capture(r'->$', name='text')),
)
