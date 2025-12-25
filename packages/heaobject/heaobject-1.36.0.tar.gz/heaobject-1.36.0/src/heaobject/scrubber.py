from collections.abc import Callable
from enum import Enum
from heaobject.root import HEAObject, HEAObjectDict, HEAObjectTypeVar, json_dumps
from wrapt import ObjectProxy

class _Scrubber(ObjectProxy):
    """
    Lightweight class that wraps an HEAObject and censors sensitive attributes in its string representations.
    This object proxies read-write attribute access to the underlying HEAObject, except that when a sensitive attribute
    is accessed, it returns a scrubbed string such as '******' instead of the actual value. Similarly, it proxies
    all HEAObject methods.
    """

    def __init__(self, obj: HEAObjectTypeVar) -> None:
        """
        Initialize the Scrubber with an HEAObject. For performance reasons, it does not copy the object, so setting
        the object's attributes affects the Scrubber's output.

        :param obj: The HEAObject to be scrubbed.
        """
        super().__init__(obj)

    def __getattr__(self, name: str):
        """
        Proxy attribute access to the underlying HEAObject, censoring sensitive attributes.

        :param name: The attribute name.
        :return: The attribute value, or '******' if the attribute is sensitive.
        """
        obj = self.__wrapped__
        if obj.has_attribute(name) and obj.get_attribute_metadata(name).sensitive:
            return '******'
        else:
            res = getattr(obj, name)
            if isinstance(res, HEAObject):
                return _Scrubber(res)
            else:
                return res

    def __repr__(self) -> str:
        """
        Return a string representation of the underlying HEAObject, with sensitive attributes scrubbed. It acts the
        same as heaobject.root.AbstractHEAObject's __repr__ method. Override this method if you want a different
        representation.
        """
        return f'heaobject.root.from_dict({self.to_dict()!r})'

    def to_dict(self) -> HEAObjectDict:
        """
        Return a dictionary representation of the underlying HEAObject, with sensitive attributes scrubbed. It acts
        the same as heaobject.root.AbstractHEAObject's to_dict method. Override this method if you want a different
        representation.
        """
        def nested(obj):
            match obj:
                case HEAObject():
                    return _Scrubber(obj).to_dict()
                case list():
                    return [nested(o) for o in obj]
                case Enum():
                    return obj.name
                case _:
                    return obj

        return {a: nested(getattr(self, a)) for a in getattr(self, 'get_attributes')()}

    def to_json(self, dumps: Callable[[HEAObjectDict], str] = json_dumps) -> str:
        """
        Returns a JSON-formatted string containing this object's data attributes as defined by the get_attributes()
        method. Passes the json_encode function as the default parameter.

        :param dumps: any callable that accepts a HEAObject and returns a string.
        :return: a string.
        """
        return dumps(self.to_dict())

    def __str__(self) -> str:
        """
        Return a string representation of the underlying HEAObject. It acts the same as HEAObject's __str__ method.
        Override this method if you want a different representation.
        """
        return getattr(self, 'display_name')


def scrubbed(obj: HEAObjectTypeVar) -> HEAObjectTypeVar:
    """
    Function that takes an HEAObject and returns a proxy that censors its sensitive attributes when reading from the
    attributes. Setting attributes and calling mutator methods affect the underlying HEAObject as normal. The proxy
    otherwise behaves like the underlying HEAObject, except issubclass checks comparing the proxy's type to HEAObject
    and its subclasses will return False.

    :param obj: The HEAObject to be scrubbed.
    :return: A scrubbed version of the HEAObject.
    """
    return _Scrubber(obj)
