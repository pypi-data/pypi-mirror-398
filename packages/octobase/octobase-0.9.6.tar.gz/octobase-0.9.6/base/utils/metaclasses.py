#!/opt/local/bin/python
''' Metaclass types for your classes. '''

import base
import threading


class Singleton(type):
  ''' Metaclass to make any other class into a global singleton.
      You may subclass a singleton class and the subclass is a separate singleton.
  '''

  _singleton_lock   = threading.RLock()
  _singleton_inst   = {}

  def __call__(klass, *args, **kwargs):
    with klass._singleton_lock:
      if not klass in klass._singleton_inst:
        klass._singleton_inst[klass] = super().__call__(*args, **kwargs)
      return klass._singleton_inst[klass]



class ThreadLocal(type):
  ''' Metaclass to make any other class into a one-per-thread singleton. '''
  _singleton_lock   = threading.Lock()
  _singleton_inst   = {}

  def __call__(klass, *args, **kwargs):
    itemname        = base.utils.ObjectName(klass) + '/' + base.utils.ThreadName()
    with klass._singleton_lock:
      if not itemname in klass._singleton_inst:
        klass._singleton_inst[itemname] = super().__call__(*args, **kwargs)
      return klass._singleton_inst[itemname]


class ThreadLocalDict(dict, metaclass=ThreadLocal):
  ''' A Dictionary that exists per thread. '''
