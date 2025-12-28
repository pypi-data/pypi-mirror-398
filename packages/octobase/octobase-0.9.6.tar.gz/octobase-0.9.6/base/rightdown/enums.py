#!/opt/local/bin/python

import base

# print modes our command line knows how to handle
base.Enum.Define(('PRINTMODE', 'PrintModes'), (
    ('HTML',                'html',           'HTML'),
    ('Naked Text',          'naked',          'NAKED'),
    ('Normalized Text',     'text',           'TEXT'),
    ('Debug',               'debug',          'DEBUG'),
))


# stages of processing, in case you want to cut parsing short for reasons of performance or testing
base.Enum.Define(('STAGE', 'Stages'), (
    ('Lines',                 1),       # rd.lines exists
    ('Fragments',             2),       # rd.fragments exists
    ('Early Metadata',        3),       # rd.metadata contains most metadata from fragment 0
    ('ReParsed',              4),       # if metadata is allowed to trigger a reparse, here's where it happens
    ('Metadata',              5),       # fragment 0 metadata is available
    ('Blocks',                6),       # all fragments broken down into blocks
    ('Inlines',               7),       # all text has been processed
    ('Parsed',                8),       # token tree has been validated
    ('Imprints',              9),       # (printing) tokens are serialized for the print settings
    ('Filtered',             10),       # (printing) last output filtering is applied
    ('Done',                 11),       # (printing) done
))


# text alignment
base.Enum.Define(('ALIGN', 'Aligns'), (
    ('Default',             None),
    ('Left',                'left'),
    ('Right',               'right'),
    ('Center',              'center'),
    ('Justify',             'justify'),
))


# table equivalent of the same thing
base.Enum.Define(('TABALIGN', 'TableColumnAligns'), (
    ('Default',             '-'),
    ('Left',                ':-'),
    ('Right',               '-:'),
    ('Center',              ':-:'),
    ('Justify',             ':=:'),
))


# used to vary how we compile different text substitution patterns
base.Enum.Define(('SUBMODE', 'SubModes'), (
    'All',
    'Solo',
    'Open',
    'Close',
    'NotOpen',
))


# let's keep all the special characters we recognize in one list
base.Enum.Define(('CHAR', 'Chars'), (
    ('No Break Space',      ' '),
    ('Left Tick',           '‘'),
    ('Right Tick',          '’'),
    ('Left Quote',          '“'),
    ('Right Quote',         '”'),
    ('Ellipsis',            '…'),
    ('Endash',              '–'),
    ('Emdash',              '—'),
    ('Plus Minus',          '±'),
    ('Not Equal',           '≠'),
    ('Almost Equal',        '≈'),
    ('Right Arrow',         '→'),
    ('Left Arrow',          '←'),
    ('Bi Arrow',            '↔'),
    ('One Half',            '½'),
    ('One Third',           '⅓'),
    ('Two Thirds',          '⅔'),
    ('One Quarter',         '¼'),
    ('Three Quarters',      '¾'),
    ('One Fifth',           '⅕'),
    ('Two Fifths',          '⅖'),
    ('Three Fifths',        '⅗'),
    ('Four Fifths',         '⅘'),
    ('One Sixth',           '⅙'),
    ('Five Sixths',         '⅚'),
    ('One Eighth',          '⅛'),
    ('Three Eighths',       '⅜'),
    ('Five Eigths',         '⅝'),
    ('Seven Eights',        '⅞'),
    ('Copyright',           '©'),
    ('Trademark',           '™'),
    ('Registered',          '®'),
    ('Division',            '÷'),
    ('Del',                 '∇'),
))


###
## token tags
#  to filter the token tree to only tokens of a certain type, see method Block.All()
#  use this, for instance, to find all the Link blocks in a document, or all the
#  template references


