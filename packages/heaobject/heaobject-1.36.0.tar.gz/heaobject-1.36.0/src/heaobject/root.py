"""
A collection of classes and interfaces supporting the construction of data transfer objects for moving data between
HEA microservices as well as between a HEA microservice and a web browser or other client. The HEAObject is the root
interface for these data transfer objects, and AbstractHEAObject provides a root abstract implementation for them.
See HEAObject's docstring for details.
"""

import orjson
from datetime import date, time

from humanize import naturalsize

from .encryption import Encryption
from .decorators import DEFAULT_ATTRIBUTE_METADATA, attribute_metadata
from .util import type_name_to_type, parse_bool, to_date_or_datetime, mangled  # Keep mangled for backwards compatibility
from .error import DeserializeException
from . import group as _group, user as _user, import_all_submodules
from .decorators import AttributeMetadata, get_attribute_metadata, attribute_metadata
from enum import auto, Enum
from typing import Optional, List, Union, Any, Callable, Dict, TypeVar, cast, Protocol, Optional, TYPE_CHECKING
from collections.abc import Iterable, Iterator, Mapping, Sequence, AsyncIterator
import copy
import inspect
import abc
import logging
import itertools
from copy import deepcopy
from dateutil import parser as dateparser
from typing import overload, final
from .user import ALL_USERS, is_system_user

# any subtype of these types are also valid (ex. datetime)
PRIMITIVE_ATTRIBUTE_TYPES = (int, float, str, bool, Enum, type(None), date, time)

NotNonePrimitive = Union[int, float, str, bool, Enum, date, time]
Primitive = Union[NotNonePrimitive, None]

MemberObjectDictValue = Union[Primitive, list[NotNonePrimitive]]
MemberObjectDict = dict[str, MemberObjectDictValue]
MemberObjectDictValueIncludesEncrypted = Union[Primitive, bytes, list[NotNonePrimitive | bytes]]
MemberObjectDictIncludesEncrypted = dict[str, MemberObjectDictValueIncludesEncrypted]

DesktopObjectDictValue = Union[Primitive, list[NotNonePrimitive | MemberObjectDict], MemberObjectDict]
DesktopObjectDict = dict[str, DesktopObjectDictValue]
DesktopObjectDictValueIncludesEncrypted = Union[Primitive, bytes,
                                                list[NotNonePrimitive | bytes | MemberObjectDictIncludesEncrypted],
                                                MemberObjectDictIncludesEncrypted]
DesktopObjectDictIncludesEncrypted = dict[str, DesktopObjectDictValueIncludesEncrypted]

HEAObjectDictValue = Union[DesktopObjectDictValue, MemberObjectDictValue]
HEAObjectDictValueIncludesEncrypted = Union[DesktopObjectDictValueIncludesEncrypted, MemberObjectDictValueIncludesEncrypted]
HEAObjectDict = Union[DesktopObjectDict, MemberObjectDict, dict[str, HEAObjectDictValue]]
HEAObjectDictIncludesEncrypted = Union[DesktopObjectDictIncludesEncrypted, MemberObjectDictIncludesEncrypted]

# Different logic for python 3.10 and earlier versions.

try:
    inspect.getmembers_static  # type:ignore[attr-defined]
    def _get_type_attributes(cls) -> set[str]:
        """
        Returns the class' attributes that do not begin with an underscore. This will include data descriptors and
        class variables but not simple member variables. We're interested in the class variables to filter them out of
        the HEAObject's attributes.

        :return: a set of attribute names.
        """
        return set(x for x in dir(cls) if not x.startswith('_'))
    def _get_attributes(self, type_attrs: set[str]) -> set[str]:
        """
        Returns an HEAObject's attributes that do not start with an underscore and are not class-level.

        :param type_attrs: a set of class-level attribute names. Those that are not data descriptors are filtered out.
        :return: a set of attribute names.
        """
        return set(m[0] for m in inspect.getmembers_static(self,  # type:ignore[attr-defined]
                                                           lambda x: not inspect.isroutine(x)) \
                     if not m[0].startswith('_') and (inspect.isdatadescriptor(m[1]) or m[0] not in type_attrs))
except AttributeError:
    def _get_type_attributes(cls) -> set[str]:
        """
        Returns class member names that should be filtered out of an HEAObject's get_attributes() method, namely
        class variables that do not begin with an underscore.

        :return: a set of public attribute names that are neither routines nor data descriptors.
        """
        return set(m[0] for m in inspect.getmembers(cls, lambda x: not inspect.isroutine(x) and not inspect.isdatadescriptor(x)) \
                   if not m[0].startswith('_'))
    def _get_attributes(self, type_attrs: set[str]) -> set[str]:
        """
        Returns an HEAObject's attributes that do not start with an underscore and are not class-level.

        :param type_attrs: a set of attribute names to filter out.
        :return: a set of attribute names.
        """
        return set(m[0] for m in inspect.getmembers(self, lambda x: not inspect.isroutine(x)) \
                     if not m[0].startswith('_') and m[0] not in type_attrs)


def json_encode(o: Any) -> Union[str, HEAObjectDict]:
    """
    Function to pass into the orjson.dumps default parameter that supports encoding HEAObjects. This function must be
    replaceable for testing purposes and everything should still work: this function must not be called while this
    module is loading.

    :param o: the object to encode.
    :return: the object after encoding.
    :raise TypeError: if the object is not a HEAObject.
    """
    match o:
        case HEAObject():
            return o.to_dict()
        case _:
            raise TypeError(f'values {o} must be HEAObject or a value type supported by orjson.dumps by default')


def json_dumps(o: Any) -> str:
    """
    Serialize any python object to a JSON document using orjson.dumps. Supports encoding HEAObjects using json_encode.

    :param o: the object to serialize.
    :return: a JSON document with UTF-8 encoding.
    """
    return orjson.dumps(o, default=json_encode).decode('utf-8')


def json_loads(o: str | bytes) -> Any:
    """
    Deserialize a HEAObject, a date, or a JSON-serializable object supported by default by orjson.dumps.

    :param o: the JSON string or bytes object.
    :return: a JSON document.
    """
    return orjson.loads(o)


class OrderedEnum(Enum):
    """An enum ordered by value."""

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class EnumAutoName(Enum):
    """
    Subclass of Enum in which auto() returns the name as a string. The values of the enum are the returned names
    instead of the usual numbers.
    """

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
        return name

    def __str__(self) -> str:
        return self.name


class EnumWithAttrs(Enum):
    """
    Enums that are specified with a non-integer value. A numerical value is auto-assigned. Enum values must be
    unordered.
    """

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


