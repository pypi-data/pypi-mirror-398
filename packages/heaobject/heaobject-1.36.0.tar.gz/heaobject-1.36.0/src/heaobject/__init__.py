"""
The HEAObject project implements classes representing all the data managed by HEA microservices. It also provides base
classes for creating additional microservices.

Generally speaking, there is a one-to-one correspondence between module and microservice. Each module's docstring, and
the docstrings for the classes contained within, describe any special requirements for microservices that use those
classes. For HEA microservice authors, it is important to understand those requirements so that your microservices
function properly. For example, the heaobject.folder module describes requirements for microservices that implement
management of folders.

Classes in this package have the following conventions for object attributes:
* Private attributes' names are prefixed with a double underscore.
* Protected attributes' names are prefixed with a single underscore. "Protected" is defined as accessible only to
the class in which it's defined and subclasses. Python does not enforce protected access, but uses of protected
attributes outside of subclasses may break even in patch releases.
* Invalid input is indicated by raising an exception. Unless otherwise indicated, the exception will be a ValueError or
TypeError. Attributes that raise AttributeError are skipped by the heaobject.root.HEAObject.from_dict() and from_json()
methods. This is done to allow for skipping read-only methods. Some attributes may raise additional exceptions as
described in their docstrings.

HEAObjects may be converted to a dictionary or JSON string using the to_dict() and to_json() methods, respectively. The
from_dict() and from_json() class methods may be used to create HEAObjects from a dictionary or JSON string. Keys in
the dictionaries are always strings with only allowed characters for Python variable names and additionally cannot
contain dots. Similarly, do not create attributes with a dot in the name.

Class, instance, and static methods are also expected to raise ValueError or TypeError for invalid input unless
otherwise indicated. Some methods may raise additional exceptions as described in their docstrings.
"""
import importlib
import logging
import pkgutil
logging.getLogger(__name__).addHandler(logging.NullHandler())


def import_all_submodules() -> None:
    """
    Import all submodules of heaobject to ensure that all classes are registered.

    :return: An iterator over the imported module specs.
    """
    for module in pkgutil.iter_modules(__path__, prefix='heaobject.'):
        importlib.import_module(module.name)
