"""
Convenience functions and descriptors for HEA object attributes.
"""
from collections.abc import Iterable, Iterator, MutableSequence
from yarl import URL
from typing import Any, cast, Generic, TypeVar, overload, Union, Callable
from abc import ABC, abstractmethod
from .util import raise_if_empty_string
from .decorators import AttributeMetadata, set_attribute_metadata
from enum import Enum
from copy import copy, deepcopy

class CopyBehavior(Enum):
    """
    Enum for copy behavior of attributes.
    """
    NO_COPY = 10
    SHALLOW_COPY = 20
    DEEP_COPY = 30


def sequence_of_non_empty_str_setter(self, attr_name: str, strings: str | Iterable[str] | None):
    """
    Sets a sequence of non-empty strings to an attribute. If the strings argument is None, the attribute is set to an
    empty list. If the strings argument is not an iterable, a TypeError is raised. If the strings argument contains
    empty strings, a ValueError is raised.

    :param attr_name: the name of the sequence-of-string attribute.
    :param strings: the iterable of non-empty strings to set.
    :raises TypeError: if the strings argument is not an iterable nor a string.
    :raises ValueError: if the strings argument contains empty strings.
    :raises AttributeError: if the attribute is not a mutable sequence.
    """
    sequence_of_str_setter(self, attr_name, strings, disallow_empty_strings=True)


def sequence_of_non_empty_str_adder(self, attr_name: str, string: str):
    """
    Adds a string to a sequence, disallowing the empty string. If the string argument is not a string, it is converted
    to a string.

    :param attr_name: the name of the sequence-of-string attribute.
    :param string: the non-empty string to add.
    """
    string_ = str(string)
    raise_if_empty_string(string_)
    if not hasattr(self, attr_name):
        setattr(self, attr_name, [string_])
    else:
        cast(MutableSequence[str], getattr(self, attr_name)).append(string_)


def sequence_of_non_empty_str_remover(self, attr_name: str, string: str):
    """
    Removes a string from a sequence. If it is not present, this operation does nothing.

    :param attr_name: the name of the sequence-of-string attribute.
    :param string: the string to remove.
    """
    try:
        attr = cast(MutableSequence[str], getattr(self, attr_name))
        if attr:
            attr.remove(string)
    except (AttributeError, ValueError) as e:
        pass


def set_of_non_empty_str_adder(self, attr_name: str, string: str):
    """
    Adds a non-empty string to a set, disallowing the empty string. If the string argument is not a string, it is
    converted to a string.

    :param attr_name: the name of the set-of-string attribute.
    :param string: the non-empty string to add.
    """
    string_ = str(string)
    raise_if_empty_string(string_)
    if not hasattr(self, attr_name):
        setattr(self, attr_name, {string_})
    else:
        cast(set, getattr(self, attr_name)).add(string_)


def set_of_non_empty_str_remover(self, attr_name: str, string: str):
    """
    Removes a string from a set. If it is not present, this operation does nothing.

    :param attr_name: the name of the set-of-string attribute.
    :param string: the string to remove.
    """
    try:
        attr = cast(set, getattr(self, attr_name))
        if attr:
            attr.remove(string)
    except (AttributeError, KeyError) as e:
        pass


def sequence_of_str_setter(self, attr_name: str, strings: str | Iterable[str] | None, disallow_empty_strings: bool = False):
    """
    Sets a sequence of non-empty strings to an attribute. If the strings argument is None, the attribute is set to an
    empty list. If the strings argument is not an iterable, a TypeError is raised. If the strings argument contains
    empty strings, a ValueError is raised.

    :param attr_name: the name of the sequence-of-string attribute.
    :param strings: the iterable of non-empty strings to set.
    :raises TypeError: if the strings argument is not an iterable nor a string.
    :raises ValueError: if the strings argument contains empty strings and disallow_empty_strings is True.
    :raises AttributeError: if the attribute is not a mutable sequence.
    """
    if isinstance(strings, str):
        strings = [strings]
    elif not isinstance(strings, Iterable):
        raise TypeError('Expected an iterable or a str')

    if (attr := cast(MutableSequence[str] | None, getattr(self, attr_name, None))) is None:
        setattr(self, attr_name, [])
        attr = getattr(self, attr_name)
    else:
        attr.clear()
    for s in strings:
        string_ = str(s)
        if disallow_empty_strings:
            raise_if_empty_string(string_)
        attr.append(string_)


