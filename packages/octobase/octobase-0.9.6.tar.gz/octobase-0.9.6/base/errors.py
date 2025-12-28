#!/opt/local/bin/python


class Error(Exception):
  ''' Useful base class to help explain an exception with its docstring. '''

  def __str__(self):
    prefix      = self.__doc__
    postfix     = super().__str__()
    if postfix:
      return prefix + '\n  ' + postfix
    return prefix



####
## Errors specific to "base"
#

class BaseError(Error):
  ''' Parent class for all exceptions specific to the "base" module. '''



class ControllerError(BaseError):
  ''' an error from the Controller part of base '''

class EnumError(BaseError):
  ''' an error from the Enum part of base '''

class RegistryError(BaseError):
  ''' an error from the Registry part of base '''

class ThingError(BaseError):
  ''' an error from the Thing part of base '''

class WhenError(BaseError):
  ''' an error from the When part of base '''

class UtilsError(BaseError):
  ''' an error from the utils part of base '''



class ControllerNameNotInNamespace(ControllerError):
  ''' An item identified with a name not in the Controller namespace. '''

class ControllerNameProperty(ControllerError):
  ''' An item's CONTROLLER_NAME_PROPERTY was not found on that item '''

class ControllerNamespaceEmpty(ControllerError):
  ''' An object needs to set CONTROLLER_NAMESPACE. '''

class ControllerNonUnity(ControllerError):
  ''' More than one Controller claims domain over the same item. '''

class ControllerNotFound(ControllerError):
  ''' No Controller wants to respond for the requested item. '''

class ControllerPropertyNotFound(ControllerError):
  ''' A Controller can only be instantiated from something that implements ControllerMixin. '''


class EnumDefinitionError(EnumError):
  ''' An Enum definition didn't make sense. '''

class EnumOptionNotFound(EnumError):
  ''' An option was not found in the enum. '''


class RegisteredObjectNameDuplication(RegistryError):
  ''' We can not register the same object more than once. '''

class RegisteredObjectNotAllowedType(RegistryError):
  ''' We can not register an object of the type given. '''

class RegisteredObjectNotPresent(RegistryError):
  ''' The expected object was not in the registry. '''


class NoAttributes(ThingError):
  ''' Thing.Copy() was called, but there were no ATTRIBUTES defined on neither source nor target '''


class BadWhen(WhenError):
  ''' When did not make sense '''

class IncompleteWhen(WhenError):
  ''' the When is missing some fields '''

class TzDataNotAvail(WhenError):
  ''' the `tzdata` package is not installed, nor are there any system zoneinfo files available '''

class EraMismatch(WhenError):
  ''' the whens are not in the same era '''

class AddingWhens(WhenError):
  ''' whens may be directly combined only if one has a date and one has a time '''

class TimeDeltaHasDate(WhenError):
  ''' timedeltas added to time-only whens may not span days '''

class TimeDeltaHasTime(WhenError):
  ''' timedeltas added to date-only whens may not include sub-day units '''



class SetAttrsSus(UtilsError):
  ''' the parameters passed to SetAttrs() look suspiciously wrong; are you truly setting nothing on a dict? '''


class SetAttrsNotSilent(UtilsError):
  ''' SetAttrs() may only be used with keywords that are already attributes on the target.
      (use SetAttrsSilently() if you need different behavior) '''
