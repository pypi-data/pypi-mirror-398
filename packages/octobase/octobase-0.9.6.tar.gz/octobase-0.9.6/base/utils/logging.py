#!/opt/local/bin/python
''' Helpers for logging to console. '''

import base
import datetime
import logging
import logging.handlers
import os
import sys
import traceback


def ConfigureLogging(infopath=None, warnpath=None, simplex=None, complex=None, filter=None, level=logging.INFO):
  ''' sets up basic logging

      - infopath -- filepath to an INFO level log file
      - warnpath -- filepath to a WARN level log file
      - simplex  -- logging formatter used for console log, or False to be the same as complex
      - complex  -- logging formatter used for log files
      - filter   -- apply this filter
  '''

  logger          = logging.getLogger()
  if logger.hasHandlers():
    return False

  filepaths       = [x for x in set([infopath, warnpath]) if x]

  for filepath in filepaths:
    dirpath       = os.path.dirname(filepath)
    if dirpath and not os.path.exists(dirpath):
      os.makedirs(dirpath, exist_ok=True)

  complex         = complex or logging.Formatter('%(isotime)s %(name)s %(message)s')

  if simplex is not None and not simplex:
    simplex       = complex
  elif not simplex:
    simplex       = logging.Formatter('%(name)s %(message)s')

  filters         = []
  if filter:
    filters.append(filter)

  console         = ConsoleLogHandler(*filters, simplex=simplex, level=level)

  logger          = logging.getLogger()
  logger.setLevel(level)
  logger.addHandler(console)

  for filepath in filepaths:
    level         = filepath != infopath and logging.WARNING or level
    logfile       = WatchedFileLogHandler(filepath, *filters, level=level, complex=complex)
    logger.addHandler(logfile)

  return True


def WatchedFileLogHandler(filepath, *filters, level=logging.INFO, complex=None):
  ''' returns a new logging handler set up for a detail file '''
  handler       = logging.handlers.WatchedFileHandler(filepath, delay=True)
  handler.set_name(os.path.basename('filepath'))
  handler.setLevel(level)
  handler.setFormatter(complex or logging.Formatter('%(isotime)s %(name)s %(message)s'))
  handler.addFilter(TimeFormatFilter())
  for filter in filters:
    handler.addFilter(filter)
  return handler


def ConsoleLogHandler(*filters, level=logging.INFO, simplex=None):
  ''' returns a new logging handler set up for console '''
  console         = logging.StreamHandler()
  console.set_name('console')
  console.setLevel(level)
  console.setFormatter(simplex or logging.Formatter('%(name)s %(message)s'))
  console.addFilter(TimeFormatFilter())
  for filter in filters:
    console.addFilter(filter)
  return console


class TimeFormatFilter(logging.Filter):
  ''' adds an `isotime` field to the log record, like `asctime` but with microseconds '''

  def filter(self, record):
    timestamp       = datetime.datetime.fromtimestamp(record.created)
    timezoned       = base.utils.LocalTime(timestamp)
    record.isotime  = timezoned.isoformat()
    return True



def Log(tag, message, level=logging.INFO, **extra):
  ''' Logs a message.  The "tag" should be a sluglike label for the type of log message. '''
  tag             = tag and base.utils.Slugify(tag).upper() or None
  if level != logging.INFO:
    tag           = (tag and (tag + '.') or '') + logging.getLevelName(level)

  logger          = logging.getLogger(tag)
  if logger.hasHandlers():
    logging.getLogger(tag).log(level, message or '', extra=extra)
  elif level >= logging.INFO:
    things        = [x for x in (tag, message) if x]
    sys.stderr.write(' '.join(things) + '\n')



def LogTraceback(error=None, limit=12):
  ''' Logs a stack trace to the console. '''
  exc_type, exc_value, exc_traceback = error and sys.exc_info() or (None, None, None)
  limit           += 1
  raw             = exc_traceback and traceback.extract_tb(exc_traceback, limit=limit) or traceback.extract_stack(limit=limit)
  lines           = traceback.format_list(raw)
  if lines and not exc_traceback:
    lines         = lines[:-1]
  if lines:
    Log('TRACEBACK', '\n' + '\n'.join(lines))


def LogException(exception):
  ''' Logs an exception to the console. '''
  last            = traceback.extract_tb(exception.__traceback__)[-1]
  filename        = last.filename
  text            = str(exception).replace('\n', '\n . ')
  base.utils.Log(
      'EXCEPTION', '{filename}:{lineno}\n - {line}\n - {text}'.format(
          filename=filename, lineno=last.lineno, line=last.line, name=last.name, text=text),
      level=logging.WARN)


def XYZZY(*messages):
  ''' Logs a debug message to the console.

      The function name "XYZZY" is chosen to be easy to search for in a codebase,
      to help reduce debug code being committed into production.
  '''
  if not messages:
    Log('XYZZY', None)
  elif len(messages) == 1:
    Log('XYZZY', repr(messages[0]))
  else:
    message       = ''
    for i in range(len(messages)):
      message     = message + '\n {:2d}: '.format(i) + repr(messages[i]).rstrip()
    Log('XYZZY', message)