def sequence_of_id_adder(self, attr_name: str, id_: str):
    """
    Adds a desktop object id string to a sequence. If the id_ argument is not a string, it is converted to a string.

    :param attr_name: the name of the sequence-of-string attribute.
    :param id_: the id to add.
    """
    sequence_of_non_empty_str_adder(self, attr_name, id_)


def sequence_of_id_remover(self, attr_name: str, id_: str):
    """
    Removes a desktop object id from a sequence. If it is not present, this operation does nothing.

    :param attr_name: the name of the sequence-of-string attribute.
    :param id_: the id to remove.
    """
    sequence_of_non_empty_str_remover(self, attr_name, id_)


def set_of_str_adder(self, attr_name: str, string: str):
    """
    Adds a string to a set. If the string argument is not a string, it is converted to a string.

    :param attr_name: the name of the set-of-string attribute.
    :param id_: the id to add.
    """
    string_ = str(string)
    if not hasattr(self, attr_name):
        setattr(self, attr_name, {string_})
    else:
        cast(set, getattr(self, attr_name)).add(string_)


def set_adder(self, attr_name: str, value: Any, type_: type | None = None):
    """
    Adds an object to a set. If the value argument is not of the expected type, a TypeError is raised.

    :param attr_name: the name of the set attribute.
    :param value: the object to add.
    :param type_: the type of the value argument. If not None, type checking is performed.
    :raises TypeError: if the value argument is not of the expected type.
    """
    if type_ is not None and not isinstance(value, type_):
        raise TypeError(f'Expected {type_}, got {type(value)}')
    if not hasattr(self, attr_name):
        setattr(self, attr_name, {value})
    else:
        cast(set, getattr(self, attr_name)).add(value)

def set_of_str_remover(self: Any, attr_name: str, string: str):
    """
    Removes a string from a set. If it is not present, this operation does nothing.

    :param attr_name: the name of the set-of-string attribute.
    :param string: the string to remove.
    """
    set_remover(self, attr_name, str(string))


def set_remover(self: Any, attr_name: str, value: Any):
    """
    Removes an object from a set. If it is not present, this operation does nothing.

    :param attr_name: the name of the set attribute.
    :param value: the object to remove.
    """
    try:
        attr = cast(set, getattr(self, attr_name))
        if attr:
            attr.remove(value)
    except AttributeError as e:
        pass


def sequence_of_str_adder(self: Any, attr_name: str, string: str):
    """
    Adds a string to a sequence. If the string argument is not a string, it is converted to a string.

    :param attr_name: the name of the sequence attribute.
    :param string: the string to add.
    """
    sequence_adder(self, attr_name, str(string))


def sequence_adder(self: Any, attr_name: str, value: Any, type_: type | None = None):
    """
    Adds an object to a sequence. If the value argument is not of the expected type, a TypeError is raised.

    :param attr_name: the name of the sequence attribute.
    :param value: the value to add.
    :param type_: the type of the value to be added. If not None, type checking is performed.
    :raises TypeError: if the value argument is not of the expected type.
    """
    if type_ is not None and not isinstance(value, type_):
        raise TypeError(f'Expected {type_}, got {type(value)}')
    if not hasattr(self, attr_name):
        setattr(self, attr_name, [value])
    else:
        cast(MutableSequence[Any], getattr(self, attr_name)).append(value)


def sequence_contains(self: Any, attr_name: str, value: Any) -> bool:
    """
    Checks if a value is in a sequence.

    :param attr_name: the name of the sequence attribute.
    :param value: the value to check for.
    :return: True if the value is in the sequence, False otherwise.
    """
    try:
        attr = cast(MutableSequence[Any], getattr(self, attr_name))
        return value in attr
    except AttributeError:
        return False

def sequence_of_str_remover(self: Any, attr_name: str, string: str):
    """
    Removes a string from a sequence. If it is not present, this operation does nothing.

    :param attr_name: the name of the sequence attribute.
    :param string: the string to remove.
    """
    sequence_remover(self, attr_name, str(string))


