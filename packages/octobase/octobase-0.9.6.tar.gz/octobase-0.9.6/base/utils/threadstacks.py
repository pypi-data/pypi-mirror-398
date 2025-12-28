#!/opt/local/bin/python

import base

from .decorators              import classproperty


class ThreadStack:
  ''' helper methods to manage a thread-local stack of class instances '''

  @classproperty
  def threadstack(klass):
    ''' returns (or creates) a thread-local stack of this class's instances '''
    tld             = base.utils.ThreadLocalDict()
    obname          = base.utils.ObjectName(klass)
    threadstack     = tld.get(obname)
    if threadstack is None:
      threadstack   = []
      tld[obname]   = threadstack
    return threadstack

  @classmethod
  def ThreadStack(klass):
    ''' returns or creates a version of ourself based on our threadstack '''
    return klass.ThreadPeek() or klass()

  @classmethod
  def ThreadPeek(klass):
    ''' retrieves the current instance at the top of our threadstack '''
    threadstack     = klass.threadstack
    return threadstack and threadstack[-1] or None

  @staticmethod
  def ThreadDupe(klass, other):
    if other and issubclass(klass, base.Thing):
      return other.Dupe()
    return klass()

  def __enter__(self):
    zelf            = self
    threadstack     = zelf.threadstack
    if threadstack and isinstance(threadstack[-1], base.Thing):
      zelf          = threadstack[-1].Dupe()
    threadstack.append(zelf)
    return zelf

  def __exit__(self, exc_type, exc_value, exc_traceback):
    threadstack     = self.threadstack
    if threadstack:
      threadstack.pop()
