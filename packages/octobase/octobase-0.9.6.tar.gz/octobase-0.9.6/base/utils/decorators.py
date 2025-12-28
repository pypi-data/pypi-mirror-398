#!/opt/local/bin/python
''' Fancy ways of calling class methods. '''

import functools


def optional_arg_decorator(fn):
  ''' Wraps another decorator and allows use of optional decorator arguments.
      https://stackoverflow.com/questions/3888158/making-decorators-with-optional-arguments#comment65959042_24617244
  '''
  def wrapped_decorator(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
      return fn(args[0])
    else:
      def real_decorator(decoratee):
        return fn(decoratee, *args, **kwargs)
      return real_decorator
  return wrapped_decorator



def classproperty(fxn):
  ''' The obvious @classproperty decorator that Python lacks.
      See stack-overflow for advice if we need to make this read-write for any reason:
          http://stackoverflow.com/questions/5189699/how-can-i-make-a-class-property-in-python
  '''
  if not isinstance(fxn, (classmethod, staticmethod)):
    fxn            = classmethod(fxn)
  return ClassPropertyDescriptor(fxn)

class ClassPropertyDescriptor(object):
  def __init__(self, fxn):
    self.fxn        = fxn

  def __get__(self, obj, klass):
    klass           = klass or type(obj)
    return self.fxn.__get__(obj, klass)()



class AnyPropertyDescriptor(object):
  def __init__(self, fxn):
    self.fxn        = fxn
    self.classfxn   = isinstance(fxn, (classmethod, staticmethod)) and fxn or classmethod(fxn)

  def __get__(self, obj, klass):
    klass           = klass or type(obj)
    fxn             = obj is None and self.classfxn or self.fxn
    return fxn.__get__(obj, klass)()

class AnyMethodDescriptor(object):
  def __init__(self, fxn):
    self.fxn        = fxn
    self.classfxn   = isinstance(fxn, (classmethod, staticmethod)) and fxn or classmethod(fxn)

  def __get__(self, obj, klass):
    klass           = klass or type(obj)
    fxn             = obj is None and self.classfxn or self.fxn
    return fxn.__get__(obj, klass)

def anyproperty(fxn):
  ''' @anyproperty decorator for properties that operate at class or instance level '''
  return AnyPropertyDescriptor(fxn)

def anymethod(fxn):
  ''' @anymethod decorator for methods that operate at class or instance level '''
  return AnyMethodDescriptor(fxn)



class cached_property:
  ''' Inspired by Django, put here so this module can run without Django. '''
  # ...then rebuilt because i like my version better.
  def __init__(self, fxn):
    self.fxn        = fxn
    self.__name__   = fxn.__name__

  def __get__(self, obj, klass):
    if obj is None:
      return self.fxn
    cachename       = self.__name__ + '__cache'
    try:
      return getattr(obj, cachename)
    except AttributeError:
      setattr(obj, cachename, self.fxn(obj))
    return getattr(obj, cachename)


class cached_method(object):
  ''' http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/ '''
  def __init__(self, fxn):
    self.fxn = fxn

  def __get__(self, obj, objtype=None):
    if obj is None:
      return self.fxn
    return functools.partial(self, obj)

  def __call__(self, *args, **kwargs):
    obj = args[0]
    try:
      cache         = obj.__cache
    except AttributeError:
      cache         = obj.__cache = {}
    key             = (self.fxn, args[1:], frozenset(kwargs.items()))
    try:
      return cache[key]
    except KeyError:
      cache[key]    = self.fxn(*args, **kwargs)
    return cache[key]