def sequence_remover(self: Any, attr_name: str, value: Any):
    """
    Removes an object from a sequence. If it is not present, this operation does nothing.

    :param attr_name: the name of the sequence attribute.
    :param value: the object to remove.
    """
    try:
        attr = cast(MutableSequence[Any], getattr(self, attr_name))
        if attr:
            attr.remove(value)
    except (AttributeError, ValueError) as e:
        pass


T = TypeVar('T')


def do_copy(obj: T, copy_behavior: CopyBehavior) -> T:
    """
    Copies the attribute value if needed based on the copy behavior.

    :param obj: the object to get the attribute from.
    :return: the copied attribute value, or None if the attribute is not set.
    """
    match(copy_behavior):
        case CopyBehavior.NO_COPY:
            return obj
        case CopyBehavior.SHALLOW_COPY:
            return copy(obj)
        case CopyBehavior.DEEP_COPY:
            return deepcopy(obj)
        case _:
            raise ValueError(f'Unexpected copy behavior {copy_behavior}')


VPARAMS = TypeVar('VPARAMS')
VSELF = TypeVar('VSELF', bound='HEAAttribute')

class HEAAttribute(Generic[T], ABC):
    """
    Base class for descriptors for HEA object attributes. It provides a way to define custom behavior for getting and
    setting attribute values, as well as a defining default values and type conversion between the attribute's type and
    an internal representation. It takes a type parameter T, which represents the type of the attribute value. To use
    this class, subclass it and implement the __get__ and __set__ methods to define the custom behavior for getting and
    setting the attribute value.
    """

    def __init__(self, doc: str | None = None, copy_behavior = CopyBehavior.NO_COPY,
                 attribute_metadata: AttributeMetadata | None = None,
                 pre_hook: Callable[[VSELF, VPARAMS], VPARAMS] | None = None,
                 post_hook: Callable[[VSELF, VPARAMS], None] | None = None):
        """
        Constructor for HEAAttribute.

        :param doc: the attribute's docstring.
        :param copy_behavior: the defensive copying behavior to use for getting and setting the attribute.
        :param attribute_metadata: metadata about the attribute.
        :param pre_hook: a function to call before setting the attribute. It takes the object and the value to be set,
        and returns a value to be set that may be different from the value passed in.
        :param post_hook: a function to call after setting the attribute. It takes the object and the value that was
        set.
        """
        self.__doc__ = doc
        self.__attribute_metadata = attribute_metadata
        self.__copy_behavior = copy_behavior if copy_behavior else CopyBehavior.NO_COPY
        self.__pre_hook = pre_hook
        self.__post_hook = post_hook

    def __set_name__(self, owner: type, name: str):
        """
        Called automatically when the descriptor is assigned to a class.

        :param owner: the class that owns the descriptor.
        :param name: the name of the descriptor.
        """
        self._private_name = f'_{owner.__name__}__{name}'
        self._public_name = name
        self._owner = owner
        if self.__attribute_metadata is not None:
            set_attribute_metadata(self, self.__attribute_metadata)

    @property
    def copy_behavior(self):
        """
        Gets the copy behavior for the attribute.
        """
        return self.__copy_behavior

    @copy_behavior.setter
    def copy_behavior(self, value: CopyBehavior):
        """
        Sets the copy behavior for the attribute.
        """
        self.__copy_behavior = value if value else CopyBehavior.NO_COPY

    @property
    def pre_hook(self) -> Callable[[Any, Any], Any] | None:
        """
        Gets the pre-hook for the attribute.
        """
        return self.__pre_hook

    @property
    def post_hook(self) -> Callable[[Any, Any], None] | None:
        """
        Gets the post-hook for the attribute.
        """
        return self.__post_hook

    @overload
    def _default_getter(self, obj: None, default_value: T) -> 'HEAAttribute': ...

    @overload
    def _default_getter(self, obj: object, default_value: T) -> T: ...

    def _default_getter(self, obj: object | None, default_value: T) -> 'HEAAttribute' | T:
        """
        A default implementation for returning the value of the attribute. If you want to use this method, implement
        __get__ to call this method.

        :param obj: the object to get the attribute from.
        :param default_value: the value to return if the attribute is not set.
        :return: the value to return, or the default value if the attribute is not set.
        """
        if obj is None:
            return self
        try:
            return do_copy(getattr(obj, self._private_name), self.copy_behavior)
        except AttributeError:
            return default_value

    @abstractmethod
    def __get__(self, obj: object | None, objtype: type | None = None) -> T | 'HEAAttribute':
        """
        Gets the value of the attribute.

        :param obj: the object to get the attribute from.
        :param objtype: the type of the object.
        :return: the value of the attribute.
        """
        pass

    @abstractmethod
    def __set__(self, obj: object, value: T):
        """
        Sets the value of the attribute.

        :param obj: the object to set the attribute on.
        :param value: the value to set.
        """
        pass


