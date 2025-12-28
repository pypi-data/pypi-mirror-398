#!/opt/local/bin/python
''' Functions for modules, callstacks, thread names, etc. '''

import base
import importlib
import inspect
import os
import socket
import subprocess
import threading


def ImportCapitalizedNamesFrom(*modulelist):
  ''' Like doing `from module import *` but pulls in only names that start with capitals. '''
  globs             = GetGlobalsOfCaller()
  for module in modulelist:
    for key in module.__dir__():
      if key[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' and not key in globs:
        globs[key]  = getattr(module, key)


class DeferredImport:
  ''' Returned by DeferImport() as a temporary placeholder. '''

  def __init__(self, globs, path, name):
    self.__sekret_stash = (globs, path, name)

  def __bool__(self):
    globs, path, name = self.__sekret_stash
    try:
      module        = importlib.import_module(path)
    except ModuleNotFoundError:
      return False
    globs[name]     = module
    return True

  def __getattr__(self, slug):
    if slug == '__sekret_stash':
      return super().__getattr__(slug)
    globs, path, name = self.__sekret_stash
    module          = importlib.import_module(path)
    globs[name]     = module
    return getattr(module, slug)


def DeferImport(path, name=None):
  ''' A way to put imports at the top of your file yet defer them until the first actual use. '''
  globs           = GetGlobalsOfCaller()
  name            = name or path
  name            = name.strip('.')
  if '.' in name:
    name          = name.rsplit('.', 1)[1]
  globs[name]     = DeferredImport(globs, path, name)


def GetGlobalsOfCaller():
  ''' Retrieves the globals() of the module that called the code that called this function. '''
  try:
    frame         = None
    stack         = inspect.stack()
    if len(stack) >= 3:
      frame       = stack[2][0]
    elif len(stack) == 2:
      frame       = stack[1][0]
    return frame and frame.f_globals
  finally:
    del frame


def GetLocalsOfCaller():
  ''' Retrieves the locals() of the function that called the code that called this function. '''
  try:
    frame         = None
    stack         = inspect.stack()
    if len(stack) >= 3:
      frame       = stack[2][0]
    elif len(stack) == 2:
      frame       = stack[1][0]
    return frame and frame.f_locals
  finally:
    del frame


def IsA(item, parent):
  ''' Returns True if item is an instance or subclass of parent. '''
  if item is parent:
    return True
  if not isinstance(parent, type):
    parent      = type(parent)
  if isinstance(item, parent):
    return True
  if isinstance(item, type):
    return issubclass(item, parent)


def ParentTypes(thing):
  ''' Returns a list of the types that a thing derives from. '''
  if not isinstance(thing, type):
    thing         = type(thing)
  supermros       = set()
  for parent in thing.__mro__[1:]:
    for notours in parent.__mro__[1:]:
      supermros.add(notours)
  return [x for x in thing.__mro__[1:] if x != object and x not in supermros]


def ClassName(o):
  ''' Returns a string for the python class name of object o. '''
  # If the object came from a query with deferred fields, we need the parent model, not the proxy
  # with a name like 'File_Deferred_bytes_extension_hash_parent_hash_s07da85ef0c792d44433336a3d733f56c'
  if hasattr(o, '_meta') and hasattr(o._meta, 'proxy_for_model') and o._meta.proxy_for_model:
    o             = o._meta.proxy_for_model

  # The rest is simple
  try:
    return o.__name__.rsplit('.', 1)[-1]
  except AttributeError:
    return type(o).__name__.rsplit('.', 1)[-1]



__APPNAMES_BY_PREFIX    = {}
def RegisterAppNamePrefix(prefix, appname):
  ''' causes us to return a preferred appname for classes defined inside a specific module prefix '''
  global __APPNAMES_BY_PREFIX
  __APPNAMES_BY_PREFIX[prefix]  = appname


def AppName(thing):
  ''' Returns a string for the app a class is defined in. '''
  modname         = None
  if hasattr(thing, '__file__'):
    # thing is a module
    modname       = thing.__name__
  elif hasattr(thing, '__module__'):
    # thing is a class
    modname       = thing.__module__
  elif hasattr(thing, '__class__'):
    # thing is an instance
    modname       = thing.__class__.__module__
  if modname:
    global __APPNAMES_BY_PREFIX
    for prefix, appname in __APPNAMES_BY_PREFIX.items():
      if prefix and modname.startswith(prefix):
        return appname
    splits        = modname.split('.')
    if len(splits) > 1 and splits[0] != 'builtins':
      return splits[0]


def ObjectName(o):
  ''' Convenience wrapper for the two above functions. '''
  return '.'.join(x for x in (AppName(o), ClassName(o)) if x)


def ThreadName():
  ''' Returns the name of our current thread. '''
  return threading.current_thread().name


def HostName():
  ''' Returns the normalized hostname for the machine we're running on.
      UNLESS: we can detect we're on OS X, at which point we return the computer name
      that's been set in sharing system settings, regardless of whether DHCP has
      given our machine a new hostname or not.
  '''
  global _hostname_cache
  if not _hostname_cache:
    try:
      name        = subprocess.check_output(['scutil', '--get', 'ComputerName'], universal_newlines=True)
      name        = name and name.strip() or None
    except Exception:
      name        = None
    if not name:
      name        = socket.gethostname()
    name          = name and '.' in name and name.split('.', 1)[0] or name
    name          = name and name.lower() or None
    _hostname_cache = name
  return _hostname_cache
_hostname_cache   = None


def IsContained():
  ''' True if this process is running inside a Docker container. '''
  # borrowed from:  https://stackoverflow.com/questions/43878953/
  global _iscontained_cache
  if _iscontained_cache is None:
    path            = '/proc/self/cgroup'
    _iscontained_cache  = bool(os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path)))
  return _iscontained_cache
_iscontained_cache  = None


def SystemMemoryBytes():
  ''' returns a count of all the memory our process group (i.e.: container) is using; returns None on MacOS '''
  try:
    with open('/sys/fs/cgroup/memory.current', 'rt') as file:
      return int(file.read().strip())
  except Exception as err:
    pass

def SystemCpuSeconds():
  ''' returns a count of all the CPU seconds our process group (i.e.: container) has used; returns None on MacOS '''
  try:
    with open('/sys/fs/cgroup/cpu.stat', 'rt') as file:
      for line in file.readlines():
        if line.startswith('usage_usec '):
          _, val  = line.split(' ')
          return int(val) / 1000000
  except Exception as err:
    pass
