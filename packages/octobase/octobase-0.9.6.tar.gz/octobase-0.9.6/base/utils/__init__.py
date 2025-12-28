import importlib

from .            import environment
from .decorators  import optional_arg_decorator, classproperty, anyproperty, anymethod, cached_property, cached_method

for modname in (
    'decorators',
    'django',
    'environment',
    'fuzzy',
    'interactive',
    'iterables',
    'logging',
    'metaclasses',
    'misc',
    'strings',
    'threadstacks',
    'time',
):
  environment.ImportCapitalizedNamesFrom(importlib.import_module('base.utils.' + modname))


def ImportTests():
  from . import tests