class SimpleAttribute(Generic[T], HEAAttribute[T]):
    """
    A simple descriptor for attributes that can be set and get directly. Attempting to set this attribute to None will
    set it to the default value. The default value is also used when the attribute is not set.
    """

    def __init__(self, type_: type[T], default_value: T, doc: str | None = None,
                 attribute_metadata: AttributeMetadata | None = None,
                 pre_hook: Callable[['SimpleAttribute', T], T] | None = None,
                 post_hook: Callable[['SimpleAttribute', T], None] | None = None):
        """
        Constructor for SimpleAttribute.

        :param type_: the type of the attribute.
        :param default_value: a default value for the attribute.
        :param doc: the attribute's docstring.
        :param attribute_metadata: metadata for the attribute.
        :param pre_hook: a function to call before setting the attribute. It takes the object and the value to be set,
        and returns a value to be set that may be different from the value passed in.
        :param post_hook: a function to call after setting the attribute. It takes the object and the value that was
        set.
        """
        super().__init__(doc=doc, attribute_metadata=attribute_metadata,
                         pre_hook=pre_hook, post_hook=post_hook)
        self.__type = type_
        self.__default_value = default_value

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> 'SimpleAttribute': ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> T: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Union[T, 'SimpleAttribute']:
        return self._default_getter(obj, default_value=self.__default_value)

    def __set__(self, obj: object, value: T):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        if value is None:
            value = self.__default_value
        if not isinstance(value, self.__type):
            raise TypeError(f'Expected {self.__type}, got {type(value)}')
        setattr(obj, self._private_name, value)
        if self.post_hook:
            self.post_hook(obj, value)



