#!/opt/local/bin/python

import base

from base                   import rightdown
from base.rightdown.enums   import *


class RightDown(rightdown.tokens.Block):

  tokentype         = BLOCKTYPE_RIGHTDOWN

  metadata          = None    # dict of structured data extracted from the first document fragment

  children          = None    # list of fragments; collectively, the fully-parsed document tree

  # warnings that may be triggered during parsing (rare)
  has_illegal_chars = False   # reserved characters in input text
  has_barf_chars    = False   # reserved characters in output text -- likely indicates bugs in rightdown
  has_squiguelgmas  = False   # an easter-egg that exists for testing was triggered

  ###
  ## instantiate a RightDown with one of these two helpers
  #

  @classmethod
  def Load(klass, filepath, **kwargs):
    ''' opens a filepath, ingests the contents, and returns a RightDown instance.
        keyword args are passed as configuration options to the Parser
    '''
    with open(filepath, 'rt') as file:
      return klass.From(file, **kwargs)

  @classmethod
  def From(klass, thing, **kwargs):
    ''' ingests text, returns a RightDown instance.
        keyword args are passed as configuration options to the Parser
    '''
    return rightdown.parser.Parser(**kwargs).Parse(thing or '')

  ###
  ## useful things you can do with your RightDown once you have it
  #

  def Text(self, **kwargs):
    ''' renders the document to fully-normalized rightdown plaintext '''
    return rightdown.printers.TextPrinter(**kwargs).Print(self) or ''

  def Html(self, **kwargs):
    ''' renders the document to a string of HTML '''
    return rightdown.printers.HtmlPrinter(**kwargs).Print(self) or ''

  def Links(self):
    ''' returns a list of all the Link tokens in the document '''
    return self.All(BLOCKTYPE_LINK)

  def Save(self, filepath):
    ''' writes our normalized plain text content to the given filepath '''
    with open(filepath, 'wt') as file:
      file.write(self.Text())

  ###
  ## mechanical
  #

  def __init__(self):
    self.metadata   = {}
    self.children   = []

  def Validate(self):
    ''' tests our structure for flaws; raises on finding any '''
    for child in self.children:
      if not child.tokentype == BLOCKTYPE_FRAGMENT:
        raise rightdown.errors.InvalidChild(child)
      child.Validate()
