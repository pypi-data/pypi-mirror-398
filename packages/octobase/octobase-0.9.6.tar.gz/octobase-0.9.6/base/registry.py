#!/opt/local/bin/python
''' The Registry allows simple name-based retrieval of Python objects. '''

import base
import logging
import threading


IGNORED             = None


class Registry(metaclass=base.utils.Singleton):

  ###
  ## AutoRegister MetaClass
  #

  class AutoRegister(type):
    ''' A metaclass that automatically registers classes that are built from it.

        This metaclass takes three optional arguments:

            skip        -- how many levels of subclass to skip registering, default = 0
            instances   -- register class instances instead of class types, default = False
            regname     -- optional name of a property on your subclass that provides the name
                           of the object to use in the registry, default = the class's ObjectName

        For example, this will auto-register sub-classes derived from MyBaseClass while not
        registering MyBaseClass itself:

            class MyBaseClass(metaclass=base.registry.AutoRegister, skip=1):
              pass
    '''

    @classmethod
    def __prepare__(klass, name, bases, skip=0, instances=False, regname=None, **kwargs):
      result        = super().__prepare__(name, bases, **kwargs)
      result['_autoregister_skip']          = skip
      result['_autoregister_instances']     = instances
      result['_autoregister_regname']       = regname
      for base in bases:
        if hasattr(base, '_autoregister_skip'):
          result['_autoregister_skip']      = skip or max(0, base._autoregister_skip - 1)
          result['_autoregister_instances'] = base._autoregister_instances
          result['_autoregister_regname']   = regname or base._autoregister_regname
          break
      return result

    @classmethod
    def __new__(klass, *args, skip=IGNORED, instances=IGNORED, regname=IGNORED, **kwargs):
      return super().__new__(*args, **kwargs)

    def __init__(klass, name, bases, namespace, skip=IGNORED, instances=IGNORED, regname=IGNORED):
      super().__init__(name, bases, namespace)
      if not klass._autoregister_skip:
        obj         = klass._autoregister_instances and klass() or klass
        name        = klass._autoregister_regname and getattr(obj, klass._autoregister_regname) or base.utils.ObjectName(obj)
        Registry().Register(obj, name)

  ###
  ## API
  #

  def Get(self, name, of_type=None):
    ''' Retrieve an object by name or return None. '''
    obj             = self.objects.get(name)
    if obj and of_type and not base.utils.IsA(obj, of_type):
      return None
    return obj

  def GetAll(self, of_type=None):
    ''' Retrieve all the objects we know of, or optionally only objects that descend from a certain type. '''
    if not of_type:
      return list(self.objects.values())
    if of_type in self.cache:
      return self.cache[of_type]
    results         = [o for o in self.objects.values()
        if o and isinstance(o, of_type)
        or (isinstance(o, type) and issubclass(o, of_type))]
    self.cache[of_type] = results
    return results

  def GetAllWithNames(self, of_type):
    ''' Retrieve (name, thing) for all the objects we know that descend from a certain type. '''
    results         = [(name, thing) for (name, thing) in self.objects.items()
        if thing and base.utils.IsA(thing, of_type)]
    return results

  def Register(self, obj, name=None):
    ''' An object would like to be part of the registry, please. '''
    if obj is None:
      raise base.errors.RegisteredObjectNotAllowedType()
    if not name:
      name          = base.utils.ObjectName(obj)
    if name in self.objects:
      raise base.errors.RegisteredObjectNameDuplication(name)
    self.objects[name]  = obj
    self.cache      = {}

  def Replace(self, name, obj):
    ''' Please update the registration of this name to a new object '''
    if obj is None:
      raise base.errors.RegisteredObjectNotAllowedType()
    if not name in self.objects:
      raise base.errors.RegisteredObjectNotPresent(name)
    self.objects[name]  = obj
    self.cache      = {}

  def UnRegister(self, name):
    ''' An object should be removed from the registry, please. '''
    if not isinstance(name, str):
      name          = base.utils.ObjectName(name)
    if not name in self.objects:
      raise base.errors.RegisteredObjectNotPresent(name)
    self.objects.pop(name)
    self.cache      = {}

  def UnRegisterByPrefix(self, prefix):
    ''' Remove all objects matching a name prefix, please. '''
    removes         = set()
    for name in self.objects:
      if name.startswith(prefix):
        removes.add(name)
    for name in removes:
      del self.objects[name]
    self.cache      = {}

  ###
  ## Internals
  #

  def __init__(self):
    self.objects    = {}    # { name: item }
    self.cache      = {}    # { type: registered items of that type }

  def __len__(self):
    return len(self.objects)

  def __bool__(self):
    return bool(self.objects)

  def __contains__(self, name):
    return name in self.objects
