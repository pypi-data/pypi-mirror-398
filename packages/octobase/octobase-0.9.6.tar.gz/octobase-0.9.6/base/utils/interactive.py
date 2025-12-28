#!/opt/local/bin/python
''' Helper functions related to the interactive python console. '''

import base
import code
import fcntl
import inspect
import logging
import os
import string
import sys
import termios
import threading


def ReadKeystroke(echo=True, limit_to=None, enter_equals=None):
  ''' Read a single keystroke from the keyboard.
      Based on:
        https://docs.python.org/2/faq/library.html#how-do-i-get-a-single-keypress-at-a-time
  '''
  fd          = sys.stdin.fileno()

  oldterm     = termios.tcgetattr(fd)
  newattr     = termios.tcgetattr(fd)
  newattr[3]  = newattr[3] & ~termios.ICANON & ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSANOW, newattr)

  oldflags    = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

  if not limit_to:
    limit_to  = string.printable + '\n'

  c           = None
  try:
    while not c in limit_to:
      while True:
        try:
          c   = sys.stdin.read(1)
          break
        except IOError:
          pass
      if enter_equals and c == '\n':
        c       = enter_equals
  finally:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

  if echo:
    sys.stderr.write(c + '\n')

  return c



def AskStdInForPermission(prompt='(y/N)? ', default='N'):
  ''' Accepts a single keystroke, returns True if the user answers yes, False for no. '''
  sys.stderr.write(prompt)
  sys.stderr.flush()
  try:
    return ReadKeystroke(limit_to=('y', 'Y', 'n', 'N'), enter_equals=default) in ('y', 'Y')
  except KeyboardInterrupt:
    sys.stderr.write('\n')



_interactive_lock     = threading.RLock()
def _GoingInteractive(banner, namespace):
  ''' A method that can be monkey-patched to add context to the GoInteractive() session '''
  return banner

def GoInteractive(**kwargs):
  ''' Go interactive in the console window with all globals() and locals() in scope. '''
  if not os.isatty(sys.stdin.fileno()):
    base.utils.Log('BASE', 'GoInteractive() called in a non-interactive process.', level=logging.ERROR)
    return
  try:
    stack         = inspect.stack()
    frame         = stack[1][0]
    namespace     = frame.f_globals.copy()
    namespace.update(frame.f_locals)
  finally:
    del frame
  banner          = '\n*** Interactive Console ***\n'
  banner          = _GoingInteractive(banner, namespace)
  banner          += 'Terminate the session with CTRL-D.\n'
  if kwargs:
    namespace.update(kwargs)
  with _interactive_lock:
    code.interact(banner=banner, local=namespace)



def WaitForInteractive():
  ''' Pauses the current thread until the GoInteractive() console has closed. '''
  with _interactive_lock:
    pass
