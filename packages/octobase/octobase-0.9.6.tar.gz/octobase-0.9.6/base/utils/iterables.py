#!/opt/local/bin/python
''' Functions for iterable data types. '''

import base
import json
import inspect


def Flatten(*lst):
  ''' Flattens lists of lists of lists as you would expect. '''
  # A naive implementation might be something like:
  #     return sum( ([x] if not hasattr(x, '__iter__') else Flatten(x) for x in lst), [] )
  # But we have this annoying thing called FileType that is iterable, includes itself in
  # its own iteration, and fits really well inside lists of things people want to Flatten().
  seen              = []
  results           = []

  def IsIterable(x):
    return hasattr(x, '__iter__') and not isinstance(x, str)

  def Accumulate(x):
    if isinstance(x, tuple) or isinstance(x, list):
      for y in x:
        Accumulate(y)
    elif isinstance(x, str) or not hasattr(x, '__iter__'):
      results.append(x)
    else:
      # An iterable that is not a tuple or list, be careful, may become recursive
      if not x in seen:
        seen.append(x)
        for y in x:
          if y == x:
            results.append(x)
          else:
            Accumulate(y)

  for item in lst:
    Accumulate(item)

  return results


def CountUnique(l):
  ''' Given an iterable we return a dict of each unique item mapped to a count of its occurrences. '''
  r             = {}
  for k in l:
    r[k]        = r.get(k, 0) + 1
  return r


def ReverseDict(d):
  ''' Given { key: value } we return { value: [key] } '''
  r             = {}
  for k in d:
    r.setdefault(d[k], []).append(k)
  return r


def CountValues(d):
  ''' given a dictionary { a: [x, y, z, ...] } returns a dictionary { a: len([x, y, z, ...]) } '''
  return {x: len(y) for x,y in d.items()}


def DictToJson(d):
  ''' pretty-prints a dictionary to a string '''
  return json.dumps(d, sort_keys=True, indent=2)


def PrintDict(d):
  ''' pretty-prints a dictionary to console '''
  print(DictToJson(d))


def GetAttrs(thing, capitals=True, lowers=True, hidden=False):
  ''' Returns a dictionary of every attribute we can read off the thing. '''
  members           = {x:y for x,y in inspect.getmembers(thing)}
  if not hidden:
    members         = {x:y for x,y in members.items() if x[0] != '_'}
  if not capitals:
    members         = {x:y for x,y in members.items() if not x[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
  if not lowers:
    members         = {x:y for x,y in members.items() if not x[0] in 'abcdefghijklmnopqrstuvwxyz'}
  return members


def SetAttrs(thing, **kwargs):
  ''' calls setattr() on thing for each keyword argument; will raise if an attribute is not present '''
  if not kwargs and isinstance(thing, dict):
    raise base.errors.SetAttrsSus
  for key, value in kwargs.items():
    if hasattr(thing, key):
      setattr(thing, key, value)
    else:
      raise base.errors.SetAttrsNotSilent('.'.join((base.utils.ObjectName(thing), key)))



def SetAttrsSilently(thing, **kwargs):
  ''' calls setattr() on thing for each keyword argument; will set attrs even if not present '''
  for key, value in kwargs.items():
    setattr(thing, key, value)



class Counter:
  ''' good for counting iterations '''

  def __init__(self, start=0):
    self.count      = start

  def __call__(self):
    ''' returns the next integer every time we're called '''
    ret             = self.count
    self.count      += 1
    return ret

