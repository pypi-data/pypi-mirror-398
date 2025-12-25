from .util import type_name_to_type, type_to_type_name
from dataclasses import dataclass, field
from typing import Callable, TypeVar, ParamSpec

@dataclass(frozen=True)
class AttributeMetadata:
    """
    Class to hold metadata for attributes, such as read-only status.
    """
    read_only: bool = field(default=False, metadata={'description': 'If True, the attribute is read-only.'})
    requires_sharer: bool = field(default=False, metadata={'description': 'If True, the attribute requires SHARER '
                                                           'permissions to edit.'})
    sensitive: bool = field(default=False, metadata={'description': 'If True, the attribute is considered sensitive '
                                                     'data.'})
    needs_encryption: bool = field(default=False, metadata={'description': 'If True, the attribute might need '
                                                            'encryption in transit and/or at rest. Only applies to str'
                                                            'objects.'})


DEFAULT_ATTRIBUTE_METADATA = AttributeMetadata()

_attr_metadata: dict[object, AttributeMetadata] = {}

P = ParamSpec('P')
RT = TypeVar('RT')

def attribute_metadata(read_only = False, requires_sharer = False, sensitive = False,
                       needs_encryption = False) -> Callable[[Callable[P, RT]], Callable[P, RT]]:
    """
    Decorator to mark an HEAObject attribute with metadata. It supports properties, and it also supports
    descriptors that subclass heaobject.attribute.HEAAttribute. It is unnecessary to use this decorator to mark an
    attribute as read-only if the attribute is already defined as read-only (property with a None fset or HEAAttribute
    with no __set__ method). However, decorating such an attribute with read_only set to False will raise an error.

    :param read_only: If True, the attribute is read-only. Defaults to False.
    :param requires_sharer: If True, the attribute requires SHARER permissions to edit. Defaults to False.
    :param sensitive: If True, the attribute is considered sensitive data. Defaults to False.
    :param needs_encryption: If True, the attribute might need encryption in transit and/or at rest. Only applies to
    strings. Defaults to False.
    :return: The decorated function.
    """
    def decorator(func: Callable[P, RT]) -> Callable[P, RT]:
        if hasattr(func, 'fget'):
            _set_property_metadata(func, AttributeMetadata(read_only=read_only, requires_sharer=requires_sharer,
                                                           sensitive=sensitive, needs_encryption=needs_encryption))
        else:
            raise ValueError("Decorator can only be applied to properties.")
        return func
    return decorator


def set_attribute_metadata(attr, attribute_metadata: AttributeMetadata) -> None:
    """
    Set metadata for a given attribute. The attribute must either be a property or have a _owner attribute that is a
    class. HEAAttribute objects have an _owner attribute. If the attribute is a property, the metadata is set on the
    getter function. If the attribute has a _owner, the metadata is set on the owner class.

    :param attr: The attribute.
    :param read_only: If True, the attribute is read-only.
    :param requires_sharer: If True, the attribute requires SHARER permissions to edit.
    """
    if hasattr(attr, 'fget'):
        _set_property_metadata(attr, attribute_metadata)
    elif owner := getattr(attr, '_owner', None):
        # If the function is an HEAAttribute, we set the metadata on the attribute
        if attribute_metadata.read_only and _is_attribute_readonly(attr):
            raise ValueError(f"Cannot set read_only=True on a read-only HEAAttribute: {attr._public_name}")
        _attr_metadata[(type_to_type_name(owner), f'{owner.__qualname__}.{attr._public_name}')] = attribute_metadata


def get_attribute_metadata(attr) -> AttributeMetadata | None:
    """
    Retrieve metadata for a given attribute. The attribute must either be a property or have a _owner attribute that
    is a class. HEAAttribute objects have an _owner attribute. If the attribute is a property, the metadata is
    retrieved from the getter function. If the attribute has a _owner, the metadata is retrieved from the owner class.

    :param attr: The attribute, or None if the attribute has no metadata.

    :return : Metadata object.
    """
    if fget := getattr(attr, 'fget', None):
        # If the function is a property getter, we set the metadata on the getter
        type_ = type_name_to_type(f'{fget.__module__}.{fget.__qualname__}'.rsplit('.', 1)[0])
        for cls in type_.__mro__:
            if result := _attr_metadata.get((type_to_type_name(cls), f'{cls.__qualname__}.{fget.__name__}'), None):
                return result
        else:
            return _new_attribute_metadata(type_, fget.__name__, attr.fset is None)
    elif owner := getattr(attr, '_owner', None):
        for cls in owner.__mro__:
            if result := _attr_metadata.get((type_to_type_name(cls), f'{cls.__qualname__}.{attr._public_name}'), None):
                return result
        else:
            return _new_attribute_metadata(owner, attr._public_name, not hasattr(attr, '__set__'))
    return None


def _new_attribute_metadata(cls: type, attr: str, read_only: bool) -> AttributeMetadata:
    """
    Create a new AttributeMetadata instance for the given class.

    :param cls: The class for which to create metadata.
    :param read_only: If True, the attribute is read-only.
    :return: A new AttributeMetadata instance.
    """
    result = AttributeMetadata(read_only=read_only)
    _attr_metadata[(type_to_type_name(cls), f'{cls.__qualname__}.{attr}')] = result
    return result


def _set_property_metadata(func: Callable[P, RT], attribute_metadata: AttributeMetadata) -> None:
    """
    Set metadata for a property. If the property has a getter, the metadata is set on the getter function.
    If the property has an owner, the metadata is set on the owner class.
    :param prop: The property.
    :param read_only: If True, the property is read-only.
    :param requires_sharer: If True, the property requires SHARER permissions to edit.
    """
    if (fget := getattr(func, 'fget', None)) is None:
        raise ValueError("Cannot set metadata on a property without a getter.")
    if attribute_metadata.read_only and not _is_property_readonly(func):
        raise ValueError(f"Cannot set read_only=True on a property with a setter: {fget.__name__}")
    # If the function is a property getter, we set the metadata on the getter
    type_name = type_to_type_name(fget).rsplit('.', 1)[0]
    _attr_metadata[(type_name, fget.__qualname__)] = attribute_metadata


def _is_property_readonly(prop: Callable[P, RT]) -> bool:
    """
    Return whether a property is read-only.

    :param prop: The property to check.

    :return: True if the property is read-only, False otherwise.
    """
    return getattr(prop, 'fset', None) is None

def _is_attribute_readonly(attr) -> bool:
    """
    Return whether an attribute is read-only.

    :param attr: The attribute to check.

    :return: True if the attribute is read-only, False otherwise.
    """
    return not hasattr(attr, '__set__')
