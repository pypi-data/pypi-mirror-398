#!/opt/local/bin/python

import base

class Error(base.errors.Error):
  ''' base error type for all errors from this library '''


class UnParsable(Error):
  ''' the thing we were asked to parse was no type that we know how to parse '''


class UnPrintable(Error):
  ''' the thing we were asked to print was no type that we know how to print '''


class MisalignedPattern(Error):
  ''' a token pattern matched some character in the token summary that was not at the start of a token '''


class DoubleDigest(Error):
  ''' a token may only have Digest called once '''


class DoubleProcess(Error):
  ''' a token may only have ProcessText called once '''


class UnicodeRangeOverflow(Error):
  ''' the special character generator has run out off the end of our "private use" unicode range '''


class NotImprint(Error):
  ''' expected only zero or more imprint instances, found something else '''


class InvalidChild(Error):
  ''' the child token is not appropriate for where we found it '''


class BadTokenType(Error):
  ''' the token type is not recognized '''


class BadImprintType(Error):
  ''' the imprint type is not recognized '''


class SnipSubbedChars(Error):
  ''' a Snip should have no substituted tokens nor other special characters; use a Text '''


class LingeringText(Error):
  ''' parsing is done yet a token has unparsed .text data '''


class TokenNotStrange(Error):
  ''' the printer was asked to render a "strange" token that did not exist in our list of strange token types '''


class TreeWalkBroken(Error):
  ''' the stack of open/close calls during token tree walking somehow got corrupted '''


class OnePrefixPerToken(Error):
  ''' we only currently support at most one prefix per each token '''