class EnumWithDisplayName(EnumWithAttrs):
    """
    Enums that are specified with a display name. A numerical value is auto-assigned. Enum values must be unordered.
    """

    def __init__(self, display_name: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__display_name = display_name

    @property
    def display_name(self) -> str:
        """The enum value's display name."""
        return self.__display_name

    def __str__(self) -> str:
        """Returns the enum value's display name."""
        return self.__display_name


class Permission(EnumAutoName):
    """
    The standard permissions that apply to all HEA desktop objects.
    """
    VIEWER = auto()  # Read-only access to the object and its content.
    EDITOR = auto()  # May update the object and its content.
    SHARER = auto()  # May share the object and its content.
    COOWNER = auto()  # May do anything with the object, like the owner of it.
    CREATOR = auto()  # May create an object; assigned to a container.
    DELETER = auto()  # May delete the object and its content.

    @classmethod
    def non_creator_permissions(cls) -> Iterator['Permission']:
        """
        Returns the permissions that are not CREATOR.

        :return: a list of Permission enum values.
        """
        return (p for p in cls if p is not cls.CREATOR)


class PermissionGroup(Protocol):
    """
    A duck typing protocol for permission groups, which are objects with a perms attribute that returns a tuple of
    Permission objects. Any object with such a perms attribute may be passed into DesktopObject.has_permissions().
    """
    @property
    def perms(self) -> list[Permission]:
        """The permissions in this group."""
        pass

    async def has_any(self, obj: 'DesktopObject', context: 'PermissionContext') -> bool:
        """
        Returns whether the object has any of the permissions in this group.

        :param: obj: a desktop object (required).
        :param: context: the permission context (required).
        :return: True or False.
        """
        pass

class DefaultPermissionGroup(EnumWithAttrs):
    """
    Enum that maps heaobject's root.Permission enum values to typical operations, suitable for passing into a
    DesktopObject's has_permissions() method.

    The Permission enum values composing each group can be queried by each PermissionGroup enum value's perms
    attribute.

    In order to access an object, the user must have at least one of the permissions in the
    ACCESSOR_PERMS permission group (VIEWER, COOWNER, EDITOR, SHARER) for the object.

    In order to create an object, the user must have at least one of the permissions in the
    CREATOR_PERMS permission group (CREATOR, COOWNER) for the container in which the object will be created.

    In order to update an object, the user must have at least one of the permissions in the
    UPDATER_PERMS permission group (EDITOR, COOWNER) for the object.

    In order to delete an object, the user must have at least one of the permissions in the
    DELETER_PERMS permission group (DELETER, COOWNER) for the object.
    """

    ACCESSOR_PERMS = [Permission.VIEWER, Permission.COOWNER, Permission.EDITOR, Permission.SHARER]
    UPDATER_PERMS = [Permission.EDITOR, Permission.COOWNER]
    SHARER_PERMS = [Permission.SHARER, Permission.COOWNER]
    CREATOR_PERMS = [Permission.CREATOR, Permission.COOWNER]
    DELETER_PERMS = [Permission.DELETER, Permission.COOWNER]

    def __init__(self, perms: Iterable[Permission]):
        self.__perms = list(perms)

    @property
    def perms(self) -> list[Permission]:
        """
        The permissions that are part of the group.
        """
        return self.__perms

    async def has_any(self, obj: 'DesktopObject', context: 'PermissionContext') -> bool:
        """
        Returns whether the object has any of the permissions in this group.

        :param: obj: a desktop object (required).
        :param: context: the permission context (required).
        :return: True or False.
        """
        return await obj.has_permissions(self.__perms, context)

    def __contains__(self, item: Permission) -> bool:
        """
        Returns whether the given permission is in the group.

        :param item: the permission to check.
        :return: True or False.
        """
        return item in self.__perms


class HEAObject(abc.ABC):
    """
    Interface for all HEA objects. HEA objects are data transfer objects for moving data between HEA microservices as
    well as between a HEA microservice and a web browser or other client. HEA objects have no behavior except support
    for storage, retrieval, serialization, and deserialization. The AbstractHEAObject class provides default
    implementations for setting and getting attributes, as well as default implementations of behaviors.

    Users of these classes should not assume that attributes are implemented as properties, even though most
    attributes are properties currently. We have begun converting attribute implementations to use the descriptor
    protocol, and that conversion will continue into the future.

    HEA objects have built-in facilities for extracting the object's data attributes into a dictionary or JSON string
    (the get_attributes(), to_dict() and to_json() methods). These methods are used by other parts of HEA to
    build REST API responses. These three methods support monkey-patched data attributes. However, from_dict() and
    from_json() will only set data attributes that already exist in the object.

    There are two sub-types of HEA objects: desktop objects (DesktopObject) and owned
    objects (MemberObject). The AbstractDesktopObject and AbstractMemberObject classes provide default implementations
    for setting and getting attributes, and default implementations of behaviors. There may be additional sub-types in
    the future.

    Desktop objects represent objects that appear on the HEA desktop. Desktop objects have permissions, timestamps for
    when the object was created and modified, versions, and more. One or more HEA microservices provide CRUD (create,
    read, update, and delete) operations on each desktop object type. Additional HEA microservices may implement actions
    that consume or produce specific desktop object types.

    Member objects cannot appear by themselves on the HEA desktop. Instead, they have a part-of relationship with a
    desktop object, and their lifecycle is managed by the desktop object. Example member objects represent permissions
    and data sharing. While owned objects provide for their own storage, retrieval, serialization, and deserialization,
    these behaviors are always invoked by the desktop object of which they are a part. HEA objects may contain only one
    level of nested members.

    HEA objects must conform to several conventions to ease their use and reuse across the HEA desktop.
    All subclasses of HEAObject must have a zero-argument constructor. Attribute values may be strings, numbers, booleans,
    enums, or a HEA object; or a list of strings, numbers, booleans, enums, or HEA objects. Attributes of type enum
    must be implemented as an attribute with a setter that accepts both strings and the enum values, and will convert
    the strings to enum values. An HEAObject's repr is expected to conform to `eval(repr(obj)) == obj`, and the repr is
    expected to stay the same so long as the state of the object does not change.

    In general, HEA objects implement composition relationships by making the container a desktop object and the "owned"
    object a member object. Other association relationships are implemented by storing the id of the associated object
    rather than nesting it. By convention, the id attributes are named hea_object_class_name_id, where
    hea_object_class_name is the name of the class converted from camel case to underscores.

    Copies and deep copies using the copy module will copy all non-callable instance members of any subclass of
    HEAObject. HEAObjects are also expected to implement the __eq__ method based on their attributes to ensure proper
    behavior in comparisons. The abstract base class, AbstractHEAObject, provides a default implementation that is
    suitable for most purposes.

    Attributes of an HEAObject must never raise an error because another attribute is unset.

    Objects are expected to perform defensive copying when setting and getting attributes so that altering an
    attribute's value from outside of the object cannot affect the object's internal state.

    Objects are expected to allow setting primitive type sequence attributes to a single object of the allowed type, in
    which case the attribute is stored as a singleton sequence containing that object. Unfortunately, there is no way
    to specify type hints for properties in which the getter type may be different from the setter type. The from_dict()
    method relies on this behavior.

    In addition, HEA objects should include type annotations throughout. Despite the type annotations, all setters
    should have comprehensive validation to ensure that the object is in a valid state after the setter is called. The
    setters may be called by the from_dict() method, which does not perform None nor type checks.

    It is imperative that users gain access to desktop objects by calling an appropriate HEA microservice as
    themselves, which will filter any nested member objects that are returned according to their permissions.

    HEA has an access control list-based permissions system that covers a wide range of use cases. Like with Unix-based
    systems, there are users (heaobject.person.Person) and groups (heaobject.person.Group), and they all may have one
    or more of the following permissions on a per-object level, which are defined in the heaobject.root.Permission
    enum:
    * VIEWER: Can access the object but not necessarily alter it.
    * EDITOR: Can update the object.
    * DELETER: Can delete the object.
    * SHARER: Can share the object with users and groups.
    * CREATOR: Used on containers to indicate the users who can create objects in that container.
    * COOWNER: All of the above.

    Users and groups are represented interchangeably by instances of the Person and Group classes or by unique strings.
    For users, the string is the Person's id attribute, and for groups, the string is the group's group attribute.

    There are multiple ways that permissions can be granted:
    1. **Owner**: The user who creates the object is the owner and has maximal permissions for the object and its
    attributes. Owners and super admins may reassign an object's ownership to another user, after which the new owner
    has all the same permissions on the object.
    2. **User Shares**: The owner can share the object with users, granting them specific permissions.
    3. **Group Shares**: The owner can share the object with groups, granting all members of the group specific
    permissions. Similarly, other users with SHARER permissions can grant additional permissions to groups. Dynamic
    permissions may also grant ability to share the object with groups.
    4. **Dynamic Permissions**: Some objects may have dynamic permissions that are determined by the object's
    attributes or other factors. For example, organizations have admin, manager, and member list attributes, which
    determine the permissions of users in those "roles."

    The user's effective object-level permissions are the union of all permissions granted to them through these
    methods. For convenience, the desktop object read-only shares attribute contains all user and group shares for an
    object.

    There are several system-defined users that make for more convenient permission management:
    * **system|none**: Requests to a HEA microservice must never be from this user. This is a convenience user for
        testing purposes, and in production it can be used as the owner user for objects that are globally read-only like
        registry component objects.
    * **system|all**: This user is used to grant permissions to all users. It is typically used in conjunction with
        system|none to create globally read-only objects. This is achieved by setting the owner to system|none and sharing
        the object with system|all with VIEWER permissions.

    Furthermore, an HEA object's class definition can define attribute-level permissions that restrict access beyond
    the user's effective object-level permissions. This allows for fine-grained control over who can access and modify
    specific attributes of an object. This may be done through the following mechanisms:
    * **heaobject.decorators.attribute_metadata**: This decorator can be used to mark attributes as globally read-only
        for all users, even for attributes that have a setter. This allows code to set values for those attributes but
        presents those attributes as read-only to users. Attributes with no setter are automatically presented as
        read-only through application programming interfaces for accessing attribute-level permissions.
    * **The DesktopObject dynamic_attribute_permission method**: this method is checked only when the user is not the
        object's owner and is not listed in a user or group share. By default, it returns VIEWER-only permissions for
        the owner, invites, user_shares, and group_shares attributes. It can be overridden in subclasses to provide
        custom permissions for users who have access solely through the dynamic permission method above.

    Attribute-level permissions are always a combination of VIEWER and EDITOR permissions. Also note that attribute-
    level permissions restrict access beyond the user's effective object-level permissions, meaning that if a user
    has VIEWER but not EDITOR permissions on an object, they will also have at most VIEWER permissions on all of that
    object's attributes.

    Finally, to support integration with data providers, groups can be mapped to a role that's known to a data
    provider, which allows for interfacing with providers that employ role-based access control, for example, Amazon
    Web Services.
    """

    @overload
    @abc.abstractmethod
    def to_dict(self) -> HEAObjectDict:
        """
        Returns a newly created dict containing this object's data attributes as defined by the get_attributes()
        method.

        :return: a dict of attribute names to attribute values.
        """
        pass

    @overload
    @abc.abstractmethod
    def to_dict(self, encryption: Encryption) -> HEAObjectDictIncludesEncrypted:
        """
        Returns a newly created dict containing this object's data attributes as defined by the get_attributes()
        method.

        :param encryption: an Encryption object to use for encrypting attribute values.
        :return: a dict of attribute names to attribute values.
        """
        pass

    @overload
    @abc.abstractmethod
    def to_dict(self, encryption: None) -> HEAObjectDict:
        ...

    @abc.abstractmethod
    def to_dict(self, encryption: Encryption | None = None) -> HEAObjectDict | HEAObjectDictIncludesEncrypted:
        """
        Returns a newly created dict containing this object's data attributes as defined by the get_attributes()
        method.

        :param encryption: an Encryption object to use for encrypting attribute values, or None for no encryption.
        :return: a dict of attribute names to attribute values.
        """
        pass

    @abc.abstractmethod
    def to_json(self, dumps: Callable[[HEAObjectDict], str] = json_dumps) -> str:
        """
        Returns a newly created JSON-formatted string containing this object's data attributes as defined by the
        get_attributes() method. Passes the json_encode function as the default parameter.

        :param dumps: any callable that accepts a HEAObject and returns a string.
        :return: a string.
        """
        pass

    @abc.abstractmethod
    def from_json(self, jsn: str, loads: Callable[[str | bytes | bytearray], HEAObjectDict] = json_loads) -> None:
        """
        Populates the object's data attributes as defined by the get_attributes() method with the attribute values in
        the provided JSON. The JSON must have a type attribute that matches this object's type. Properties that
        correspond to read-only data attributes or non-existent data attributes are ignored. This object's attributes
        are set in order of appearance in the JSON.

        Implementations of this method must catch and suppress AttributeError exceptions, which are raised when
        attempting to write to a read-only attribute, among other scenarios.

        :param jsn: a JSON string.
        :param loads: any callable that accepts str and returns dict with parsed JSON (json_loads() by default).
        :raises DeserializeException: if any of the JSON object's values are wrong, or the provided JSON
        document is not a valid JSON document.
        """
        pass

    @overload
    @abc.abstractmethod
    def from_dict(self, d: HEAObjectDict) -> None:
        pass

    @overload
    @abc.abstractmethod
    def from_dict(self, d: HEAObjectDict | HEAObjectDictIncludesEncrypted, *, encryption: Encryption) -> None:
        pass

    @overload
    @abc.abstractmethod
    def from_dict(self, d: HEAObjectDict, *, encryption: None) -> None:
        pass

    @abc.abstractmethod
    def from_dict(self, d: HEAObjectDict | HEAObjectDictIncludesEncrypted, *, encryption: Encryption | None = None) -> None:
        """
        Populates the object's data attributes as defined by the get_attributes() method with the attribute values in
        the given dict. The dict must have a type key whose value matches this object's type. Dict entries that
        correspond to read-only data attributes or non-existent data attributes are ignored. This object's attributes
        are set in order of appearance in the dictionary.

        Implementations of this method must catch and suppress AttributeError exceptions when setting attributes.
        Ideally, implementations should log such exceptions, at least at the DEBUG level, for diagnostic purposes.

        :param d: a mapping.
        :param encryption: an Encryption object to use for decrypting attribute values, or None for no decryption.
        :raises DeserializeException: if any of the mapping's values are wrong.
        """
        pass

    @property  # type: ignore
    @abc.abstractmethod
    def type(self) -> str:
        """
        The string representation of this object's type.

        :return: a string.
        """
        pass

    @property
    @abc.abstractmethod
    def type_display_name(self) -> str:
        """
        Returns a display name for the HEAObject type. Returns the type name if there is no display name.
        """
        pass

    @abc.abstractmethod
    def get_attributes(self) -> Iterator[str]:
        """
        Returns an iterator containing the object's member variables, including monkey-patched variables, that do not
        begin with an underscore. These are the attributes that are serialized by the to_dict() and to_json() methods.

        :return: an iterator of attribute names.
        """
        pass

    @abc.abstractmethod
    def has_attribute(self, attr: str) -> bool:
        """
        Returns whether the object has the given attribute.

        :param attr: the attribute name.
        :return: True or False.
        """
        pass

    @abc.abstractmethod
    def get_attribute_metadata(self, attr: str) -> AttributeMetadata:
        """
        Retrieve metadata for a specific attribute of the object.

        :param attr: The name of the attribute.
        :return: Metadata object.
        :raises AttributeError: if the attribute does not exist.
        """
        pass

    @abc.abstractmethod
    def get_all_attribute_metadata(self) -> dict[str, AttributeMetadata]:
        """
        Retrieve metadata for all attributes of the object.

        :param obj: The HEAObject to retrieve metadata for.

        :return: A dictionary mapping attribute names to their metadata.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def get_prompt(cls, field_name: Optional[str]) -> Optional[str]:
        pass

    @classmethod
    @abc.abstractmethod
    def is_displayed(cls, field_name: Optional[str]) -> bool:
        pass

    @classmethod
    @abc.abstractmethod
    def get_type_name(cls) -> str:
        """
        Returns a string representation of a HEAObject type.

        :return: a type string.
        """
        pass

class MemberObject(HEAObject, abc.ABC):
    """
    Interface for HEA objects that have a part-of relationship with a desktop objects and whose lifecycle is
    managed by the desktop object. Owned objects have the same permissions as the owning desktop object. As a result,
    they can be accessed by anyone who can access the desktop object, and they can be modified by anyone who can modify
    the desktop object. The desktop class and this class have a composition relationship in UML.
    """
    @abc.abstractmethod
    async def get_member_attribute_permissions(self, context: 'PermissionContext', attr: str) -> list[Permission]:
        """
        Get permissions for an attribute of this member object.

        :param context: the permission context (required).
        :param desktop_object: the member's desktop object (required).
        :param attr: the attribute (required).
        :return: a list of permissions.
        :raises ValueError: if this object does not have a parent desktop object.
        """
        pass

    @abc.abstractmethod
    def _set_parent_object(self, obj: Optional['DesktopObject']):
        """
        Sets the member object's parent desktop object. Set it to None to unset the parent object, for example, when
        removing the member object from the desktop object.

        :param obj: the desktop object or None.
        """
        pass

    @abc.abstractmethod
    def get_parent_object(self) -> Optional['DesktopObject']:
        """
        Gets the member object's parent desktop object, if it has been added to a desktop object.

        :return: the parent desktop object or None.
        """
        pass


class PermissionBasis(Enum):
    """
    Whether a permission assignment is based on a user or a group.
    """

    USER = 10
    GROUP = 20


class PermissionAssignment(MemberObject, abc.ABC):
    """
    Interface for permission assignments for desktop objects. Desktop objects are initially owned by the user who
    created them. After creating an object, the object's owner can share the object with other users and groups with
    the desired set of permissions. Optionally, users can invite another users and groups to access the object with the
    desired set of permissions, and the user will receive access upon accepting the invite. Permission assignment
    objects are owned by a desktop object.

    Permission assignments can be made to users or groups, but a PermissionAssignment object may only assign
    permissions to one user or one group. Setting one will clear the other (set it to system|none). If both are
    system|none, which is the default, then the permission assignment is for the system|none user. In real-world
    implementations, a permission assignment for the system|none user cannot exist, and so the permission assignment
    will be ignored. However, the system|none user is available for automated testing purposes.

    To determine whether a permission assignment is for a user or a group, check the basis attribute, or check which of
    the user and group properties is not equal to system|none, noting the semantics of the default values for the user
    and group properties above.
    """

    @property
    @abc.abstractmethod
    def user(self) -> str:
        """
        The user whose permissions will be impacted. Attempting to set it to None will set it to system|none. Setting
        it to a non-None value will also set the group to system|none.
        """
        pass

    @user.setter
    @abc.abstractmethod
    def user(self, user: str) -> None:
        pass

    @property
    @abc.abstractmethod
    def group(self) -> str:
        """
        The group whose permissions will be impacted. Attempting to set it to None will set it to system|none. Setting
        it to a non-None value will also set the user to system|none.
        """
        pass

    @group.setter
    @abc.abstractmethod
    def group(self, group: str) -> None:
        pass

    @property
    @abc.abstractmethod
    def basis(self) -> PermissionBasis:
        """
        The basis of the permission assignment. This is either a user or group. Any strings in the list will be parsed
        into PermissionBasis objects. Read-only.
        """
        pass

    @property
    @abc.abstractmethod
    def permissions(self) -> List[Permission]:
        """
        List of granted permissions. Any strings in the list will be parsed into Permission objects. Cannot be None.
        Attempting to set this attribute to None will result in setting it to the empty list.
        """
        pass

    @permissions.setter
    @abc.abstractmethod
    def permissions(self, perms: List[Permission]):
        pass

    @abc.abstractmethod
    def add_permission(self, perm: Permission):
        """
        Adds a permission the share.

        :param perm: the Permission.
        """
        pass

    @abc.abstractmethod
    def remove_permission(self, perm: Permission):
        """
        Removes a permission from the share.

        :param perm: the Permission.
        :raises ValueError: if the perm value is not present.
        """
        pass

    @abc.abstractmethod
    async def applies_to(self, context: 'PermissionContext') -> bool:
        """
        Returns whether the permission assignment applies to the provided permission context.

        :param context: the permission context (required).
        :return: True or False.
        """
        pass

    @abc.abstractmethod
    async def get_applicable_permissions(self, context: 'PermissionContext') -> AsyncIterator[Permission]:
        """
        Returns the permissions that apply to the provided permission context.

        :param context: the permission context (required).
        :return: an async iterator of permissions, if any.
        """
        yield Permission.VIEWER  # Dummy yield to enforce AsyncIterator type


class Invite(PermissionAssignment, abc.ABC):
    """
    Interface for invites to access a desktop object. Invite objects are owned by a desktop object, and as a result they
    do not have permissions of their own.
    """

    @property  # type: ignore
    @abc.abstractmethod
    def accepted(self) -> bool:
        """
        Whether the user has accepted the invite.
        """
        pass

    @accepted.setter  # type: ignore
    @abc.abstractmethod
    def accepted(self, accepted: bool) -> bool:
        pass


class Share(PermissionAssignment, abc.ABC):
    """
    Interface for representing the permissions of users to whom a desktop object has been shared. Share objects are
    owned by a desktop object, and as a result they do not have permissions of their own.
    """

    @property  # type: ignore
    @abc.abstractmethod
    def invite(self) -> Invite | None:
        """
        The invite, if any.
        """
        pass

    @invite.setter  # type: ignore
    @abc.abstractmethod
    def invite(self, invite: Invite | None) -> None:
        pass


HEAObjectTypeVar = TypeVar('HEAObjectTypeVar', bound=HEAObject)
DesktopObjectTypeVar = TypeVar('DesktopObjectTypeVar', bound='DesktopObject')
DesktopObjectTypeVar_contra = TypeVar('DesktopObjectTypeVar_contra', bound='DesktopObject', contravariant=True)
DesktopObjectTypeVar_cov = TypeVar('DesktopObjectTypeVar_cov', bound='DesktopObject', covariant=True)
MemberObjectTypeVar = TypeVar('MemberObjectTypeVar', bound=MemberObject)


class PermissionContext:
    """
    Helper class for determining object and attribute permissions. This class is a default implementation. Subclasses
    may be needed to consult external sources for permissions information, for example, when representing cloud data
    objects as desktop object. Subclasses should usually override get_permissions(), get_attribute_permissions(),
    get_association_many(), and get_groups() for custom functionality, though unless otherwise documented, all methods
    may be overridden if there is a performance benefit to doing so. Responses from external sources of permissions may
    be cached in the subclass to improve performance. The default implementation must be overridden by subclasses to
    provide group membership. Due the caching, it is recommended that PermissionContext objects be relatively
    short-lived.

    This implementation is all that is needed for desktop objects for determining permissions for the object's owner
    because by definition the owner has maximal permissions for the object and all its attributes. An external source
    would at most restrict access to the object and its attributes. Subclasses of this class must return the exact same
    permissions as this one for the object's owner.

    This class does not expect any constructor arguments. However, it supports cooperative multiple inheritance, and in
    a multiple inheritance situation, the constructor will pass any arguments on to the next class in the method
    resolution order.
    """
    def __init__(self, sub: str, **kwargs):
        """
        This class expects a user subject, and it will pass any other provided arguments through to the next class
        in the method resolution order.

        :param sub: the user subject (required).
        """
        super().__init__(**kwargs)
        if sub is None:
            raise ValueError('sub cannot be None')
        self.__sub = str(sub)
        self.__is_super_admin: bool | None = None

    @property
    def sub(self) -> str:
        return self.__sub

    async def get_groups(self) -> list[str]:
        """
        Gets the group ids for context's user sub. The default implementation does not consult any external sources for
        group membership and must be overridden by subclasses to provide group membership information. System users
        cannot be members of groups, and in permission contexts for system users, this method will always return an
        empty list.

        :return: a list of groups.
        """
        return []

    async def get_permissions(self, obj: 'DesktopObject') -> list[Permission]:
        """
        Gets the subject's permissions for a desktop object. If the subject is the owner of the object, or they are a
        super admin user and the object has its super_admin_has_all_permissions attribute set to True, then the user
        has all permissions. Otherwise, this method checks the object's shares and dynamic permissions. This behavior
        may be overridden. The provided desktop object must have been persisted (i.e., it must have populated id and
        instance_id attributes)

        :param obj: the desktop object (required).
        :return: a list of Permissions, or the empty list if there is none.
        """
        logger = logging.getLogger(__name__)
        sub = self.sub
        owner = obj.owner
        logger.debug('Checking permissions for user %s and object %r', sub, obj)
        if owner == sub or owner == ALL_USERS:
            logger.debug('Owner %s and sub %s are the same', owner, sub)
            return obj.get_owner_permissions()
        result = set[Permission]()
        if obj.super_admin_default_permissions and await self.is_super_admin():
            logger.debug('User %s is a super admin or a system user, and they have full access to object %r', sub, obj)
            result.update(obj.super_admin_default_permissions)
        for share in obj.shares:
            async for perm in share.get_applicable_permissions(self):
                result.add(perm)
        if obj.dynamic_permission_supported:
            result.update(obj.dynamic_permission(sub))
        logger.debug('Permissions for user %s and object %r: %s', sub, obj, result)
        return list(result)

    def is_system_user(self) -> bool:
        """
        Checks whether the current user is a system user.

        :return: True if the user is a system user, False otherwise.
        """
        return is_system_user(self.sub)

    async def is_super_admin(self) -> bool:
        """
        Checks whether the current user is a super admin. This method is not designed to be overridden. For non-system
        users, this method may call group_id_from() and get_groups(), which may involve resource-intensive database
        operations. As a result, the result of this method is cached for the lifetime of the PermissionContext object.

        :return: True if the user is a super admin, False otherwise.
        """
        if self.__is_super_admin is not None:
            return self.__is_super_admin
        else:
            groups = await self.get_groups()
            if groups:
                group_id = await self.group_id_from(_group.SUPERADMIN_GROUP)
                self.__is_super_admin = group_id in groups
            else:
                self.__is_super_admin = False
            return self.__is_super_admin

    async def get_permissions_as_share(self, obj: 'DesktopObject') -> Share:
        """
        Gets a user share representing permissions for a desktop object in a permissions context. This method is
        intended for desktop objects where the backend storage does not directly store HEA permissions, and the
        permissions must be computed from the context.

        :param obj: a desktop object (required).
        :return: a Share.
        """
        share: Share = ShareImpl()
        share.user = self.sub
        for perm in await self.get_permissions(obj):
            share.add_permission(perm)
        return share

    async def has_permissions(self, obj: 'DesktopObject', perms: Sequence[Permission] | PermissionGroup):
        """
        Returns whether a subject has any of the provided permissions for a desktop object. If the subject is the owner of
        the object, then the user has all permissions. Otherwise, this method checks the object's shares and dynamic
        permissions. This behavior may be overridden.

        :param obj: the desktop object (required).
        :param perms: the permissions to check (required).
        :returns: True or False.
        """
        if obj is None:
            raise ValueError('obj cannot be None')
        if perms is None:
            raise ValueError('perms cannot be None')
        if hasattr(perms, 'perms'):
            perms_: Sequence[Permission] = cast(PermissionGroup, perms).perms
        else:
            perms_ = perms
        return any(perm in perms_ for perm in await self.get_permissions(obj))

    async def is_read_only(self, obj: 'DesktopObject') -> bool:
        """
        Checks whether the subject has only VIEWER permission for an object. If the subejct is the owner of the object,
        the user has all permissions, and this method will return False. Otherwise, this method checks the object's
        shares and dynamic permissions. This behavior may be overridden.

        :param obj: the desktop object (required).
        :return: True or False.
        """
        if obj is None:
            raise ValueError('obj cannot be None')
        return await self.get_permissions(obj) == [Permission.VIEWER]

    async def get_attribute_permissions(self, obj: 'DesktopObject', attr: str) -> list[Permission]:
        """
        Gets the user's permissions for an attribute of the given desktop object. If the user is the object's owner or
        a super admin, then the user is granted VIEWER and EDITOR permissions for all non-read-only attributes, or
        VIEWER permission for read-only attributes. If the user has a user share or a group share, the user is granted
        at most the permissions defined in the share. Owner, super admin, user share, group share, and dynamic
        permissions are aggregated. If the user has dynamic permissions, the user is granted at most the permissions
        specified by the dynamic_permission function. The default custom_attribute_permissions method grants only
        VIEWER permission for read-only attributes.

        :param obj: the desktop object (required).
        :param attr: the attribute (required).
        :return: a list of Permissions, or the empty list if the subject has no permissions for the object's attribute.
        """
        if not hasattr(obj, attr):
            raise ValueError(f'Attribute {attr} does not exist on object {obj}')
        perms = set(await self.get_permissions(obj))
        attr_perms: set[Permission] = set()
        metadata = obj.get_attribute_metadata(attr)
        read_only_attr = metadata.read_only
        sharer_attr = metadata.requires_sharer
        super_admin = await self.is_super_admin()
        for perm in perms:
            if attr == 'owner' and obj.owner != self.sub and not super_admin and perm in DefaultPermissionGroup.ACCESSOR_PERMS:
                attr_perms.add(Permission.VIEWER)
                break
            elif not read_only_attr and ((sharer_attr and perm in DefaultPermissionGroup.SHARER_PERMS) or \
                (not sharer_attr and perm in DefaultPermissionGroup.UPDATER_PERMS)):
                attr_perms.add(Permission.VIEWER)
                attr_perms.add(Permission.EDITOR)
                break
            else:
                attr_perms.add(Permission.VIEWER)
        if attr_perms:
            if obj.owner == self.sub or super_admin or \
                bool(await anext((share for share in obj.shares if await share.applies_to(self)), None)):
                return list(attr_perms)
            elif (custom_perms := obj.dynamic_attribute_permission(attr, self.sub)) is None:
                return list(attr_perms)
            else:
                return [custom_perm for custom_perm in custom_perms if custom_perm in attr_perms]
        else:
            return []

    async def has_attribute_permissions(self, obj: 'DesktopObject', attr: str, perms: Sequence[Permission] | PermissionGroup) -> bool:
        """
        Checks whether the subject has any of the provided permissions for the attribute of an object.

        :param obj: the desktop object (required).
        :param attr: the attribute (required).
        :param perms: the permissions to check (required).
        :return: True or False.
        """
        if obj is None:
            raise ValueError('obj cannot be None')
        if attr is None:
            raise ValueError('attr cannot be None')
        if perms is None:
            raise ValueError('perms cannot be None')
        if hasattr(perms, 'perms'):
            perms_: Sequence[Permission] = cast(PermissionGroup, perms).perms
        else:
            perms_ = perms
        return any(perm in perms_ for perm in await self.get_attribute_permissions(obj, attr))

    async def is_attribute_read_only(self, obj: 'DesktopObject', attr: str) -> bool:
        """
        Checks whether the subject has only VIEWER permission for the attribute of an object.

        :param obj: the desktop object (required).
        :param attr: the attribute (required).
        :return: True or False.
        """
        return await self.get_attribute_permissions(obj, attr) == [Permission.VIEWER]

    async def can_create(self, desktop_object_type: type['DesktopObject']) -> bool:
        """
        Checks whether the current user has permission to create this type of object. This default implementation
        always returns True. Override this method to change its behavior.

        There are two potential sources of information for whether a user can create objects: the permission context
        and the registry. The permission context is the source of truth when the context implementation's can_create
        method is documented as such. Otherwise, can_create always returns True, and retrieve the registry resource
        corresponding to the object type and check its is_creator method.

        :param desktop_object_type: the desktop object type to check.
        :return: True or False.
        """
        return True

    async def group_id_from(self, group: str) -> str:
        """
        Gets the group id for a group path. The default implementation assumes the id and the group are the same. In
        most situations, you will want to override this method to return the id of the group from a database. Passing
        a system user into this method will return itself. Expensive operations to retrieve the group id should be
        cached to improve performance.

        :param group: the group (required).
        :return: the group id.
        """
        return group

class ViewerPermissionContext(PermissionContext):
    """
    Implementation where all users have VIEWER permissions for all objects.
    """

    async def get_permissions(self, obj: 'DesktopObject') -> list[Permission]:
        """
        Always returns VIEWER permissions for the object.

        :param obj: the desktop object (required).
        :return: a list containing just Permission.VIEWER.
        """
        return [Permission.VIEWER]

    async def can_create(self, desktop_object_type: type['DesktopObject']) -> bool:
        """
        Always returns False, indicating the user cannot create objects. When this permission context implementation is
        used, it is the source of truth for whether a user can create objects.

        :param desktop_object_type: the desktop object type to check (required).
        :return: False.
        """
        return False

class AssociationContext:

    def __init__(self, **kwargs):
        """
        This class expects a user sub, and it will pass any other provided arguments through to the next class
        in the method resolution order.

        :param sub: the user (required).
        """
        super().__init__(**kwargs)

    async def get_association_many(self, obj: 'DesktopObject', attr: str, type_: type[DesktopObjectTypeVar]) -> list[DesktopObjectTypeVar]:
        """
        Gets the associated objects when the association is one-to-many or many-to-many. For one-to-one and many-to-one
        associations, an empty list or list of one is returned. This default implementation raises a ValueError.

        :param obj: the desktop object (required).
        :param attr: the attribute (required).
        :param type_: the type of the target objects in the association.
        :raises ValueError: if an error occurred, or the attr does not represent an association.
        """
        raise ValueError('Not an association')

    async def get_association_one(self, obj: 'DesktopObject', attr: str, type_: type[DesktopObjectTypeVar]) -> DesktopObjectTypeVar | None:
        """
        Gets the associated object when the association is one-to-one or many-to-one. For one-to-many and many-to-many
        associations, just one of the associated objects is returned. This default implementation delegates to
        get_association_many() and returns the first object returned by it.

        :param obj: the desktop object (required).
        :param attr: the attribute (required).
        :param type_: the type of the target objects in the association.
        :returns: the associated object, or None.
        :raises ValueError: if an error occurred, or the attr does not represent an association.
        """
        result = await self.get_association_many(obj, attr, type_)
        return next(iter(result), None)


class DesktopObject(HEAObject, abc.ABC):
    """
    Interface for objects that can appear on the HEA desktop. Desktop objects have permissions, with those permissions
    represented by owned objects implementing the MemberObject interface. Other attributes may also employ owned
    objects. One or more HEA microservices provide CRUD (create, read, update, and delete) operations on each desktop
    object type. Additional HEA microservices may implement actions that use specific desktop object types.

    Desktop objects implement no capability to check the current user when getting and setting owned objects, and
    different users may only have access to a subset of its owned objects. Similarly, owned objects have no knowledge of
    permissions at all. It is imperative that users gain access to desktop objects by calling an appropriate HEA
    microservice as themselves, which will filter the owned objects that are returned according to their permissions.

    Desktop objects may employ the following permission checks to determine whether to return a desktop object to a
    user or save the desktop object with a user's changes. Attribute-level permissions checks are also available.

    1) User-based: if the user is the object's owner, then the user can do anything with the object.
    2) Group-based: if the user is a member of the super-admin group, and the object's super_admin_has_all_permission
    attribute is set to True, then the user can do anything with the object.
    3) Shares-based: if the owner has shared the object with a user, then the user can use the object according to the
    values of the heaobject.root.Permission enum specified in the Share object.
    4) Dynamic permissions: Implemented using the dynamic_permission and dynamic_attribute_permission methods, they use
    the object's attribute values to determine the user's permissions. They will only be invoked if the object's
    dynamic_permission_supported attribute is True.
    5) The permissions context: a heaobject.root.PermissionContext object is passed into all the desktop object
    permissions checking methods except for the dynamic permissions methods above. The default permissions context
    implementation, PermissionContext, checks aggregates user and shares-based permissions, and if the object's
    dynamic_permission_supported attribute is True, adds any permissions returned by the dyanmic_permission and
    dynamic_atribute_permission methods. Subclasses may perform addition permissions checking or override the above
    checks and implement their own.

    The permissions granted will be the greatest of the above checks. Being an object's owner trumps everything. The
    shares-based and dynamic permissions-based approaches both return heaobject.root.Permission objects, and the most
    permissive permissions prevail.

    Objects may have any of the permissions in the Permissions enum. Attributes may only have the Permission.VIEWER
    and/or the Permission.EDITOR permissions. The PermissionContext class grants the id, modified, and created
    attributes only Permission.VIEWER permissions, and it grants all other attributes Permission.VIEWER and
    Permission.EDITOR permissions. Object-level permissions override attribute-level permissions. For example, an
    object cannot grant a user Permission.EDITOR permissions to an attribute if the user's object-level permissions do
    not include Permission.EDITOR or Permission.COOWNER. Subclasses of PermissionContext should honor this constraint.

    When updating and persisting an object, implementations must ensure that attributes for which the user lacks the
    Permission.EDITOR privilege are NOT updated, in other words, those attributes must retain the previously persisted
    values.

    If a microservice provides an object to a user who is not the object's owner, and the object has not been shared
    with the user, this should be interpreted as unknown permissions. In this situation, the microservices responsible
    for the object must deny operations that the user might attempt on the object for which the user lacks the
    necessary permissions. An example where this situation might occur is when a user accesses desktop objects
    representing data in a cloud storage service that has its own permissions system and correctly denies access when
    the user lacks the necessary permissions, but the service lacks APIs for querying those permissions.

    Desktop objects may have a class variable, associations, with type Dict[attribute, str]. For properties ending in
    _id or _ids that represent an association relationship with another desktop object type, it defines the type name
    of the desktop object being referred to. The associations variable is intended to have many purposes. In the future,
    implementations of the dynamic_permission() method might use these annotations to traverse an association
    relationship to another desktop object as part of permissions checking.

    Desktop objects may be versioned, indicated by the presence of a version attribute. For convenience, the
    VersionedDesktopObject and AbstractVersionedDesktopObject classes provide a default implementation of this
    attribute. Desktop objects represent one version of the actual persisted object.
    """

    @attribute_metadata(read_only=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def id(self) -> Optional[str]:
        """
        The object's resource unique identifier. It must be unique among all
        objects of the same type. The id is expected to be generated by a
        database in which the objects are stored, thus prior to storing the
        object the id is expected to be None. In a client-server application,
        the id is generated on the server side and provided back to the client.
        The id may not be the empty string.

        When an application needs to store updates of an object in a database,
        the application should first arrange to store the original version of
        the object and get its generated id back from the database for use in
        subsequent updates. However, in asynchronous operations this may not be
        possible, such as when an object and updates to it are sent over a
        message queue. In a message queue, the sender may generate updates to
        an object before the receiver finishes processing the original object
        version.

        In this case, the application must generate and maintain its own object
        id, and the object class should provide a different attribute for the
        application to store it. The database will still generate its id and
        store it in the id field, thus the object will have two unique ids, a
        database-generated id and an application-generated id. Typical methods
        for generating ids on the application side such as UUIDs are highly
        reliable but may be somewhat less reliable over the long term than
        database-generated ids. Thus, applications should use database-
        generated ids whenever feasible and treat application-generated ids as
        temporary. Applications should link the database- and application-
        generated ids. In a client-server application, this must happen server-
        side so that the server can appropriately store objects received from
        the client with only an application-generated id. However, the client
        could maintain its own linkage if necessary.

        In client-server applications with multiple server processes such as
        microservices, application-generated ids should be based upon unique
        identifiers of the source of the object, which depending on the
        architecture might include IP address or other form of host identifier,
        so that objects generated by separate server processes cannot clash.
        Consider security concerns if the generated ids may become visible to
        users.

        For some HEAObject classes, it may be natural for its unique id to be
        a string with characters that cannot be incorporated into a URL's path,
        such as /. The same is true for HEAObject's name attribute. For this
        situation, we recommend encoding the value using URL-safe base 64
        encoding as described in IETF RFC 4648 section 5, and adding a custom
        attribute to the class for storing the actual id/name value. The id,
        name, and custom attributes can be synchronized such that setting the
        custom attribute automatically generates an encoded value that can be
        accessed via the id and/or name attributes. The id may not be the empty
        string.
        """
        pass

    @id.setter  # type: ignore
    @abc.abstractmethod
    def id(self, id_: Optional[str]) -> None:
        pass

    @attribute_metadata(read_only=True)  # type: ignore[prop-decorator]
    @property
    @abc.abstractmethod
    def instance_id(self) -> str | None:
        """An identifier that is unique across all desktop objects in a single deployment of HEA. It is created at
        storage time, like the id attribute. Prior to storage, its value will be None. When there are multiple
        subclasses of a desktop object class, the instance_id value serves as a globally unique id across all
        subclasses. It takes the form type^id, or None if the object has no id."""
        pass

    @property  # type: ignore
    @abc.abstractmethod
    def source(self) -> Optional[str]:
        """
        A string indicating the object's source system
        """
        pass

    @source.setter  # type: ignore
    @abc.abstractmethod
    def source(self, source: Optional[str]) -> None:
        pass

    @property  # type: ignore
    @abc.abstractmethod
    def source_detail(self) -> Optional[str]:
        """
        Additional details about the object's source.
        """
        pass

    @source_detail.setter  # type: ignore
    @abc.abstractmethod
    def source_detail(self, source: Optional[str]) -> None:
        pass

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def name(self) -> Optional[str]:
        """
        This object's name. The name must be unique across all objects of the same type, sometimes in combination with
        the object's owner. For some HEAObject classes, it may be natural for its name to be a string with characters
        that cannot be incorporated into a URL's path, such as /. The same is true for HEAObject's id attribute. For
        this situation, we recommend encoding the value using URL-safe base 64 encoding as described in IETF RFC 4648
        section 5, and adding a custom attribute to the class for storing the actual id/name value. The id, name, and
        custom attributes can be synchronized such that setting the custom attribute automatically generates an encoded
        value that can be accessed via the id and/or name attributes, and setting the id or name attribute
        automatically generates a decoded value that is returned by the custom attribute. The name may not be the empty
        string.
        """
        pass

    @name.setter  # type: ignore
    @abc.abstractmethod
    def name(self, name: Optional[str]) -> None:
        pass

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def display_name(self) -> str:
        """
        The object's display name. The default value is the object's name. If the name is None, then a sensible
        default value is returned.
        """
        pass

    @display_name.setter  # type: ignore
    @abc.abstractmethod
    def display_name(self, display_name: str) -> None:
        pass

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def description(self) -> Optional[str]:
        """
        The object's description.
        """
        pass

    @description.setter  # type: ignore
    @abc.abstractmethod
    def description(self, description: Optional[str]) -> None:
        pass

    @property  # type: ignore
    @abc.abstractmethod
    def owner(self) -> str:
        """
        The username of the object's owner. Cannot be None. Defaults to heaobject.user.NONE_USER.
        """
        pass

    @owner.setter  # type: ignore
    @abc.abstractmethod
    def owner(self, owner: str) -> None:
        pass

    @attribute_metadata(read_only=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def created(self) -> Optional[date]:
        """
        The date or datetime at which this object was initially stored, as a
        date object. Setting this attribute with an ISO 8601 string will also
        work -- the ISO string will be parsed automatically as a datetime
        object.
        """
        pass

    @created.setter  # type: ignore
    @abc.abstractmethod
    def created(self, value: Optional[date]) -> None:
        pass

    @attribute_metadata(read_only=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def modified(self) -> Optional[date]:
        """
        The date or datetime at which the latest update to this object was
        stored. Setting this attribute with an ISO 8601 string will also work --
        the ISO string will be parsed automatically as a datetime object.
        """
        pass

    @modified.setter  # type: ignore
    @abc.abstractmethod
    def modified(self, value: Optional[date]) -> None:
        pass

    @property  # type: ignore
    @abc.abstractmethod
    def derived_by(self) -> Optional[str]:
        """
        The id of the mechanism by which this object was derived, if any.
        """
        pass

    @derived_by.setter  # type: ignore
    @abc.abstractmethod
    def derived_by(self, derived_by: Optional[str]) -> None:
        pass

    @property  # type: ignore
    @abc.abstractmethod
    def derived_from(self) -> List[str]:
        """
        A list of the ids of the HEAObjects from which this object was derived. If None, will be set to the default
        value (the empty list).
        """
        pass

    @derived_from.setter  # type: ignore
    @abc.abstractmethod
    def derived_from(self, derived_from: List[str]) -> None:
        pass

    @attribute_metadata(requires_sharer=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def invites(self) -> list[Invite]:
        """
        A list of Invite objects representing the users who have been invited to access this object. If None, will be
        set to the default value (the empty list). Duplicate invites will be ignored. Other invalid input will raise a
        ValueError.
        """
        pass

    @invites.setter  # type: ignore
    @abc.abstractmethod
    def invites(self, invites: list[Invite]) -> None:
        pass

    @property
    @abc.abstractmethod
    def super_admin_default_permissions(self) -> list[Permission]:
        """
        Returns the permissions that the /*super-admin group automatically has for this object. Additional permissions
        can be granted by making such a user the object's owner or by sharing the object with them. The default value
        is the empty list.
        """
        pass

    @abc.abstractmethod
    def add_invite(self, invite: Invite):
        """
        Adds an invite to the desktop object. Attempting to add an invite that is already in this desktop object's
        invites list will be ignored. Other invalid input will raise a ValueError.

        :param invite: an Invite (required).
        """
        pass

    @abc.abstractmethod
    def remove_invite(self, invite: Invite):
        """Removes an invite from the desktop object. Invites that are not in this desktop object's invites list are
        ignored.

        :param invite: an Invite (required).
        """
        pass

    @attribute_metadata(read_only=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def shares(self) -> list[Share]:
        """
        A list of Share objects representing all user and group permissions assigned to this desktop object. The shares
        attribute, in combination with the owner attribute, may reflect all permissions for all users and gruops, or
        they may only reflect permissions of the user requesting the desktop object. Add and remove shares using the
        user_shares and group_shares attributes and their corresponding add_* and remove_* methods.
        """
        pass

    @attribute_metadata(requires_sharer=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def user_shares(self) -> list[Share]:
        """
        A list of Share objects representing all user permissions assigned to this desktop object. If set to
        None, it will be set to the default value, the empty list. Duplicate shares will be ignored. The shares
        attribute, in combination with the owner attribute, may reflect all permissions for all users, or they may only
        reflect permissions of the user requesting the desktop object. In the latter case, the shares attribute must be
        read-only.
        """
        pass

    @user_shares.setter  # type: ignore
    @abc.abstractmethod
    def user_shares(self, shares: list[Share]) -> None:
        pass

    @abc.abstractmethod
    def add_user_share(self, share: Share):
        """
        Adds a user share to the desktop object. Attempting to add a share that is already in this desktop object's
        user shares list or is not a user share will be ignored.

        :param share: a user Share (required).
        """
        pass

    @abc.abstractmethod
    def remove_user_share(self, share: Share):
        """Removes a user share from the desktop object. Shares that are not in this desktop object's user shares list
        are ignored.

        :param share: a Share (required).
        """
        pass

    @attribute_metadata(requires_sharer=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    @abc.abstractmethod
    def group_shares(self) -> list[Share]:
        """
        A list of Share objects representing all group permissions assigned to this desktop object. If set to
        None, it will be set to the default value, the empty list. Duplicate shares will be ignored. The shares
        attribute, in combination with the owner attribute, may reflect all permissions for all groups, or they may
        only reflect permissions of the group membership of the user requesting the desktop object. In the latter case,
        the shares attribute must be read-only.
        """
        pass

    @group_shares.setter  # type: ignore
    @abc.abstractmethod
    def group_shares(self, shares: list[Share]) -> None:
        pass

    @abc.abstractmethod
    def add_group_share(self, share: Share):
        """
        Adds a group share to the desktop object. Attempting to add a share that is already in this desktop object's
        group shares list or is not a group share will be ignored.

        :param share: a group Share (required).
        """
        pass

    @abc.abstractmethod
    def remove_group_share(self, share: Share):
        """
        Removes a share from the desktop object. Shares that are not in this desktop object's shares list are
        ignored.

        :param share: a Share (required).
        """
        pass

    @abc.abstractmethod
    def add_share(self, share: Share):
        """
        Adds a share to the desktop object. Attempting to add a share that is already in this desktop object's shares
        list will be ignored.

        :param share: a Share (required).
        """

    @abc.abstractmethod
    def remove_share(self, share: Share):
        """
        Removes a share from the desktop object. Attempting to remove a share that is not present will be ignored.

        :param share: a Share (required).
        """

    @property
    @abc.abstractmethod
    def dynamic_permission_supported(self) -> bool:
        """
        Whether the object supports dynamic permissions. The default value is False. Override this attribute to
        return True for classes for which the dynamic_permissions attribute might have a non-empty list value."""
        pass

    @abc.abstractmethod
    def dynamic_permission(self, sub: str) -> list[Permission]:
        """
        Uses the object's attributes to determine what additional permissions a user may have to this object. The
        PermissionsContext class may use the return value of this method to add permissions for a user to a desktop
        object when the is_dyanmic_permission_supported method returns True.

        :param sub: the user id to check.
        :return: a list of Permission enum values, or an empty list to signify no permissions.
        """
        pass

    @abc.abstractmethod
    def dynamic_attribute_permission(self, attribute: str, sub: str) -> list[Permission] | None:
        """
        Restricts permissions for the object's attributes when the user is not the object's owner, is not a super
        admin user, and does not have a user share nor a group share. It may be called by a permission context's
        get_attribute_permissions method and must never be used separately.

        :param attribute: the attribute to check.
        :param sub: the user id to check.
        :return: VIEWER and/or EDITOR permissions, an empty list to signify no permissions, or None to indicate that
        this method doesn't calculate permissions for the attribute.
        """
        pass

    @abc.abstractmethod
    async def get_permissions(self, context: PermissionContext) -> list[Permission]:
        """
        Gets permissions for this object for the current permissions context. The returned permissions may be dependent
        on the desktop object's attributes but not on the object's attribute permissions.

        :param context: the current permission context (required).
        :return: a list of Permission enum values, or an empty list to signify no permissions.
        """
        pass

    @abc.abstractmethod
    async def get_permissions_as_share(self, context: PermissionContext) -> Share:
        """
        Gets a Share representing the permissions for the current permissions context. The returned permissions may be
        dependent on the desktop object's attributes but not on the object's attribute permissions.

        :param context: the current permission context (required).
        :return: a Share.
        """
        pass

    @abc.abstractmethod
    async def has_permissions(self, perms: Sequence[Permission] | PermissionGroup, context: PermissionContext) -> bool:
        """
        Returns whether the subject in the current permission context has any of the provided permissions for this
        object. The returned value may be dependent on the desktop object's attributes but not on the object's
        attribute permissions.

        :param perms: the permissions to check (required), which may be passed as a sequence of Permission objects or
        an object adhering to the PermissionGroup protocol.
        :param context: the current permission context (required).
        :return: True or False.
        """
        pass

    @abc.abstractmethod
    async def is_read_only(self, context: PermissionContext) -> bool:
        """
        Returns whether the subject in the current permission context has read-only permissions for this object.

        :param context: the current permission context (required).
        :return: True or False.
        """
        pass

    @abc.abstractmethod
    async def get_attribute_permissions(self, attr: str, context: PermissionContext) -> list[Permission]:
        """
        Gets the permissions for the specified attribute of this object given a permission context. The returned values
        may depend on the object's attribute values but cannot depend on the return value of
        get_permissions/get_permissions_as_share/has_permissions/etc.

        :param attr: the attribute to check (required).
        :param context: a permission context (required).
        :return: list of Permission.VIEWER and/or Permission.EDITOR, or the empty list.
        """
        pass

    @abc.abstractmethod
    async def get_all_attribute_permissions(self, context: PermissionContext) -> dict[str, list[Permission]]:
        """
        Gets permissions for all attributes of this object given a permission context.

        :param context: a permission context (required).
        :return: list of Permission.VIEWER and/or Permission.EDITOR, or the empty list.
        """
        pass

    @abc.abstractmethod
    async def has_attribute_permissions(self, attr: str, perms: Sequence[Permission] | PermissionGroup, context: PermissionContext) -> bool:
        """
        Gets whether the subject in the current permission context has any of the provided permissions for the
        specified attribute of this object.

        :param attr: the attribute to check (required).
        :param perms: the permissions to check (required), which may be passed as a sequence of Permission objects or
        an object adhering to the PermissionGroup protocol.
        :param context: the current permission context (required).
        :return: True or False.
        """
        pass

    @abc.abstractmethod
    async def is_attribute_read_only(self, attr: str, context: PermissionContext) -> bool:
        """
        Uses the subject's permissions to determine whether the given attribute is read-only. This method delegates to
        the current permission context.

        :param attr: the attribute to check (required).
        :param context: the current permission context (required).
        :return: True or False.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def get_owner_permissions(cls) -> list[Permission]:
        """
        Returns the expected permissions for owners of objects of this class. The default value is all permissions
        except for Permission.CREATOR. A PermissionContext implementation may assign different permissions to the owner
        as needed.

        :return: a list of Permission enum values.
        """
        pass

    @classmethod
    @abc.abstractmethod
    async def can_create(cls, context: PermissionContext) -> bool:
        """
        Returns whether the user has permission to create this type of object.

        :param context: the current permission context (required).
        :return: True or False.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def get_subclasses(cls) -> Iterator[type['DesktopObject']]:
        """
        Returns an iterator of subclasses of this class that have previously been loaded into the python interpreter.
        :return: an iterator of DesktopObject types.
        """
        pass


class AbstractHEAObject(HEAObject, abc.ABC):
    """
    Abstract base class for all HEA objects. HEA objects are data transfer objects for moving data between HEA
    microservices as well as between a HEA microservice and a web browser or other client. HEA objects have no behavior
    except support for storage, retrieval, serialization, and deserialization. The AbstractHEAObject class provides
    default implementations for setting and getting attributes, as well as default implementations of behaviors.

    There are two sub-types of HEA objects: desktop objects (DesktopObject) and owned
    objects (MemberObject). The AbstractDesktopObject and AbstractMemberObject classes provide default implementations
    for setting and getting attributes, and default implementations of behaviors. There may be additional sub-types in
    the future.

    Desktop objects represent objects that appear on the HEA desktop. Desktop objects have permissions, timestamps for
    when the object was created and modified, versions, and more. One or more HEA microservices provide CRUD (create,
    read, update, and delete) operations on each desktop object type. Additional HEA microservices may implement actions
    that consume or produce specific desktop object types.

    Owned objects cannot appear by themselves on the HEA desktop. Instead, they have a part-of relationship with a
    desktop object, and their lifecycle is managed by the desktop object. Example owned objects represent permissions
    and data sharing. While owned objects provide for their own storage, retrieval, serialization, and deserialization,
    these behaviors are always invoked by the desktop object of which they are a part.

    HEA object implementations must conform to several conventions to ease their use and reuse across the HEA desktop.
    All subclasses of HEAObject must have a zero-argument constructor. All non-callable instance members must be
    included in the to_dict() and json_dumps() methods. Copies and deep copies using the copy module will copy all
    non-callable instance members of any subclass of HEAObject. Override __copy__ and __deepcopy__ to change that
    behavior. In addition, HEA objects should include type annotations for all properties and callables.

    Desktop objects implement no capability to check the current user when getting and setting owned objects, and
    different users may only have access to a subset of its owned objects. Similarly, owned objects have no knowledge of
    permissions at all. It is imperative that users gain access to desktop objects by calling an appropriate HEA
    microservice as themselves, which will filter the owned objects that are returned according to their permissions.
    """

    __cls_type_attributes: set[str] | None = None
    __cls_attributes: set[str] | None = None

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.__cls_type_attributes = None
        cls.__cls_attributes = None

    @abc.abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.__attributes: dict[str, None] = {}   # ensure the attributes are always returned in the same order.
        self.__added_cls_attributes = False

    @overload
    def to_dict(self) -> HEAObjectDict:
        pass

    @overload
    def to_dict(self, encryption: Encryption) -> HEAObjectDictIncludesEncrypted:
        pass

    @overload
    def to_dict(self, encryption: None) -> HEAObjectDict:
        pass

    def to_dict(self, encryption: Encryption | None = None) -> HEAObjectDict | HEAObjectDictIncludesEncrypted:
        def nested(obj, a: str, encrypt: bool):
            match obj:
                case HEAObject():
                    return obj.to_dict(encryption=encryption)
                case list():
                    return [nested(o, a, encrypt) for o in obj]
                case Enum():
                    return obj.name
                case str():
                    if encryption and encrypt:
                        return encryption.encrypt(obj.encode('utf-8'))
                    else:
                        return obj
                case _:
                    return obj

        return {a: nested(getattr(self, a), a, self.get_attribute_metadata(a).needs_encryption) for a in self.get_attributes()}

    def to_json(self, dumps: Callable[[HEAObjectDict], str] = json_dumps) -> str:
        return dumps(self.to_dict())

    def from_json(self, jsn: str, loads: Callable[[str | bytes | bytearray], HEAObjectDict] = json_loads) -> None:
        try:
            self.from_dict(loads(jsn))
        except orjson.JSONDecodeError as e:
            raise DeserializeException from e

    @overload
    def from_dict(self, d: HEAObjectDict) -> None:
        pass

    @overload
    def from_dict(self, d: HEAObjectDict | HEAObjectDictIncludesEncrypted, *, encryption: Encryption) -> None:
        pass

    @overload
    def from_dict(self, d: HEAObjectDict, *, encryption: None) -> None:
        pass

    def from_dict(self, d: HEAObjectDict | HEAObjectDictIncludesEncrypted, *, encryption: Encryption | None = None) -> None:
        try:
            for k, v in d.items():
                if self.has_attribute(k):
                    if isinstance(v, list):
                        lst: list[Union[HEAObject, Primitive]] = []
                        for e in v:
                            if isinstance(e, dict):
                                if 'type' not in e:
                                    raise ValueError(
                                        'type attribute is required in nested dicts but is missing from {}'.format(e))
                                e_type = str(e['type'])  # python 3.15 PEP 728 will let us define a TypedDict instead.
                                obj = type_for_name(e_type)()
                                if encryption:
                                    obj.from_dict(e, encryption=encryption)
                                else:
                                    obj.from_dict(cast(HEAObjectDict, e))
                                lst.append(obj)
                            elif encryption is not None and isinstance(e, bytes):
                                lst.append(encryption.decrypt(e).decode('utf-8'))
                            elif not isinstance(e, bytes):
                                lst.append(e)
                            else:
                                raise ValueError('Unexpected list element type: {}'.format(type(e)))
                        self.__setattr_known_and_writeable(k, lst)
                    elif isinstance(v, dict):
                        if 'type' not in v:
                            raise ValueError(
                                'type attribute is required in nested dicts but is missing from {}'.format(v))
                        v_type = str(v['type'])   # python 3.15 PEP 728 will let us define a TypedDict instead.
                        obj = type_for_name(v_type)()
                        if encryption:
                            obj.from_dict(v, encryption=encryption)
                        else:
                            obj.from_dict(cast(HEAObjectDict, v))
                        self.__setattr_known_and_writeable(k, obj)
                    elif k != 'type':
                        if encryption is not None and isinstance(v, bytes) and \
                                self.get_attribute_metadata(k).needs_encryption:
                            self.__setattr_known_and_writeable(k, encryption.decrypt(v).decode('utf-8'))
                        else:
                            self.__setattr_known_and_writeable(k, v)
                    else:
                        if v != self.type:
                            raise ValueError(
                                f"type attribute does not match object type: object type is {self.type} but the dict's type attribute has value {str(v)}")
        except (ValueError, TypeError) as e:
            raise DeserializeException(str(e)) from e

    @property
    def type(self) -> str:
        return self.get_type_name()

    @property
    def type_display_name(self):
        return type(self).__name__

    def get_attributes(self) -> Iterator[str]:
        """
        Returns an iterator of this object's attribute names. This method is not designed to be overridden.

        :return: an iterator of attribute names.
        """
        self.__populate_attributes_if_needed()
        return iter(self.__attributes)

    def has_attribute(self, attr: str) -> bool:
        """
        Returns whether this object has the specified attribute. This method is not designed to be overridden.

        :param attr: the attribute name (required).
        :return: True or False.
        """
        self.__populate_attributes_if_needed()
        return attr in self.__attributes

    def get_attribute_metadata(self, attr: str) -> AttributeMetadata:
        if (m := get_attribute_metadata(getattr(type(self), attr, None))) is not None:
            return m
        elif self.has_attribute(attr):
            return DEFAULT_ATTRIBUTE_METADATA
        else:
            raise AttributeError(f'Attribute {attr} not found in object of type {self.get_type_name()}')

    def get_all_attribute_metadata(self) -> dict[str, AttributeMetadata]:
        return {attr: self.get_attribute_metadata(attr) for attr in self.get_attributes()}

    @classmethod
    def __get_type_attributes(cls) -> set[str]:
        """
        Returns class attributes to be fed into the _get_attributes() function.

        :return: a set of class attributes.
        """
        if cls.__cls_type_attributes is None:
            cls.__cls_type_attributes = _get_type_attributes(cls)
        return cls.__cls_type_attributes

    def __setattr__(self, attr, value):
        if not attr.startswith('_'):
            self.__attributes[attr] = None  # tracks monkey-patched attributes.
        super().__setattr__(attr, value)

    @classmethod
    def get_prompt(cls, field_name: Optional[str]) -> Optional[str]:
        return field_name

    @classmethod
    def is_displayed(cls, field_name: Optional[str]) -> bool:
        return True if field_name != 'id' else False

    @classmethod
    def get_type_name(cls) -> str:
        return cls.__module__ + '.' + cls.__name__

    def __setattr_known_and_writeable(self, name: str, value: Any) -> None:
        """
        Sets any of this object's attributes, ignoring attempts to set read-only attributes or to monkey patch the object with additional attributes.

        :param name: the name of the attribute.
        :param value: the attribute's value.
        """
        try:
            setattr(self, name, value)
        except AttributeError:
            logger = logging.getLogger(__name__)
            if not hasattr(self, name):
                logger.debug('Attempted to set an unexpected attribute %s.%s=%s. HEA will ignore this attribute.',
                             self,
                             name, value)


    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        attrs = set(self.get_attributes()).union(other.get_attributes())
        return all(getattr(self, a, None) == getattr(other, a, None) for a in attrs)

    def __repr__(self) -> str:
        return f'heaobject.root.from_dict({self.to_dict()!r})'

    def __copy__(self):
        clz = type(self)
        result = clz()
        for a in self.get_attributes():
            try:
                setattr(result, a, getattr(self, a))
            except AttributeError:
                pass  # Skip read-only attributes
        return result

    def __deepcopy__(self, memo):
        result = type(self)()
        for a in self.get_attributes():
            try:
                setattr(result, a, copy.deepcopy(getattr(self, a), memo))
            except AttributeError:
                pass  # Skip read-only attributes
        return result

    def __populate_attributes_if_needed(self):
        if self.__cls_attributes is None:
            self.__cls_attributes = _get_attributes(self, self.__get_type_attributes())
        if not self.__added_cls_attributes:
            for a in self.__cls_attributes:
                self.__attributes[a] = None
            self.__added_cls_attributes = True


class AbstractMemberObject(AbstractHEAObject, MemberObject, abc.ABC):
    """
    Abstract base class for all classes that are owned by a desktop class. Owned classes have a part-of relationship
    with a desktop class, and their lifecycle is managed by the desktop class. The desktop class and this class have a
    composition relationship in UML. Owned objects have the same permissions as the owning desktop object. As a result,
    they can be accessed by anyone who can access the desktop object, and they can be modified by anyone who can modify
    the desktop object.
    """

    @abc.abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.__parent: DesktopObject | None = None

    def _set_parent_object(self, obj: DesktopObject | None):
        if obj is not None and not isinstance(obj, DesktopObject):
            raise ValueError(f'obj is {type(obj)} not a DesktopObject')
        self.__parent = obj

    def get_parent_object(self) -> DesktopObject | None:
        return self.__parent

    async def get_member_attribute_permissions(self, context: PermissionContext, attr: str) -> list[Permission]:
        parent = self.get_parent_object()
        if parent is None:
            raise ValueError('No parent desktop object')
        return [Permission.VIEWER, Permission.EDITOR]


class VersionedDesktopObject(DesktopObject, abc.ABC):
    """
    Interface for desktop objects that can be versioned. The presence of the version attribute provided by this
    interface indicates that a desktop object is versioned, irrespective of whether the object's class implements this
    interface.
    """
    @property  # type: ignore
    @abc.abstractmethod
    def version(self) -> Optional[str]:
        """
        The current version of this object.
        """
        pass

    @version.setter
    @abc.abstractmethod
    def version(self, version: str | None):
        pass


class AbstractPermissionAssignment(AbstractMemberObject, PermissionAssignment, abc.ABC):
    """
    Abstract base class for permissions-related classes. Desktop objects are owned by the user who created them.
    After creating an object, the object's owner can share the object with other users with the desired set of
    permissions. Optionally, users can invite another users to access the object with the desired set of permissions,
    and the user will receive access upon accepting the invite. Permission assignment objects are owned by a desktop
    object. As a result, they can be accessed by anyone who can access the desktop object, and they can be
    modified by anyone who can modify the desktop object.
    """

    @abc.abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.__user = _user.NONE_USER
        self.__group = _group.NONE_GROUP
        self.__permissions: List[Permission] = []

    @property
    def user(self) -> str:
        return self.__user

    @user.setter
    def user(self, user: str) -> None:
        self.__user = str(user) if user else _user.NONE_USER
        if user and user != _user.NONE_USER:
            self.group = _group.NONE_GROUP

    @property
    def group(self) -> str:
        return self.__group

    @group.setter
    def group(self, group: str) -> None:
        self.__group = str(group) if group else _group.NONE_GROUP
        if group and group != _group.NONE_GROUP:
            self.user = _user.NONE_USER

    @property
    def basis(self) -> PermissionBasis:
        return PermissionBasis.GROUP if self.group != _group.NONE_GROUP else PermissionBasis.USER

    @property
    def permissions(self) -> List[Permission]:
        return list(self.__permissions)

    @permissions.setter
    def permissions(self, perms: List[Permission]):
        if perms is None:
            self.__permissions = []
        else:
            perms_ = [p if isinstance(p, Permission) else Permission[str(p)] for p in perms]
            self.__permissions = perms_

    def add_permission(self, perm: Permission):
        if not isinstance(perm, Permission):
            raise TypeError('perm must be a Permission')
        self.__permissions.append(perm)

    def remove_permission(self, perm: Permission):
        self.__permissions.remove(perm)

    async def applies_to(self, context: PermissionContext) -> bool:
        basis = self.basis
        return (basis is PermissionBasis.USER and self.user in (context.sub, ALL_USERS)) or \
            (basis is PermissionBasis.GROUP and self.group in await context.get_groups())

    async def get_applicable_permissions(self, context: PermissionContext) -> AsyncIterator[Permission]:
        if await self.applies_to(context):
            for perm in self.permissions:
                yield perm


class InviteImpl(AbstractPermissionAssignment, Invite):
    """
    Implementation of an invite.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__accepted = False

    @property
    def accepted(self) -> bool:
        return self.__accepted

    @accepted.setter
    def accepted(self, accepted: bool) -> None:
        if accepted is None:
            self.__accepted = False
        elif isinstance(accepted, bool):
            self.__accepted = accepted
        else:
            self.__accepted = parse_bool(accepted)  # type: ignore

    @property
    def type_display_name(self) -> str:
        return 'Invite'


class ShareImpl(AbstractPermissionAssignment, Share):
    """
    Implementation of a share.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__invite: Invite | None = None

    @property
    def invite(self) -> Invite | None:
        return self.__invite

    @invite.setter
    def invite(self, invite: Invite | None) -> None:
        if invite is not None and not isinstance(invite, Invite):
            raise TypeError('invite not an Invite')
        parent = self.get_parent_object()
        if parent is not None:
            if self.__invite is not None:
                parent.remove_invite(self.__invite)
            if invite is not None:
                invite._set_parent_object(parent)
                parent.add_invite(invite)
        self.__invite = invite

    @property
    def type_display_name(self) -> str:
        return 'Share'

    def _set_parent_object(self, obj: DesktopObject | None):
        super()._set_parent_object(obj)
        invite = self.invite
        if obj is not None and invite is not None:
            invite._set_parent_object(obj)
            obj.add_invite(invite)


class Tag(AbstractMemberObject):
    """
    Tags are essentially key value pairs
    """

    def __init__(self) -> None:
        super().__init__()
        self.__key: str | None = None
        self.__value: str | None = None

    @property
    def key(self) -> str | None:
        return self.__key

    @key.setter
    def key(self, key: str | None) -> None:
        self.__key = str(key) if key is not None else key

    @property
    def value(self) -> str | None:
        return self.__value

    @value.setter
    def value(self, value: str | None):
        self.__value = str(value) if value is not None else value

    @property
    def type_display_name(self) -> str:
        return 'Tag'


class AbstractDesktopObject(AbstractHEAObject, DesktopObject, abc.ABC):
    """
    Abstract base class representing HEA desktop objects. Desktop objects have permissions, with those permissions
    represented by owned objects implementing the MemberObject interface. Other attributes may also employ owned
    objects.

    Desktop objects implement no capability to check the current user when getting and setting owned objects, and
    different users may only have access to a subset of its owned objects. Similarly, owned objects have no knowledge of
    permissions at all. It is imperative that users gain access to desktop objects by calling an appropriate HEA
    microservice as themselves, which will filter the owned objects that are returned according to their permissions.
    """

    @abc.abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.__id: Optional[str] = None
        self.__source: Optional[str] = None
        self.__source_detail: Optional[str] = None
        self.__name: Optional[str] = None
        self.__description: Optional[str] = None
        self.__owner = _user.NONE_USER
        self.__created: Optional[date] = None  # The date when the object was created
        self.__modified: Optional[date] = None  # The date when the object was last modified
        self.__invites: list[Invite] = []
        self.__user_shares: list[Share] = []
        self.__group_shares: list[Share] = []
        self.__derived_by: str | None = None
        self.__derived_from: list[str] = []

    @property
    def id(self) -> Optional[str]:
        return self.__id

    @id.setter
    def id(self, id_: Optional[str]) -> None:
        if id_ == '':
            raise ValueError('id may not be the empty string')
        self.__id = str(id_) if id_ is not None else None

    @property
    def instance_id(self) -> str | None:
        return f'{self.type}^{self.id}' if self.id is not None else None

    @property
    def source(self) -> Optional[str]:
        return self.__source

    @source.setter
    def source(self, source: Optional[str]) -> None:
        self.__source = str(source) if source is not None else None

    @property
    def source_detail(self) -> Optional[str]:
        return self.__source_detail

    @source_detail.setter
    def source_detail(self, source_detail: Optional[str]) -> None:
        self.__source_detail = str(source_detail) if source_detail is not None else None

    @property
    def name(self) -> Optional[str]:
        return self.__name

    @name.setter
    def name(self, name: Optional[str]) -> None:
        if name == '':
            raise ValueError('name may not be the empty string')
        self.__name = str(name) if name is not None else None

    @property
    def display_name(self) -> str:
        try:
            return self.__display_name
        except:
            return self.__default_display_name()

    @display_name.setter
    def display_name(self, display_name: str) -> None:
        if display_name is not None:
            self.__display_name = str(display_name)
        elif self.name is not None:
            self.__display_name = self.name
        else:
            self.__display_name = self.__default_display_name()

    @property
    def description(self) -> Optional[str]:
        return self.__description

    @description.setter
    def description(self, description: Optional[str]) -> None:
        self.__description = str(description) if description is not None else None

    @property
    def owner(self) -> str:
        return self.__owner

    @owner.setter
    def owner(self, owner: str) -> None:
        self.__owner = str(owner) if owner is not None else _user.NONE_USER

    @property
    def created(self) -> date | None:
        return self.__created

    @created.setter
    def created(self, value: date | None) -> None:
        self.__created = to_date_or_datetime(value)

    @property
    def modified(self) -> Optional[date]:
        return self.__modified

    @modified.setter
    def modified(self, value: date | None) -> None:
        self.__modified = to_date_or_datetime(value)

    @property
    def derived_by(self) -> Optional[str]:
        return self.__derived_by

    @derived_by.setter
    def derived_by(self, derived_by: Optional[str]) -> None:
        self.__derived_by = str(derived_by) if derived_by is not None else None

    @property
    def derived_from(self) -> list[str]:
        return list(self.__derived_from)

    @derived_from.setter
    def derived_from(self, derived_from: list[str]) -> None:
        if derived_from is None:
            self.__derived_from = []
        else:
            self.__derived_from = [str(i) for i in derived_from]

    @property
    def super_admin_default_permissions(self) -> list[Permission]:
        """
        Returns the default permissions that the super admin has for this object. It always returns no permissions.
        """
        return []

    @property
    def invites(self) -> list[Invite]:
        """
        The Invite objects representing the users who have been invited to access this object. Cannot be None.
        """
        return list(self.__invites)

    @invites.setter
    def invites(self, invites: list[Invite]) -> None:
        if invites is None:
            for old_invite in self.__invites:
                old_invite._set_parent_object(None)
            self.__invites.clear()
        elif isinstance(invites, Invite):
            invites._set_parent_object(self)
            self.__invites.clear()
            self.__invites.append(invites)
        else:
            if not all(isinstance(s, Invite) for s in invites):
                raise KeyError('invites can only contain Invite objects')
            for old_invite in self.__invites:
                old_invite._set_parent_object(None)
            self.__invites.clear()
            for new_invite in invites:
                if new_invite not in self.__invites:
                    new_invite._set_parent_object(self)
                    self.__invites.append(new_invite)

    def add_invite(self, invite: Invite):
        if not isinstance(invite, Invite):
            raise TypeError('invite must be a Invite')
        if invite not in self.__invites:
            invite._set_parent_object(self)
            self.__invites.append(invite)

    def remove_invite(self, invite: Invite):
        try:
            self.__invites.remove(invite)
        except ValueError:
            return
        invite._set_parent_object(None)

    @final
    @property
    def shares(self) -> list[Share]:
        """
        A list of Share objects representing all user and group permissions assigned to this desktop object. The shares
        attribute, in combination with the owner attribute, may reflect all permissions for all users and groups, or
        they may only reflect permissions of the user requesting the desktop object.
        """
        return list(itertools.chain(self.user_shares, self.group_shares))

    @property
    def user_shares(self) -> list[Share]:
        """
        A list of Share objects representing all user permissions assigned to this desktop object. If set to
        None, it will be set to the default value, the empty list. Duplicate shares will be ignored. The shares
        attribute, in combination with the owner attribute, may reflect all permissions for all users, or they may only
        reflect permissions of the user requesting the desktop object. In the latter case, the shares attribute must be
        read-only. When overriding this attribute, you must override the setter and getter, as well as the
        add_user_share and remove_user_share methods.
        """
        return list(self.__user_shares)

    @user_shares.setter
    def user_shares(self, shares: list[Share]) -> None:
        if shares is None:
            for old_share in self.__user_shares:
                old_share._set_parent_object(None)
            self.__user_shares.clear()
        elif isinstance(shares, Share):
            if shares.basis != PermissionBasis.USER:
                raise ValueError('shares must be a Share with basis USER')
            shares._set_parent_object(self)
            self.__user_shares.clear()
            self.__user_shares.append(shares)
        else:
            if not all(isinstance(s, Share) for s in shares):
                raise TypeError("shares can only contain Share objects")
            if not all(s.basis == PermissionBasis.USER for s in shares):
                raise ValueError('shares must have basis USER')
            for old_share in self.__user_shares:
                old_share._set_parent_object(None)
            self.__user_shares.clear()
            for new_share in shares:
                if new_share not in self.__user_shares:
                    new_share._set_parent_object(self)
                    self.__user_shares.append(new_share)

    def add_user_share(self, share: Share):
        """
        Adds a user share to the desktop object. Attempting to add a share that is already in this desktop object's
        user shares list or is not a user share will be ignored. When overriding this method, you must also override
        the remove_user_share method and the user_share attribute.

        :param share: a Share (required).
        """
        if not isinstance(share, Share):
            raise TypeError(f'share must be a Share but was {type(share)}')
        if share.basis != PermissionBasis.USER:
            raise ValueError(f'share must have basis USER but has basis {share.basis}')
        if share not in self.__user_shares:
            share._set_parent_object(self)
            self.__user_shares.append(share)

    def remove_user_share(self, share: Share):
        """Removes a user share from the desktop object. Shares that are not in this desktop object's user shares list
        are ignored. When overriding this method, you must also override the add_user_share method and the
        user_share attribute.

        :param share: a Share (required).
        """
        try:
            self.__user_shares.remove(share)
            share._set_parent_object(None)
        except ValueError:
            return

    @property
    def group_shares(self) -> list[Share]:
        """
        A list of Share objects representing all group permissions assigned to this desktop object. If set to
        None, it will be set to the default value, the empty list. Duplicate shares will be ignored. The shares
        attribute, in combination with the owner attribute, may reflect all permissions for all groups, or they may
        only reflect permissions of the group membership of the user requesting the desktop object. In the latter case,
        the shares attribute must be read-only. When overriding this attribute, you must override the setter and
        getter, as well as the add_group_share and remove_group_share methods.
        """
        return list(self.__group_shares)

    @group_shares.setter
    def group_shares(self, shares: list[Share]) -> None:
        if shares is None:
            for old_share in self.__group_shares:
                old_share._set_parent_object(None)
            self.__group_shares.clear()
        elif isinstance(shares, Share):
            if shares.basis != PermissionBasis.GROUP:
                raise ValueError('shares must be a Share with basis GROUP')
            shares._set_parent_object(self)
            self.__group_shares.clear()
            self.__group_shares.append(shares)
        else:
            if not all(isinstance(s, Share) for s in shares):
                raise TypeError("shares can only contain Share objects")
            if not all(s.basis == PermissionBasis.GROUP for s in shares):
                raise ValueError('shares must have basis GROUP')
            for old_share in self.__group_shares:
                old_share._set_parent_object(None)
            self.__group_shares.clear()
            for new_share in shares:
                if new_share not in self.__group_shares:
                    new_share._set_parent_object(self)
                    self.__group_shares.append(new_share)

    def add_group_share(self, share: Share):
        """
        Adds a group share to the desktop object. Attempting to add a share that is already in this desktop object's
        group shares list or is not a group share will be ignored. When overriding this method, you must also override
        the remove_group_share method and the group_share attribute.

        :param share: a Share (required).
        """
        if not isinstance(share, Share):
            raise TypeError(f'share must be a Share but was {type(share)}')
        if share.basis != PermissionBasis.GROUP:
            raise ValueError(f'share must have basis GROUP but has basis {share.basis}')
        if share not in self.__group_shares:
            share._set_parent_object(self)
            self.__group_shares.append(share)

    def remove_group_share(self, share: Share):
        """
        Removes a group share from the desktop object. Shares that are not in this desktop object's group shares list
        are ignored. When overriding this method, you must also override the add_group_share method and the
        group_share attribute.

        :param share: a Share (required).
        """
        try:
            self.__group_shares.remove(share)
            share._set_parent_object(None)
        except ValueError:
            return

    def add_share(self, share: Share):
        """
        Adds a share to the desktop object. Attempting to add a share that is not already in this desktop object's
        shares list will be ignored.

        :param share: a Share (required).
        """
        if share.basis == PermissionBasis.USER:
            self.add_user_share(share)
        else:
            self.add_group_share(share)

    def remove_share(self, share: Share):
        """
        Removes a share from the desktop object. Attempting to remove a share that is not already in this desktop
        object's shares list will be ignored.

        :param share: a Share (required).
        """
        if share.basis == PermissionBasis.USER:
            self.remove_user_share(share)
        else:
            self.remove_group_share(share)

    @property
    def dynamic_permission_supported(self) -> bool:
        return False

    def dynamic_permission(self, sub: str) -> List[Permission]:
        """
        Default implementation that returns an empty list, signifying no additional permissions.

        :param sub: the user id.
        :return: an empty list.
        """
        return []

    def dynamic_attribute_permission(self, attribute: str, sub: str) -> list[Permission] | None:
        """
        Restricts permissions for attributes that should always be read-only for users who are not the object's owner,
        are not a super admin, and do not have a user share nor a group share.

        :param attribute: the attribute to check.
        :param sub: the user id to check.
        :return: the attribute's permissions, or None if this method does not know about the requested attribute's
        permissions.
        """
        match attribute:
            case 'owner' | 'invites' | 'user_shares' | 'group_shares':
                return [Permission.VIEWER]
            case _:
                return None

    async def get_permissions(self, context: PermissionContext) -> list[Permission]:
        return await context.get_permissions(self)

    async def get_permissions_as_share(self, context: PermissionContext) -> Share:
        return await context.get_permissions_as_share(self)

    async def has_permissions(self, perms: Sequence[Permission] | PermissionGroup, context: PermissionContext) -> bool:
        return await context.has_permissions(self, perms)

    async def is_read_only(self, context: PermissionContext) -> bool:
        return are_permissions_read_only(await self.get_permissions(context))

    async def get_attribute_permissions(self, attr: str, context: PermissionContext) -> list[Permission]:
        return await context.get_attribute_permissions(self, attr)

    async def get_all_attribute_permissions(self, context: PermissionContext) -> dict[str, list[Permission]]:
        return {attr: await self.get_attribute_permissions(attr, context) for attr in self.get_attributes()}

    async def has_attribute_permissions(self, attr: str, perms: Sequence[Permission] | PermissionGroup, context: PermissionContext) -> bool:
        return await context.has_attribute_permissions(self, attr, perms)

    async def is_attribute_read_only(self, attr: str, context: PermissionContext) -> bool:
        return are_permissions_read_only(await self.get_attribute_permissions(attr, context))

    @classmethod
    def get_owner_permissions(cls) -> list[Permission]:
        return list(Permission.non_creator_permissions())

    @classmethod
    def get_subclasses(cls) -> Iterator[type['AbstractDesktopObject']]:
        for subclass in cls.__subclasses__():
            yield from subclass.get_subclasses()
            yield subclass

    @classmethod
    async def can_create(cls: type[DesktopObjectTypeVar], context: PermissionContext) -> bool:
        return await context.can_create(cls)

    def __default_display_name(self):
        return 'Untitled ' + self.type_display_name

    def __str__(self) -> str:
        """
        Returns the object's display name.
        :return: the display name.
        """
        return self.display_name


def are_permissions_read_only(permissions: Sequence[Permission | str]) -> bool:
    """
    Returns whether the given permissions are read-only (contains VIEWER permissions but not EDITOR nor COOWNER).

    :param permissions: a sequence of Permission objects or strings representing permissions.
    :return: True if the permissions are read-only, False otherwise.
    """
    permissions_ = [perm if isinstance(perm, Permission) else Permission[perm] for perm in permissions]
    return Permission.VIEWER in permissions_ and (Permission.EDITOR not in permissions_ and Permission.COOWNER not in permissions_)


class Version(AbstractDesktopObject):
    """
    Represents version metadata for a desktop object. Versioned desktop objects (that implement the version attribute)
    may implement an API for getting version metadata represented by instances of this class. If such an API is
    provided, it must return a Version metadata object whose id equals the value of the desktop object's version
    attribute. The API may also return additional Version objects representing older versions of the object.

    Microservices may implement subclasses of Version if their versions have extra attributes or their attributes need
    custom validation logic.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__current = False
        self.__version_of_id: str | None = None

    @property
    def current(self) -> bool:
        """Whether this is the current version of the desktop object. The default value is False."""
        return self.__current

    @current.setter
    def current(self, current: bool):
        if current is None:
            self.__current = False
        elif isinstance(current, bool):
            self.__current = current
        else:
            self.__current = parse_bool(current)

    @property
    def version_of_id(self) -> str | None:
        return self.__version_of_id

    @version_of_id.setter
    def version_of_id(self, version_of_id: str | None):
        self.__version_of_id = str(version_of_id) if version_of_id is not None else None


class AbstractVersionedDesktopObject(AbstractDesktopObject, VersionedDesktopObject, abc.ABC):
    """
    Base class for versioned desktop objects.
    """

    @abc.abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.__version: str | None = None

    @property
    def version(self) -> str | None:
        return self.__version

    @version.setter
    def version(self, version: str | None):
        self.__version = str(version) if version is not None else None


class Alias(abc.ABC):
    """
    Placeholder mixin for implementing aliases similar to those in MacOS and Windows.
    """
    pass


class View(abc.ABC):
    """
    View mixin. Views are desktop objects that are automatically managed alternative representations of some other
    desktop object. Acting on a view also acts on the other desktop object, and vice-versa. A desktop object can have
    multiple views served by different endpoints, all of which synchronize with the corresponding desktop object.
    Create a view class by extending both heaobject.root.DesktopObject (or a subclass) and this class. In addition to
    the attributes provided by this mixin, microservices are expected to populate a view's attributes from those of the
    desktop object for all attributes that overlap. Furthermore, submitting a view object to a PUT, POST, or DELETE
    endpoint must also update the corresponding desktop object. A client must be able to work with views and their
    corresponding desktop objects interchangeably, and synchronization between the two must be immediate such that a
    workflow must be able to submit a change to a view and subsequently request the corresponding desktop object,
    and the changes in the view must reflect in the desktop object.

    A View's type_display_name attribute is expected to be equal to the type_display_name of the other desktop object
    it represents.

    Views are different from MacOS or Windows aliases. While aliases can be modified and deleted without affecting
    the object that they point to, and changes to an object may or may not affect its aliases, changes to HEA views
    always change the corresponding desktop object and vice-versa. HEA defines an heaobject.root.Alias mixin as a
    placeholder for supporting desktop objects in the future that have similar properties to MacOS and Windows aliases.
    """

    @property
    def actual_object_type_name(self) -> str | None:
        """The actual object's type name."""
        try:
            return self.__actual_object_type_name
        except AttributeError:
            self.__actual_object_type_name: str | None = None
            return self.__actual_object_type_name

    @actual_object_type_name.setter
    def actual_object_type_name(self, actual_object_type_name: str | None) -> None:
        self.__actual_object_type_name = str(actual_object_type_name) if actual_object_type_name is not None else None

    @property
    def actual_object_id(self) -> str | None:
        """The actual object's id."""
        try:
            return self.__actual_object_id
        except AttributeError:
            self.__actual_object_id: str | None = None
            return self.__actual_object_id

    @actual_object_id.setter
    def actual_object_id(self, actual_object_id: str | None) -> None:
        self.__actual_object_id = str(actual_object_id) if actual_object_id is not None else None

    @property
    def actual_object_uri(self) -> str | None:
        """The actual object's URL, as a relative URL without a leading slash to an API gateway for accessing the
        object."""
        try:
            return self.__actual_object_uri
        except AttributeError:
            self.__actual_object_uri: str | None = None
            return self.__actual_object_uri

    @actual_object_uri.setter
    def actual_object_uri(self, actual_object_uri: str | None) -> None:
        self.__actual_object_uri = str(actual_object_uri) if actual_object_uri is not None else None


class HasSize:
    """
    Size mixin for use in desktop objects with content.
    """
    @property
    def size(self) -> Optional[int]:
        """Size of the item in bytes"""
        try:
            return self.__size
        except AttributeError:
            return None

    @size.setter
    def size(self, size: Optional[int]) -> None:
        """The size of the desktop object's content in bytes."""
        self.__size = int(size) if size is not None else None

    @property
    def human_readable_size(self) -> str | None:
        """The size of the desktop object's content in human readable form."""
        return naturalsize(self.size) if self.size is not None else None


def is_primitive(obj: Any) -> bool:
    """
    Returns whether the argument is an instance of a HEA primitive type (int, float, str, bool, Enum, or NoneType).
    :return: True or False.
    """
    return isinstance(obj, PRIMITIVE_ATTRIBUTE_TYPES)


def is_primitive_list(obj: Any) -> bool:
    """
    Returns whether the argument is a list of HEA primitive types. Will return True if passed an empty list.
    :return: True or False.
    """
    return isinstance(obj, list) and all(is_primitive(elt) for elt in obj)


def is_member_object(obj: Any) -> bool:
    """
    Returns whether the argument is a MemberObject.
    :return: True or False.
    """
    return isinstance(obj, MemberObject)


def is_member_object_list(obj: Any) -> bool:
    """
    Returns whether the argument is an iterable of MemberObjects. Will return False if passed an empty list.
    :return: True or False.
    """
    return isinstance(obj, list) and len(obj) > 0 and all(isinstance(elt, MemberObject) for elt in obj)


def is_desktop_object_dict(obj: Any) -> bool:
    """
    Returns whether the argument is a desktop object dict, defined as a dict with a type key, and the type name is
    that of a subclass of DesktopObject.

    :param obj: any object.
    :return: True or False.
    """
    return isinstance(obj, dict) and 'type' in obj and is_desktop_object_type(obj['type'])


def is_member_object_dict(obj: Any) -> bool:
    """
    Returns whether the argument is a MemberObject dict, defined as a dict with a type key, and the type name is
    that of a subclass of MemberObject.

    :param obj: any object.
    :return: True or False.
    """
    return isinstance(obj, dict) and 'type' in obj and not is_desktop_object_type(obj['type'])


def is_heaobject_dict(obj: Any) -> bool:
    """
    Returns whether the argument is an HEAObject dict, defined as a dict with a type key.

    :param obj: any object.
    :return: True or False.
    """
    return isinstance(obj, dict) and 'type' in obj


def is_heaobject_dict_list(obj: Any) -> bool:
    """
    Returns whether the argument is a list of HEAObject dicts. Will return False if passed an empty list.

    :param obj: any object.
    :return: True or False.
    """
    return isinstance(obj, list) and len(obj) > 0 and all(is_heaobject_dict(elt) for elt in obj)


@overload
def type_for_name(name: str) -> type[HEAObject]:
    ...


@overload
def type_for_name(name: str, *, type_: type[HEAObjectTypeVar]) -> type[HEAObjectTypeVar]:
    ...


@overload
def type_for_name(name: str, *, type_: None) -> type[HEAObject]:
    ...


def type_for_name(name: str, *, type_: type[HEAObject] | None = None) -> type[HEAObject]:
    """
    Returns the HEAObject type for the given string.

    :param name: a type string.
    :param type_: the type of HEAObject that is expected. This may be an abstract type.
    :return: a HEAObject type.
    :raises TypeError: if the supplied type name is unexpected.
    """
    result = type_name_to_type(name)
    if issubclass(result, type_ or HEAObject):
        return result
    else:
        raise TypeError(f'{name} is not a subclass of {type_}')


def is_heaobject_type(name: str, type_: type[HEAObject] | tuple[type[HEAObject]] | None = HEAObject) -> bool:
    """
    Returns whether the supplied string is the name of an HEAObject type.

    :param name: a string.
    :param type_: optional upper bound for the type. The name must have a subclass relationship to the given.
    :return: True if the string is the name of an HEAObject type, or False if not.
    """
    if type_ is None:
        upper_bound_: type[HEAObject] | tuple[type[HEAObject]] = HEAObject
    else:
        upper_bound_ = type_
    try:
        return issubclass(type_for_name(name), upper_bound_)
    except TypeError:
        return False


@overload
def desktop_object_type_for_name(name: str) -> type[DesktopObject]:
    ...


@overload
def desktop_object_type_for_name(name: str, *, type_: type[DesktopObjectTypeVar]) -> type[DesktopObjectTypeVar]:
    ...


@overload
def desktop_object_type_for_name(name: str, *, type_: None) -> type[DesktopObject]:
    ...


def desktop_object_type_for_name(name: str, *, type_: type[DesktopObject] | None = None) -> type[DesktopObject]:
    """
    Returns the desktop object type for the given type name.

    :param name: a type string.
    :param type_: the desktop object type to expect. It may be an abstract type. It must have a subclass relationship
    to the given type_ or must be the same class.
    :return: a DesktopObject type.
    :raises TypeError: if the supplied type name is unexpected.
    """
    result = type_name_to_type(name, type_=type_)
    if issubclass(result, type_ or DesktopObject):
        return result
    else:
        raise TypeError(f'{name} is not a subclass of {type_}')



def is_desktop_object_type(name: str, type_: type[DesktopObject] | tuple[type[DesktopObject]] | None = DesktopObject) -> bool:
    """
    Returns whether the supplied string is the name of an HEA desktop object type.

    :param name: a string.
    :param upper_bound: optional upper bound for the type. The name must have a subclass relationship to the given.
    :return: True if the string is the name of an HEA desktop object type, or False if not.
    """
    if type_ is None:
        upper_bound_: type[DesktopObject] | tuple[type[DesktopObject]] = DesktopObject
    else:
        upper_bound_ = type_
    try:
        return issubclass(desktop_object_type_for_name(name), upper_bound_)
    except TypeError:
        return False


@overload
def from_dict(d: HEAObjectDict | HEAObjectDictIncludesEncrypted, *, encryption: Encryption) -> HEAObject:
    ...

@overload
def from_dict(d: HEAObjectDict, *, encryption: None) -> HEAObject:
    ...

@overload
def from_dict(d: HEAObjectDict) -> HEAObject:
    ...

@overload
def from_dict(d: HEAObjectDict | HEAObjectDictIncludesEncrypted, *, type_: type[HEAObjectTypeVar], encryption: Encryption) -> HEAObjectTypeVar:
    ...

@overload
def from_dict(d: HEAObjectDict, *, type_: type[HEAObjectTypeVar], encryption: None) -> HEAObjectTypeVar:
    ...

@overload
def from_dict(d: HEAObjectDict, *, type_: type[HEAObjectTypeVar]) -> HEAObjectTypeVar:
    ...

@overload
def from_dict(d: HEAObjectDict | HEAObjectDictIncludesEncrypted, *, type_: None, encryption: Encryption) -> HEAObject:
    ...

@overload
def from_dict(d: HEAObjectDict, *, type_: None, encryption: None) -> HEAObject:
    ...

@overload
def from_dict(d: HEAObjectDict, *, type_: None) -> HEAObject:
    ...

def from_dict(d: HEAObjectDict | HEAObjectDictIncludesEncrypted, *, type_: type[HEAObject] | None = None,
              encryption: Encryption | None = None) -> HEAObject:
    """
    Creates a HEA object from the given dict.

    :param d: a dict. It must have, at minimum, a type key with the type name of the HEA object to create. It must
    additionally have key-value pairs for any mandatory attributes of the HEA object.
    :param type_: the type of HEA object to create. If None, the type will be inferred from the dict's type key. If
    provided, the type_ must match that of the dict's type key.
    :param encryption: an Encryption object to use for decrypting attribute values, or None for no decryption.
    :return: a HEAObject.
    :raises ValueError: if the input DesktopObjectDict is missing a type key.
    :raises TypeError: if the input DesktopObjectDict's type value is not a string.
    :raises DeserializeException: if the input DesktopObjectDict could not otherwise be read.
    """
    type_name = d.get('type', None)
    if not type_name:
        raise ValueError('type key is required')
    if not isinstance(type_name, str):
        raise TypeError(f'type is {type(type_name)} but must be a str')
    if type_ is not None and type_name != type_.get_type_name():
        raise TypeError(f'type name {type_name} does not match expected type {type_.get_type_name()}')
    obj = type_for_name(type_name)()
    obj.from_dict(d, encryption=encryption) if encryption else obj.from_dict(cast(HEAObjectDict, d))
    return obj


def from_json(o: str | bytes, type_: type[HEAObject] | None = None) -> HEAObject:
    """
    Creates a HEA object from the given JSON document.

    :param o: the JSON document. It must have, at minimum, a type property with the type name of the HEA object to
    create. It must additionally have properties for any mandatory attributes of the HEA object.
    :param type_: the type of HEA object to create. If None, the type will be inferred from the dict's type key. If
    provided, the type_ must match that of the dict's type key.
    :return: a HEAObject.
    :raises ValueError: if the input DesktopObjectDict is missing a type key.
    :raises TypeError: if the input DesktopObjectDict's type value is not a string.
    :raises heaobject.error.DeserializeException: if the input DesktopObjectDict could not otherwise be read.
    :raises orjson.JSONDecodeError: if the input is not valid JSON.
    """
    return from_dict(json_loads(o), type_=type_)


@overload
def to_dict(obj: DesktopObject) -> DesktopObjectDict:
    ...

@overload
def to_dict(obj: DesktopObject, encryption: Encryption) -> DesktopObjectDictIncludesEncrypted:
    ...

@overload
def to_dict(obj: DesktopObject, encryption: None) -> DesktopObjectDict:
    ...

@overload
def to_dict(obj: MemberObject) -> MemberObjectDict:
    ...

@overload
def to_dict(obj: MemberObject, encryption: Encryption) -> MemberObjectDictIncludesEncrypted:
    ...

@overload
def to_dict(obj: MemberObject, encryption: None) -> MemberObjectDict:
    ...

@overload
def to_dict(obj: HEAObject) -> HEAObjectDict:
    ...

@overload
def to_dict(obj: HEAObject, encryption: Encryption) -> HEAObjectDictIncludesEncrypted:
    ...

@overload
def to_dict(obj: HEAObject, encryption: None) -> HEAObjectDict:
    ...

def to_dict(obj: HEAObject, encryption: Encryption | None = None) -> HEAObjectDict | HEAObjectDictIncludesEncrypted:
    """
    Returns a dict containing this object's data attributes as defined by the get_attributes() method.

    :param obj: a HEAObject (required).
    :param encryption: an Encryption object to use for encrypting attribute values, or None for no encryption.
    :return: a dict of attribute names to attribute values.
    """
    return obj.to_dict(encryption=encryption)


def to_json(obj: HEAObject) -> str:
    """
    Returns a JSON document containing this object's data attributes as defined by the get_attributes() method.

    :param obj: a HEAObject (required).
    :return: a JSON document as a str.
    """
    return obj.to_json()


@overload
def desktop_object_from_dict(d: DesktopObjectDict) -> DesktopObject: ...

@overload
def desktop_object_from_dict(d: DesktopObjectDict | DesktopObjectDictIncludesEncrypted, *, encryption: Encryption) -> DesktopObject: ...

@overload
def desktop_object_from_dict(d: DesktopObjectDict, *, encryption: None) -> DesktopObject: ...

@overload
def desktop_object_from_dict(d: DesktopObjectDict, *, type_: type[DesktopObjectTypeVar]) -> DesktopObjectTypeVar: ...

@overload
def desktop_object_from_dict(d: DesktopObjectDict | DesktopObjectDictIncludesEncrypted, *, type_: type[DesktopObjectTypeVar],
                             encryption: Encryption) -> DesktopObjectTypeVar: ...

@overload
def desktop_object_from_dict(d: DesktopObjectDict, *, type_: type[DesktopObjectTypeVar],
                             encryption: None) -> DesktopObjectTypeVar: ...

@overload
def desktop_object_from_dict(d: DesktopObjectDict, *, type_: None) -> DesktopObject: ...

@overload
def desktop_object_from_dict(d: DesktopObjectDict | DesktopObjectDictIncludesEncrypted, *, type_: type[DesktopObject] | None,
                             encryption: Encryption | None) -> DesktopObject: ...


def desktop_object_from_dict(d: DesktopObjectDict | DesktopObjectDictIncludesEncrypted, *, type_: type[DesktopObject] | None = None,
                             encryption: Encryption | None = None) -> DesktopObject:
    """
    Creates a desktop object from the given dict.

    :param d: a dict. It must have, at minimum, a type key with the type name of the desktop object to create. It must
    additionally have key-value pairs for any mandatory attributes of the desktop object.
    :param type_: the type of desktop object to create. If None, the type will be inferred from the dict's type key.
    If provided, the type_ must match that of the dict's type key.
    :param encryption: an Encryption object to use for decrypting attribute values, or None for no decryption.
    :return: a desktop object.
    :raises ValueError: if the input DesktopObjectDict is missing a type key.
    :raises TypeError: if the input DesktopObjectDict's type value is not a string or if the desktop object dict has an
    incompatible type with the given type_.
    :raises heaobject.error.DeserializeException: if the input DesktopObjectDict could not otherwise be read.
    """
    type_name = d.get('type', None)
    if not type_name:
        raise ValueError('type key is required')
    if not isinstance(type_name, str):
        raise TypeError(f'type is {type(type_name).__name__} but must be a str')
    if type_:
        obj: DesktopObject = desktop_object_type_for_name(type_name, type_=type_)()
    else:
        obj = cast(DesktopObject, desktop_object_type_for_name(type_name)())
    obj.from_dict(d, encryption=encryption) if encryption else obj.from_dict(cast(HEAObjectDict, d))
    return obj


def desktop_object_from_json(o: str | bytes, type_: type[DesktopObject] | None = None) -> DesktopObject:
    """
    Creates a desktop object from the given JSON document.

    :param o: the JSON document. It must have, at minimum, a type property with the type name of the desktop object to
    create. It must additionally have properties for any mandatory attributes of the desktop object.
    :param type_: the type of desktop object to create. If None, the type will be inferred from the dict's type key.
    If provided, the type_ must match that of the dict's type key.
    :return: a DesktopObject.
    :raises ValueError: if the input DesktopObjectDict is missing a type key.
    :raises TypeError: if the input DesktopObjectDict's type value is not a string.
    :raises heaobject.error.DeserializeException: if the input DesktopObjectDict could not otherwise be read.
    :raises orjson.JSONDecodeError: if the input is not valid JSON.
    """
    return desktop_object_from_dict(json_loads(o), type_=type_)


@overload
def copy_heaobject_dict_with(d: DesktopObjectDict, changes: Mapping[str, DesktopObjectDictValue] | None) -> DesktopObjectDict:
    ...

@overload
def copy_heaobject_dict_with(d: MemberObjectDict, changes: Mapping[str, MemberObjectDictValue] | None) -> MemberObjectDict:
    ...

@overload
def copy_heaobject_dict_with(d: HEAObjectDict, changes: Mapping[str, HEAObjectDictValue] | None) -> HEAObjectDict:
    ...

def copy_heaobject_dict_with(d: HEAObjectDict, changes: Mapping[str, HEAObjectDictValue] | None) -> HEAObjectDict:
    """
    Shallow copies the given dictionary and updates it with the given changes.

    :param d: The HEA object dictionary that will be changed (required).
    :param changes: The changes being made, expressed as a mapping.
    :return: A shallow copy of the given dictionary with the given changes.
    """
    if changes and is_member_object_dict(d) and any((is_member_object_dict(v) or (isinstance(v, Sequence) and any(is_member_object_dict(vl) for vl in v)) for v in changes.values())):
        raise TypeError('d is a MemberObjectDict but member object changes requested')
    copied_dict = dict[str, HEAObjectDictValue](d)
    if changes:
        copied_dict.update(changes)
    return copied_dict


@overload
def copy_heaobject_dict_with_deletions(d: DesktopObjectDict, deletions: Iterable[str] | None) -> DesktopObjectDict:
    ...

@overload
def copy_heaobject_dict_with_deletions(d: MemberObjectDict, deletions: Iterable[str] | None) -> MemberObjectDict:
    ...

@overload
def copy_heaobject_dict_with_deletions(d: HEAObjectDict, deletions: Iterable[str] | None) -> HEAObjectDict:
    ...

def copy_heaobject_dict_with_deletions(d: HEAObjectDict, deletions: Iterable[str] | None) -> HEAObjectDict:
    """
    Shallow copies the given dictionary and updates it with the given deletions. It does no validation of whether the
    provided dictionary is a HEAObjectDict.

    :param d: The HEA object dictionary that will be changed (required).
    :param deletions: The deletions being made, as an iterable.
    :return: A shallow copy of the given dictionary with the given changes.
    """
    copied_dict = dict(d)
    for deletion in (deletions or []):
        if deletion in d:
            del copied_dict[deletion]
    return copied_dict


@overload
def deepcopy_heaobject_dict_with(d: DesktopObjectDict, changes: Mapping[str, DesktopObjectDictValue] | None) -> DesktopObjectDict:
    ...

@overload
def deepcopy_heaobject_dict_with(d: MemberObjectDict, changes: Mapping[str, MemberObjectDictValue] | None) -> MemberObjectDict:
    ...

@overload
def deepcopy_heaobject_dict_with(d: HEAObjectDict, changes: Mapping[str, HEAObjectDictValue] | None) -> HEAObjectDict:
    ...

def deepcopy_heaobject_dict_with(d: HEAObjectDict, changes: Mapping[str, HEAObjectDictValue] | None) -> HEAObjectDict:
    """
    Deep copies the given dictionary and updates it with the given changes.

    :param d: The HEA object dictionary that will be changed (required).
    :param changes: The changes being made, expressed as a mapping.
    :return: A deep copy of the given dictionary with the given changes.
    """
    if changes and is_member_object_dict(d) and any((is_member_object_dict(v) or (isinstance(v, Sequence) and any(is_member_object_dict(vl) for vl in v)) for v in changes.values())):
        raise TypeError('d is a MemberObjectDict but member object changes requested')
    copied_dict = dict(deepcopy(d))
    if changes:
        copied_dict.update(changes)
    return copied_dict


@overload
def deepcopy_heaobject_dict_with_deletions(d: DesktopObjectDict, deletions: Iterable[str] | None) -> DesktopObjectDict:
    ...

@overload
def deepcopy_heaobject_dict_with_deletions(d: MemberObjectDict, deletions: Iterable[str] | None) -> MemberObjectDict:
    ...

@overload
def deepcopy_heaobject_dict_with_deletions(d: HEAObjectDict, deletions: Iterable[str] | None) -> HEAObjectDict:
    ...

def deepcopy_heaobject_dict_with_deletions(d: HEAObjectDict, deletions: Iterable[str] | None) -> HEAObjectDict:
    """
    Deep copies the given dictionary and updates it with the given deletions. It does no validation of whether the
    provided dictionary is a HEAObjectDict.

    :param d: The HEA object dictionary that will be changed (required).
    :param deletions: The deletions being made, as an iterable.
    :return: A deep copy of the given dictionary with the given changes.
    """
    copied_dict = deepcopy(d)
    for deletion in (deletions or []):
        if deletion in d:
            del copied_dict[deletion]
    return copied_dict


if TYPE_CHECKING:
    _Base = DesktopObject
else:
    _Base = object


class TagsMixin(_Base):
    """
    Mixin for adding a tags attribute to a desktop object.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__tags: list[Tag] = []

    @property
    def tags(self) -> list[Tag]:
        """Returns the tags"""
        return list(self.__tags)

    @tags.setter
    def tags(self, tags: list[Tag]) -> None:
        """Sets the tags"""
        if tags is not None and type(tags) is not list:
            raise ValueError("This format is not correct for tags, type should be list")
        if not all(isinstance(tag, Tag) for tag in (tags or [])):
            raise ValueError("This format is not correct list must contain tags")
        for tag in self.__tags:
            tag._set_parent_object(None)
        self.__tags.clear()
        for tag in tags or []:
            tag._set_parent_object(self)
            self.__tags.append(tag)


class NonCreatorSuperAdminDefaultPermissionsMixin:
    """
    Mixin for adding a super_admin_default_permissions attribute to a desktop object with non-creator permissions.
    """

    @property
    def super_admin_default_permissions(self) -> list[Permission]:
        """
        The default permissions that the super admin has for this object (all permissions except CREATOR).
        """
        return list(Permission.non_creator_permissions())


def get_all_heaobject_subclasses(predicate: Callable[[type[HEAObject]], bool] | None = None) -> Iterator[type[HEAObject]]:
    """
    Returns all HEAObject subclasses.

    :return: an iterator of HEAObject subclasses.
    """
    import_all_submodules()
    def _get_all_subclasses(cls: type[HEAObject]) -> Iterator[type[HEAObject]]:
        result = {cls__ for cls__ in cls.__subclasses__()}
        for subcls in result:
            result = result.union(_get_all_subclasses(subcls))
        return iter(r for r in result if (predicate(r) if predicate else True))
    return _get_all_subclasses(HEAObject)   # type: ignore[type-abstract]