class URLAttribute(HEAAttribute[str | None]):
    """
    A URL descriptor.
    """

    def __init__(self, absolute = False, doc: str | None = None, attribute_metadata: AttributeMetadata | None = None,
                 pre_hook: Callable[[Any, str | None], str | None] | None = None,
                 post_hook: Callable[[Any, str | None], None] | None = None):
        """
        Constructor for URLAttribute.

        :param absolute: if True, only absolute URLs are allowed.
        :param doc: the attribute's docstring.
        :param attribute_metadata: metadata for the attribute.
        :param pre_hook: a function to call before setting the attribute. It takes the object and the value to be set,
        and returns a value to be set that may be different from the value passed in.
        :param post_hook: a function to call after setting the attribute. It takes the object and the value that was
        set.
        """
        super().__init__(doc=doc, attribute_metadata=attribute_metadata,
                         pre_hook=pre_hook, post_hook=post_hook)
        self.__absolute = absolute

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> 'URLAttribute': ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> str | None: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Union[str, None, 'URLAttribute']:
        return self._default_getter(obj, default_value=None)

    def __set__(self, obj, value: str | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        if value is not None:
            u = URL(value)
            if self.__absolute and not u.is_absolute():
                raise ValueError(f'relative url {value} not allowed')
            setattr(obj, self._private_name, str(value))
        else:
            setattr(obj, self._private_name, None)
        if self.post_hook:
            self.post_hook(obj, value)


class StrOrNoneAttribute(HEAAttribute[str | None]):
    """
    A descriptor for attributes that can be either a str or None
    """

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> 'StrOrNoneAttribute': ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> str | None: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Union[str, None, 'StrOrNoneAttribute']:
        return self._default_getter(obj, default_value=None)

    def __set__(self, obj, value: str | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        setattr(obj, self._private_name, str(value) if value is not None else None)
        if self.post_hook:
            self.post_hook(obj, value)


class NonEmptyStrOrNoneAttribute(HEAAttribute[str | None]):
    """
    A descriptor for attributes that can be either a non-empty str or None. The empty string is converted to None prior
    to assignment.
    """

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> 'NonEmptyStrOrNoneAttribute': ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> str | None: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Union[str, None, 'NonEmptyStrOrNoneAttribute']:
        return self._default_getter(obj, default_value=None)

    def __set__(self, obj, value: str | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        raise_if_empty_string(value)
        setattr(obj, self._private_name, str(value) if value else None)
        if self.post_hook:
            self.post_hook(obj, value)


class IdAttribute(HEAAttribute[str | None]):
    """
    A descriptor for desktop object id attributes, which can be either a non-empty str or None.
    """

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> 'IdAttribute': ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> str | None: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Union[str, None, 'IdAttribute']:
        return self._default_getter(obj, default_value=None)

    def __set__(self, obj, value: str | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        value_ = str(value) if value is not None else None
        raise_if_empty_string(value_)
        setattr(obj, self._private_name, value_ if value_ else None)
        if self.post_hook:
            self.post_hook(obj, value_)


class NameAttribute(HEAAttribute[str | None]):
    """
    A descriptor for desktop object name attributes, which can be either a non-empty str or None.
    """

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> 'NameAttribute': ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> str | None: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Union[str, None, 'NameAttribute']:
        return self._default_getter(obj, default_value=None)

    def __set__(self, obj, value: str | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        value_ = str(value)
        raise_if_empty_string(value_)
        setattr(obj, self._private_name, value_ if value_ else None)
        if self.post_hook:
            self.post_hook(obj, value_)


U = TypeVar('U')


class ListAttribute(Generic[U], HEAAttribute[list[U]]):
    """
    A descriptor for lists.
    """

    def __init__(self, doc: str | None = None, copy_behavior = CopyBehavior.NO_COPY,
                 attribute_metadata: AttributeMetadata | None = None,
                 objtype: type | None = None,
                 pre_hook: Callable[[Any, U | Iterable[U] | None], U | Iterable[U] | None] | None = None,
                 post_hook: Callable[[Any, U | Iterable[U] | None], None] | None = None,
                 **kwargs):
        """
        Constructor for ListAttribdute.

        :param doc: the attribute's docstring.
        :param copy_behavior: the defensive copying behavior to use for getting and setting the attribute.
        :param attribute_metadata: metadata about the attribute.
        :param objtype: the type of the value to be added. If not None, type checking is performed on added values.
        :param pre_hook: a function to call before setting the attribute. It takes the object and the value to be set,
        and returns a value to be set that may be different from the value passed in.
        :param post_hook: a function to call after setting the attribute. It takes the object and the value that was
        set.
        """
        super().__init__(doc=doc, copy_behavior=copy_behavior, attribute_metadata=attribute_metadata,
                         pre_hook=pre_hook, post_hook=post_hook, **kwargs)
        self.__objtype = objtype

    @property
    def objtype(self) -> type | None:
        """
        Gets the type of objects in the list, or None if any type is allowed.
        """
        return self.__objtype

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> 'ListAttribute': ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> list[U]: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Union[list[U], 'ListAttribute']:
        return self._default_getter(obj, default_value=[])

    def __set__(self, obj: object, value: U | Iterable[U] | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        if not isinstance(value, Iterable) and value is not None:
            if self.objtype and not isinstance(value, self.objtype):
                raise TypeError(f'Expected {self.objtype}, got {type(value)}')
            value = [value]
            setattr(obj, self._private_name, do_copy(value, self.copy_behavior))
        elif value is not None:
            if not isinstance(value, Iterable):
                raise TypeError('Expected an iterable')
            value = list(value)
            if self.objtype and any(not isinstance(o, self.objtype) for o in value):
                raise TypeError(f'Expected iterable of {self.objtype}')
            if self.copy_behavior is CopyBehavior.DEEP_COPY:
                setattr(obj, self._private_name, deepcopy(value))
            else:
                setattr(obj, self._private_name, value)
        else:
            setattr(obj, self._private_name, [])
        if self.post_hook:
            self.post_hook(obj, value)

    def add(self, obj, value: U):
        """
        Adds an object to the list. If the value argument is not of the expected type, a TypeError is raised.

        :param obj: the object to add the value to.
        :param value: the value to add.
        """
        sequence_adder(obj, self._private_name, do_copy(value, self.copy_behavior), type_=self.objtype)

    def remove(self, obj, value: U):
        """
        Removes an object from the list. If it is not present, this operation does nothing.

        :param obj: the object to remove the value from.
        :param value: the value to remove.
        """
        sequence_remover(obj, self._private_name, value)

    def replace(self, obj, old_value: U, new_value: U):
        """
        Replaces the first occurrence of old_value in the list with new_value. If old_value is not found, this operation
        does nothing.

        :param obj: the object to replace the value in.
        :param old_value: the value to replace.
        :param new_value: the value to replace with.
        """
        try:
            lst = cast(MutableSequence[U], getattr(obj, self._private_name))
            index = lst.index(old_value)
            lst[index] = new_value
        except (AttributeError, ValueError):
            pass

    def len(self, obj) -> int:
        """
        Gets the number of ids in the list.

        :param obj: the object to get the number of ids from.
        :return: the number of ids in the list.
        """
        try:
            attr = getattr(obj, self._private_name)
            return len(attr) if attr else 0
        except AttributeError:
            return 0


class StrListAttribute(ListAttribute[str]):
    """
    A descriptor for lists of str. Passing a str into this attribute will set the attribute to a singleton list with that
    string. For other iterables, contained objects that are not strings are converted to strings prior to being added.
    """

    def __init__(self, disallow_empty_strings=False, doc: str | None = None,
                 attribute_metadata: AttributeMetadata | None = None,
                 pre_hook: Callable[[Any, str | Iterable[str] | None], str | Iterable[str] | None] | None = None,
                 post_hook: Callable[[Any, str | Iterable[str] | None], None] | None = None,
                 **kwargs):
        """
        Constructor for StrListAttribute.

        :param disallow_empty_strings: if True, empty strings are not allowed in the list.
        :param doc: the attribute's docstring.
        :param attribute_metadata: metadata for the attribute.
        :param pre_hook: a function to call before setting the attribute. It takes the object and the value to be set,
        and returns a value to be set that may be different from the value passed in.
        :param post_hook: a function to call after setting the attribute. It takes the object and the value that was
        set.
        """
        super().__init__(doc=doc, attribute_metadata=attribute_metadata, objtype=str,
                         pre_hook=pre_hook, post_hook=post_hook, **kwargs)
        self.__disallow_empty_strings = bool(disallow_empty_strings)

    def __set__(self, obj, value: str | Iterable[str] | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        sequence_of_non_empty_str_setter(obj, self._private_name, value)
        if self.post_hook:
            self.post_hook(obj, value)

    def add(self, obj, value: str):
        """
        Adds a string to the list. If the value is not a string, it is converted to one.

        :param obj: the object to add the value to.
        :param value: the string to add.
        :param type_: the type of the value to be added. If not None, type checking is performed.
        """
        if self.__disallow_empty_strings:
            raise_if_empty_string(value)
        sequence_of_str_adder(obj, self._private_name, value)

    def remove(self, obj, value: str):
        """
        Removes a string from the list. If the value is not a string, it is converted to one prior to the lookup. If it
        is not present, this operation does nothing.

        :param obj: the object to remove the value from.
        :param value: the string to remove.
        """
        sequence_of_str_remover(obj, self._private_name, value)


class ListWithBackingSetAttribute(Generic[U], ListAttribute[U]):
    """
    A descriptor for lists that are stored as a backing set. This attribute type is not suitable for storing HEAObjects
    because they are typically not hashable. Passing a str into this attribute will set the attribute to a singleton
    list with that string. For other iterables, contained objects that are not strings are converted to strings prior
    to being added. For unique lists of HEAObjects, use UniqueListAttribute instead.
    """

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> 'ListWithBackingSetAttribute': ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> list[U]: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> Union[list[U], 'ListWithBackingSetAttribute']:
        if obj is None:
            return self
        try:
            if self.copy_behavior in (CopyBehavior.SHALLOW_COPY, CopyBehavior.NO_COPY):
                return sorted(getattr(obj, self._private_name))
            return sorted(deepcopy(item) for item in getattr(obj, self._private_name))
        except AttributeError:
            return []

    def __set__(self, obj, value: U | Iterable[U] | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        if not isinstance(value, Iterable) and value is not None:
            setattr(obj, self._private_name, {do_copy(value, self.copy_behavior)})
        elif value is not None:
            if not isinstance(value, Iterable):
                raise TypeError('Expected an iterable')
            setattr(obj, self._private_name, do_copy(set(value), self.copy_behavior))
        else:
            setattr(obj, self._private_name, set())
        if self.post_hook:
            self.post_hook(obj, value)

    def add(self, obj, value: U):
        """
        Adds an object to the list. If the value argument is not of the expected type, a TypeError is raised.

        :param obj: the object to add the value to.
        :param value: the value to add.
        :param type_: the type of the value to be added. If not None, type checking is performed.
        """
        set_adder(obj, self._private_name, do_copy(value, self.copy_behavior), type_=self.objtype)

    def remove(self, obj, value: U):
        """
        Removes an object from the list. If it is not present, this operation does nothing.

        :param obj: the object to remove the value from.
        :param value: the value to remove.
        """
        set_remover(obj, self._private_name, value)

    def replace(self, obj, old_value: U, new_value: U):
        """
        Replaces the first occurrence of old_value in the list with new_value. If old_value is not found, this operation
        does nothing.

        :param obj: the object to replace the value in.
        :param old_value: the value to replace.
        :param new_value: the value to replace with.
        """
        try:
            s = cast(set, getattr(obj, self._private_name))
            if old_value in s:
                s.remove(old_value)
                s.add(new_value)
        except AttributeError:
            pass


class StrListWithBackingSetAttribute(ListWithBackingSetAttribute[str], StrListAttribute):
    """
    A descriptor for lists of strings with a backing set. Passing a str into this attribute will set the attribute to a
    singleton set with that string. For other iterables, contained objects that are not strings are converted to
    strings prior to being added.
    """

    def __init__(self, disallow_empty_strings=False, doc: str | None = None,
                 attribute_metadata: AttributeMetadata | None = None,
                 pre_hook: Callable[[Any, str | Iterable[str] | None], str | Iterable[str] | None] | None = None,
                 post_hook: Callable[[Any, str | Iterable[str] | None], None] | None = None,
                 **kwargs):
        """
        Constructor for StrListWithBackingSetAttribute.

        :param disallow_empty_strings: if True, empty strings are not allowed in the list.
        :param doc: the attribute's docstring.
        :param attribute_metadata: metadata for the attribute.
        :param pre_hook: a function to call before setting the attribute. It takes the object and the value to be set,
        and returns a value to be set that may be different from the value passed in.
        :param post_hook: a function to call after setting the attribute. It takes the object and the value that was
        set.
        """
        super().__init__(doc=doc, attribute_metadata=attribute_metadata,
                         pre_hook=pre_hook, post_hook=post_hook, **kwargs)
        self.__disallow_empty_strings = bool(disallow_empty_strings)

    @property
    def disallow_empty_strings(self) -> bool:
        """Whether or not this attribute disallows empty strings."""
        return self.__disallow_empty_strings

    def __set__(self, obj, value: str | Iterable[str] | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        if isinstance(value, str):
            setattr(obj, self._private_name, {value})
        elif value is not None:
            if not isinstance(value, Iterable):
                raise TypeError('Expected an iterable or a str')
            set_ = set()
            for val in value:
                val_ = str(val)
                if self.__disallow_empty_strings:
                    raise_if_empty_string(val_)
                set_.add(val_)
            setattr(obj, self._private_name, set_)
        else:
            setattr(obj, self._private_name, set())
        if self.post_hook:
            self.post_hook(obj, value)

    def add(self, obj, value: str):
        """
        Adds an object to the list. If the value argument is not of the expected type, a TypeError is raised.

        :param obj: the object to add the value to.
        :param value: the value to add.
        """
        if self.__disallow_empty_strings:
            raise_if_empty_string(value)
        set_of_str_adder(obj, self._private_name, value)

    def remove(self, obj, value: str):
        """
        Removes an object from the list. If it is not present, this operation does nothing.

        :param obj: the object to remove the value from.
        :param value: the value to remove.
        """
        set_of_str_remover(obj, self._private_name, value)


class UniqueListAttribute(Generic[U], ListAttribute[U]):
    """
    A descriptor for lists when the list's items must remain unique, defined as !=, but the items cannot be in a set.
    Attempts to add duplicates to the list are ignored. The implementation sorts the elements of the list to detect
    duplicates, resulting in O(n*log(n)) time complexity for additions and sets.
    """

    def __init__(self, doc: str | None = None, copy_behavior = CopyBehavior.NO_COPY,
                 attribute_metadata: AttributeMetadata | None = None, key_fn: Callable[[U], Any] | None = None,
                 pre_hook: Callable[[Any, U | Iterable[U] | None], U | Iterable[U] | None] | None = None,
                 post_hook: Callable[[Any, U | Iterable[U] | None], None] | None = None,
                 **kwargs):
        """
        Constructor for list attributes when you want to enforce uniqueness.

        :param doc: the attribute's docstring.
        :param copy_behavior: the defensive copying behavior to use for getting and setting the attribute.
        :param attribute_metadata: metadata about the attribute.
        :param key_fn: a function that takes an item and returns an object used for sorting the elements of the list.
        If None, default sorting behavior is applied.
        :param pre_hook: a function to call before setting the attribute. It takes the object and the value to be set,
        and returns a value to be set that may be different from the value passed in.
        :param post_hook: a function to call after setting the attribute. It takes the object and the value that was
        set.
        """
        super().__init__(doc=doc, copy_behavior=copy_behavior, attribute_metadata=attribute_metadata,
                         pre_hook=pre_hook, post_hook=post_hook, **kwargs)
        self.__key_fn = key_fn

    def __set__(self, obj: object, value: U | Iterable[U] | None):
        if self.pre_hook:
            value = self.pre_hook(obj, value)
        if not isinstance(value, Iterable) and value is not None:
            setattr(obj, self._private_name, do_copy([value], self.copy_behavior))
        elif value is not None:
            if not isinstance(value, Iterable):
                raise TypeError('Expected an iterable')
            result = self.__remove_duplicates(sorted(value, key=self.__key_fn) if self.__key_fn else sorted(value))
            setattr(obj, self._private_name, do_copy(result, self.copy_behavior))
        else:
            setattr(obj, self._private_name, [])
        if self.post_hook:
            self.post_hook(obj, value)

    @property
    def key_fn(self) -> Callable[[U], Any] | None:
        return self.__key_fn

    def add(self, obj, value: U, type_: type[U] | None = None):
        """
        Adds an object to the list. If the value argument is not of the expected type, a TypeError is raised.

        :param obj: the object to add the value to. If the value is already in the list, it is ignored.
        :param value: the value to add.
        :param type_: the type of the value to be added. If not None, type checking is performed.
        """
        objs = cast(list[U], getattr(obj, self._private_name, []))
        def itr() -> Iterator[U]:
            yield value
            for obj in objs: yield obj
        objs_sorted = sorted(itr(), key=self.__key_fn) if self.__key_fn else sorted(itr())  #type:ignore[type-var]
        result = self.__remove_duplicates(objs_sorted)
        setattr(obj, self._private_name, result)

    def remove(self, obj, value: U):
        """
        Removes an object from the list. If it is not present, this operation does nothing.

        :param obj: the object to remove the value from.
        :param value: the value to remove.
        """
        sequence_remover(obj, self._private_name, value)

    def __remove_duplicates(self, objs: list[U]) -> list[U]:
        last = objs[0] if objs else None
        result = [last] if last else []
        for current in objs[1:]:
            if current != last:
                result.append(current)
            last = current
        return result


class IdListWithBackingSetAttribute(StrListWithBackingSetAttribute):
    """
    A descriptor for lists of desktop object ids with a backing set. Passing an id into this attribute will set the
    attribute to a singleton set with that id. For other iterables, contained objects that are not strings are
    converted to strings prior to being added.
    """

    def __init__(self, doc: str | None = None, attribute_metadata: AttributeMetadata | None = None,
                 pre_hook: Callable[[Any, str | Iterable[str] | None], str | Iterable[str] | None] | None = None,
                 post_hook: Callable[[Any, str | Iterable[str] | None], None] | None = None,
                 **kwargs):
        """
        Constructor for an id list attribute where each id must be unique.

        :param doc: the attribute's docstring.
        :param copy_behavior: the defensive copying behavior to use for getting and setting the attribute.
        :param attribute_metadata: metadata about the attribute.
        :param pre_hook: a function to call before setting the attribute. It takes the object and the value to be set,
        and returns a value to be set that may be different from the value passed in.
        :param post_hook: a function to call after setting the attribute. It takes the object and the value that was
        set.
        """
        super().__init__(doc=doc, attribute_metadata=attribute_metadata, disallow_empty_strings=True,
                         pre_hook=pre_hook, post_hook=post_hook, **kwargs)