base.Enum.Define(('LINETYPE', 'LineTypes'), (
    ('Empty',               'emt,'),    # totally empty line

    ('Hard Break',          'br0,'),    # ---
    ('Soft Break',          'br1,'),    # ...
    ('Blank',               'blk,'),    # .

    ('Fence',               'fnc,'),    # ```

    ('Comment Line',        'cml,'),    # prefixed with //
    ('Comment Start',       'cm0,'),    # prefixed with /*
    ('Comment End',         'cm1,'),    # suffixed with */

    ('Header',              'hdr,'),    # prefixed with #
    ('Quote',               'qte,'),    # prefixed with >
    ('Table',               'tbl,'),    # contains at least two |

    ('Slug',                'slg,'),
    ('Attribute',           'atr,'),    # slug :
    ('Value',               'val,'),    # prefixed with :

    ('List Bullet',         'lbt,'),    # prefixed with -, +, or *
    ('List Number',         'lnb,'),    # prefixed with digit(s) .
    ('List Alpha',          'lal,'),    # prefixed with alpha .

    ('Indented Code',       'ind,'),    # fully indented to code level
    ('Almost Indented',     'ain,'),    # indented at least one tabstop but less than full code level
    ('Text',                'tex,'),    # normal line of text
))


base.Enum.Define(('BLOCKTYPE', 'BlockTypes'), (
    ('Blank',               'bnk,'),    # .
    ('Code',                'cod,'),    # code block, either fenced or indented
    ('Comment',             'cmt,'),    # entire block of comment
    ('Field',               'fld,'),    # slug: value
    ('Fragment',            'frg,'),    # immediate children of the RightDown instance
    ('Heading',             'hed,'),    # title, subtitle, etc.
    ('Item',                'lii,'),    # child of a List
    ('Link',                'lnk,'),    # out-of-document reference
    ('List',                'lst,'),    # any type of list -- bullet, number, or alpha
    ('Metadata',            'mtd,'),    # invisible metadata at the beginning of a Fragment
    ('MultiField Item',     'mfi,'),    # item within a multifield
    ('MultiField',          'mfd,'),    # slug: list of values
    ('Paragraph',           'par,'),    # plain ol' text block
    ('Quote',               'qot,'),    # >
    ('RightDown',           'rd_,'),    # the top-level RightDown instance itself
    ('Soft Break',          'sbr,'),    # . . .
    ('Subscript',           'sub,'),    # piece of text that should be sub-scripted
    ('Superscript',         'sup,'),    # piece of text that should be super-scripted
    ('Table Item',          'tbi,'),    # child of a Table Row
    ('Table Row',           'tbr,'),    # child of a Table
    ('Table',               'tab,'),    # contains one or more Table Rows
    ('Text',                'txt,'),    # a formatted line of text
))


base.Enum.Define(('SNIPTYPE', 'SnipTypes'), (
    ('code',                'cds,'),    # text that should be emitted in fixed-width typeface
    ('comment',             'com,'),    # text that should not be emitted at all
    ('html',                'htm,'),    # snippet of HTML that was detected in the document
    ('icon',                'ico,'),    # icon reference
    ('plain',               'ezy,'),    # plain ol' text, ready to print
    ('template',            'tpl,'),    # template language markup that was detected in the document
    ('format up',           'fup,',     'FORMAT_UP'),       # in-line formatting:  count goes up
    ('format dn',           'fdn,',     'FORMAT_DOWN'),     # in-line formatting:  count goes down
    ('format md',           'fmd,',     'FORMAT_MIDDLE'),   # in-line formatting:  count toggles
    ('format lt',           'flt,',     'FORMAT_LEFT'),     # in-line formatting:  paragraph left
    ('format rt',           'frt,',     'FORMAT_RIGHT'),    # in-line formatting:  paragraph right
))


###
## Imprints are not tokens, but are what the token tree serializes to during printing
#


base.Enum.Define(('IMPRINT', 'ImprintTypes'), (
    ('Markup',              'htm,'),    # markup language
    ('Formatting',          'frm,'),    # formatting text
    ('Narrative',           'txm,'),    # actual text content
    ('Inert',               'nrt,'),    # pre-rendered and pre-escaped content
    ('Break',               'brk,'),    # indicates the end of a block
))
