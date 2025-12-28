#!/opt/local/bin/python

import base
import logging
import weakref


class Controller(metaclass=base.registry.AutoRegister, skip=1):
  ''' Controllers ride along with Models to extend their functionality.

      When a model inherits from ControllerMixin it gains a property
      named "controller".  This property returns an instance of this class
      or a child class of this class, always.

      Controller subclasses register for a namespace and a name within that
      namespace.  When a subclass exists that matches the namespace and name
      provided through the ControllerMixin interface, that subclass is
      chosen.

      This allows for dynamic controllers based on, say, an Enum field present
      on your model.  The Enum class definition is the namespace and each model
      has a value in that enum field, which becomes the name.  So different
      model instances get different controllers based on the value of their enum
      field.
'''

  CONTROLLER_NAMESPACE  = None  # An item that implements "in" testing, or a ControllerNamespace
  CONTROLLER_NAME       = None  # Some name "in" the namespace
  CONTROLLER_ITEM_NAME  = None  # Name of a property to set as a contextual sugar

  CONTROLLERS           = None  # Internal cache for performance reasons

  @staticmethod
  def DowncastFor(item, name_override=None, **kwargs):
    # No item, trivial result
    if not item:
      return Controller()

    # The item must be something that we know how to talk about
    if not isinstance(item, ControllerMixin):
      if isinstance(item, type) and not issubclass(item, ControllerMixin):
        raise base.errors.ControllerPropertyNotFound(item)

    # It must have a namespace
    if not item.CONTROLLER_NAMESPACE:
      raise base.errors.ControllerNamespaceEmpty(item)
    namespace       = item.CONTROLLER_NAMESPACE
    if isinstance(namespace, str):
      namespace     = base.utils.GetModelByName(namespace)
      if not namespace:
        raise base.errors.ControllerNamespaceEmpty(item, 'Could not find a model named: ' + item.CONTROLLER_NAMESPACE)

    # If we instantiate the item() we need to keep its lifespan around
    strongitem      = None

    # It may or may not have a name
    name            = None
    error           = False
    if name_override:
      name          = name_override
    elif item.CONTROLLER_NAME_PROPERTY:
      if not hasattr(item, item.CONTROLLER_NAME_PROPERTY):
        error       = base.errors.ControllerNameProperty(item, item.CONTROLLER_NAME_PROPERTY)
      else:
        # Instantiate an empty instance if we've been given a type
        if isinstance(item, type):
          item        = item()
          strongitem  = item
        name          = getattr(item, item.CONTROLLER_NAME_PROPERTY)
        if base.utils.IsA(name, namespace):
          name        = None
        try:
          error       = name and not(name in namespace)
        except:
          pass
    elif base.utils.IsA(namespace, ControllerNamespace):
      name          = isinstance(item, type) and item or type(item)
      error         = not base.utils.IsA(name, namespace)
    else:
      error         = True

    # Treat any errors gently
    if error:
      error         = error or base.errors.ControllerNameNotInNamespace(item, name, namespace)
      base.utils.Log('CONTROLLER', str(error), level=logging.WARNING)
      name          = None

    # Init our list of all controllers if it's not been done
    if Controller.CONTROLLERS is None:
      Controller.CONTROLLERS  = base.registry.GetAll(Controller)

    # Look for all registered Controllers that match our enum and value
    Accept          = lambda x: x.CONTROLLER_NAMESPACE == namespace and x.CONTROLLER_NAME == name
    candidates      = [x for x in Controller.CONTROLLERS if Accept(x)]
    if base.utils.IsA(name, ControllerNamespace):
      name          = base.utils.ObjectName(name)
      candidates.extend([x for x in Controller.CONTROLLERS if Accept(x)])

    # If we found nothing, try emptying the name
    if not candidates and name is not None:
      name          = None
      candidates    = [x for x in Controller.CONTROLLERS if Accept(x)]

    # If we didn't do it above, turn types into new instances
    if isinstance(item, type):
      item        = item()
      strongitem  = item

    # Return what we found
    if not candidates:
      raise base.errors.ControllerNotFound(item, namespace, name)
    if len(candidates) > 1:
      raise base.errors.ControllerNonUnity(item, candidates)
    return candidates[0](item=item, strongitem=strongitem, **kwargs)

  def __init__(self, item=None, strongitem=None):
    self.itemref    = item and weakref.ref(item) or None  # May be a ControllerMixin instance, subclass, or None
    self.strongitem = strongitem        # Keeps the weakref alive if our caller is the one that made it
    # Add a shortcut property to ourselves named whatever the class of item we have.
    # For example, if our item is an Asset, we add a property named "asset" to access the item.
    if item:
      classname     = self.CONTROLLER_ITEM_NAME or base.utils.ClassName(item).lower()
      if not hasattr(self, classname) and classname != 'item':
        setattr(self, classname, self.item)
    elif self.CONTROLLER_ITEM_NAME:
      setattr(self, self.CONTROLLER_ITEM_NAME, None)

  @property
  def item(self):
    return self.itemref and self.itemref() or None

  def ControlledClassName(self):
    ''' Convenience name that puts the controller name before the class name
        if it makes sense: "Document Asset" for instance.
    '''
    if self.item and self.item.CONTROLLER_NAME_PROPERTY:
      name          = getattr(self.item, self.item.CONTROLLER_NAME_PROPERTY)
    else:
      name          = self.CONTROLLER_NAME

    namespace       = self.CONTROLLER_NAMESPACE

    if isinstance(namespace, base.Enum):
      if name in namespace:
        return ' '.join((namespace.Name(name), base.utils.ClassName(self.item)))

    if base.utils.IsA(namespace, ControllerNamespace):
      return ' '.join((base.utils.ClassName(self.item), base.utils.ClassName(namespace)))

    return base.utils.ClassName(self.item)



class ControllerMixin:
  ''' A mixin that enables Controller interfaces for that model. '''

  CONTROLLER_NAMESPACE      = None          # An item that implements "in" testing
  CONTROLLER_NAME_PROPERTY  = None          # Name of a property on the model
  CONTROLLER_CACHE          = True          # should the controller instance be cached?

  @base.utils.anyproperty
  def controller(self):
    if isinstance(self, type):
      return Controller.DowncastFor(self)
    if self.CONTROLLER_CACHE:
      if not self._controller:
        self._controller      = Controller.DowncastFor(self)
      return self._controller
    return Controller.DowncastFor(self)
  _controller               = None

  @classmethod
  def Controller(klass, name=None):
    return Controller.DowncastFor(klass, name_override=name)



class ControllerNamespace:
  ''' A parent class you can derive a model from if you want us to do subclass testing
      for your controller namespace.
  '''



class SlugMetaNamespace(type):
  ''' metaclass for SlugControllerNamespace '''
  def __contains__(klass, x):
    try:
      return bool(x and isinstance(x, str) and base.utils.Slugify(x) == x)
    except:
      return False

class SlugControllerNamespace(metaclass=SlugMetaNamespace):
  ''' controller namespace class that accepts any valid slug '''

