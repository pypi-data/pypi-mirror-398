from .attribute import IdListWithBackingSetAttribute
from .decorators import attribute_metadata
from .root import AbstractDesktopObject, Share, ShareImpl, Permission, NonCreatorSuperAdminDefaultPermissionsMixin
from typing import Optional, cast
from email_validator import validate_email, EmailNotValidError  # Leave this here for other modules to use
from base64 import urlsafe_b64encode, urlsafe_b64decode
from functools import partial
from enum import Enum
from .source import HEA
from .user import NONE_USER, ALL_USERS, TEST_USER, SOURCE_USER, AWS_USER, CREDENTIALS_MANAGER_USER, is_system_user
from .group import SUPERADMIN_GROUP


class Person(NonCreatorSuperAdminDefaultPermissionsMixin, AbstractDesktopObject):
    """
    Represents a Person
    """
    group_ids = IdListWithBackingSetAttribute('The ids of the groups that this person belongs to. Duplicates and '
                                              'None ids are ignored, and the id order may not be preserved.')

    def __init__(self) -> None:
        super().__init__()
        # id is a super field
        # name is inherited in super
        self.__preferred_name: Optional[str] = None
        self.__first_name: Optional[str] = None
        self.__last_name: Optional[str] = None
        self.__title: Optional[str] = None
        self.__email: Optional[str] = None
        self.__phone_number: Optional[str] = None
        self.__display_name: str | None = None
        self.__overridden_display_name: str | None = None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def preferred_name(self) -> Optional[str]:
        """
        The Person's preferred name (Optional).
        """
        return self.__preferred_name

    @preferred_name.setter
    def preferred_name(self, preferred_name: Optional[str]) -> None:
        self.__preferred_name = str(preferred_name) if preferred_name is not None else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def first_name(self) -> Optional[str]:
        """
        The Person's first name or given name (Optional).
        """
        return self.__first_name

    @first_name.setter
    def first_name(self, first_name: Optional[str]) -> None:
        self.__first_name = str(first_name) if first_name is not None else None
        self.__update_display_name()

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def last_name(self) -> Optional[str]:
        """
          The Person's last name (Optional).
        """
        return self.__last_name

    @last_name.setter
    def last_name(self, last_name: Optional[str]) -> None:
        self.__last_name = str(last_name) if last_name is not None else None
        self.__update_display_name()

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        return self.display_name

    @property
    def title(self) -> Optional[str]:
        """
          The Person's title (Optional).
        """
        return self.__title

    @title.setter
    def title(self, title: Optional[str]) -> None:
        self.__title = str(title) if title is not None else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def email(self) -> Optional[str]:
        """
        The person's email (Optional). Must be a valid e-mail address or None.
        """
        return self.__email

    @email.setter
    def email(self, email: Optional[str]) -> None:
        self.__email = _validate_email(str(email)).normalized if email is not None else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def phone_number(self) -> Optional[str]:
        """
          The Person's phone number (Optional).
        """
        return self.__phone_number

    @phone_number.setter
    def phone_number(self, phone_number: Optional[str]) -> None:
        self.__phone_number = str(phone_number) if phone_number is not None else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def display_name(self) -> str:
        if self.__overridden_display_name is not None:
            return self.__overridden_display_name
        elif self.__display_name is not None:
            return self.__display_name
        else:
            return super().display_name

    @display_name.setter
    def display_name(self, display_name: str) -> None:
        self.__overridden_display_name = display_name

    @property
    def type_display_name(self) -> str:
        return 'Person'

    def add_group_id(self, group_id: str):
        """
        Adds a group id to the list of group ids.

        :param group_id: the group id to add.
        """
        type(self).group_ids.add(self, group_id)

    def remove_group_id(self, group_id: str):
        """
        Removes a group id from the list of group ids.

        :param group_id: the group id to remove.
        """
        type(self).group_ids.remove(self, group_id)

    @property
    def super_admin_default_permissions(self) -> list[Permission]:
        """
        The default permissions that the super admin has for this object (all permissions except CREATOR and DELETER).
        Also, super-admins only have VIEWER permission for system users.
        """
        if self.id and is_system_user(self.id):
            return [Permission.VIEWER]
        else:
            return super().super_admin_default_permissions

    def __update_display_name(self):
        fname = self.first_name if self.first_name else ""
        lname = self.last_name if self.last_name else ""
        if fname or lname:
            self.__display_name = f"{fname}{' ' if fname and lname else ''}{lname}"
        else:
            self.__display_name = None


ROLE_ENCODING = 'utf-8'


class Role(AbstractDesktopObject):
    """
    A user role, for authorization purposes. While HEA exposes user authorization information via access control lists,
    this class supports compatibility with file systems with role-based authorization like Amazon Web Services S3
    buckets. The id and name attributes are synchronized with the role attribute such that setting one automatically
    populates the others.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__role: str | None = None
        self.__display_name: str | None = None

    @property
    def id(self) -> str | None:
        """
        The role, base64-encoded using this module's encode_role() function. Setting this attribute automatically
        generates values for the name and role attributes.
        """
        return self.name

    @id.setter
    def id(self, id_: str | None):
        if id_ == '':
            raise ValueError('id cannot be the empty string')
        self.name = id_

    @property
    def name(self) -> str | None:
        """
        The role, base64-encoded using this module's encode_role() function. Setting this attribute automatically
        generates values for the id and role attributes.
        """
        role_ = self.role
        return encode_role(role_) if role_ is not None else None

    @name.setter
    def name(self, name: str | None):
        if name == '':
            raise ValueError('name cannot be the empty string')
        self.role = decode_role(name) if name is not None else None

    @property
    def role(self) -> str | None:
        """
        The role. Setting this attribute automatically generates values for the id and name attributes. Cannot be the
        empty string.
        """
        return self.__role

    @role.setter
    def role(self, role: str | None):
        if role == '':
            raise ValueError('role cannot be the empty string')
        self.__role = str(role) if role is not None else role
        if self.__display_name is None:
            self.__display_name = self.__role

    @property
    def type_display_name(self) -> str:
        return 'Role'

    @property
    def display_name(self) -> str:
        return self.__display_name if self.__display_name is not None else super().display_name

    @display_name.setter
    def display_name(self, display_name: str):
        self.__display_name = str(display_name) if display_name is not None else None

    @staticmethod
    def id_to_role(id_: str) -> str:
        """
        Converts a Role id to a role.

        :param id_: the role id.
        :return: the role.
        """
        role: Role = Role()
        role.id = id_
        return cast(str, role.role)

class GroupType(Enum):
    ADMIN = 10
    ORGANIZATION = 20

class Group(NonCreatorSuperAdminDefaultPermissionsMixin, AbstractDesktopObject):
    """
    A user group, for authorization purposes. The id and name attributes are synchronized with the group attribute such
    that setting one automatically populates the others. There is expected to be a one-to-one relationship between
    group and id. The PermissionContext class in this module supports mapping from a group to its corresponding id.
    Generally speaking, use the id attribute to create associations from a desktop object to groups.
    """

    role_ids = IdListWithBackingSetAttribute('The ids of the roles that this group has. Duplicates and None ids are '
                                             'ignored, and the id order may not be preserved.')

    def __init__(self) -> None:
        super().__init__()
        self.__group: str | None = None
        self.__display_name: str | None = None
        self.__group_type = GroupType.ADMIN

    @property
    def name(self) -> str | None:
        """
        The group, base64-encoded using this module's encode_group() function. Setting this attribute automatically
        generates values for the id and group attributes.
        """
        group_ = self.group
        return encode_group(group_) if group_ is not None else None

    @name.setter
    def name(self, name: str | None):
        self.group = decode_group(name) if name is not None else None

    @property
    def group(self) -> str | None:
        """The group path as represented by the heaobject.group module. Setting this attribute automatically generates
        values for name attribute. There is expected to be a one-to-one relationship between the group and id. Cannot
        be the empty string."""
        return self.__group

    @group.setter
    def group(self, group: str | None):
        if group == '':
            raise ValueError('group cannot be the empty string')
        self.__group = str(group) if group is not None else None
        if self.__display_name is None:
            self.__display_name = self.__group

    @property
    def type_display_name(self) -> str:
        return 'Group'

    @property
    def display_name(self) -> str:
        """The group display name, which is the group path in the group attribute, if populated, or the default
        display name."""
        return self.__display_name if self.__display_name is not None else super().display_name

    @display_name.setter
    def display_name(self, display_name: str):
        self.__display_name = str(display_name) if display_name is not None else None

    def add_role_id(self, role_id: str):
        """
        Adds a role id to the list of role ids.

        :param role_id: the role id to add.
        """
        type(self).role_ids.add(self, role_id)

    def remove_role_id(self, role_id: str):
        """
        Removes a role id from the list of role ids.

        :param role_id: the role id to remove.
        """
        type(self).role_ids.remove(self, role_id)

    @property
    def group_type(self) -> GroupType:
        return self.__group_type

    @group_type.setter
    def group_type(self, group_type: GroupType):
        if group_type is None:
            self.__group_type = GroupType.ADMIN
        else:
            self.__group_type = group_type if isinstance(group_type, GroupType) else GroupType[str(group_type)]

    @property
    def super_admin_default_permissions(self) -> list[Permission]:
        """
        The default permissions that the super admin has for this object (all permissions except CREATOR and DELETER).
        """
        if self.group == SUPERADMIN_GROUP:
            return [Permission.VIEWER]
        else:
            return super().super_admin_default_permissions


class AccessToken(AbstractDesktopObject):
    def __init__(self) -> None:
        super().__init__()
        self.__id: str | None = None
        self.__auth_scheme: str | None = None

    @property
    def id(self) -> str | None:
        """
        The IDC token issued by keycloak.
        """
        return self.__id

    @id.setter
    def id(self, id_: str | None):
        self.__id = id_

    @property
    def auth_scheme(self) -> str | None:
        """
         The auth_scheme precedes the id token typically Bearer
        """
        return self.__auth_scheme if self.__auth_scheme else 'Bearer'

    @auth_scheme.setter
    def auth_scheme(self, auth_scheme: str | None):
        self.__auth_scheme = auth_scheme


def encode_role(role: str) -> str:
    """
    Encodes a role string using the Base 64 URL- and filesystem-safe alphabet, which replaces '+' with '-' and '/' with
    '_' in the base 64 alphabet as described in the IETF RFC 4648 specification section 5.

    :param role: the role string (required).
    :returns: returns the encoded data as a utf-8 string.
    """
    return urlsafe_b64encode(role.encode(ROLE_ENCODING)).decode(ROLE_ENCODING)

def decode_role(role_encoded: str) -> str:
    """
    Decodes a string encoded using this module's encode_role() function.

    :param role_encoded: the encoded role string (required).
    :returns: the decoded data as a utf-8 string.
    """
    return urlsafe_b64decode(role_encoded).decode(ROLE_ENCODING)

def encode_group(group: str) -> str:
    """
    Encodes a group string using the Base 64 URL- and filesystem-safe alphabet, which replaces '+' with '-' and '/' with
    '_' in the base 64 alphabet as described in the IETF RFC 4648 specification section 5.

    :param group: the group string (required).
    :returns: returns the encoded data as a utf-8 string.
    """
    return encode_role(group)

def decode_group(group_encoded: str) -> str:
    """
    Decodes a string encoded using this module's encode_group() function.

    :param group_encoded: the encoded group string (required).
    :returns: the decoded data as a utf-8 string.
    """
    return decode_role(group_encoded)

def get_system_person(id_: str) -> Person:
    """
    Gets a Person object for the system user with the given id_ (from heaobject.user).

    :param id_: the id of the system user (required).
    :returns: the Person object.
    :raises ValueError: if there is no system user with the provided id_.
    """
    if id_ not in _system_user_display_names:
        raise ValueError(f'No system user with id {id_}')
    p: Person = Person()
    p.id = id_
    p.name = id_
    p.display_name = _system_user_display_names[id_]
    p.source = HEA
    p.owner = NONE_USER
    share: Share = ShareImpl()
    share.user = ALL_USERS
    share.permissions = [Permission.VIEWER]
    p.add_user_share(share)
    return p


def get_system_people() -> list[Person]:
    """
    Gets a list of all system users as Person objects.
    :returns: a list of Person objects.
    """
    return [get_system_person(id_) for id_ in _system_user_display_names]


_validate_email = partial(validate_email, check_deliverability=False)

_system_user_display_names = {
    NONE_USER: 'None',
    ALL_USERS: 'All users',
    TEST_USER: 'Test user',
    SOURCE_USER: 'Source user',
    AWS_USER: 'AWS account holder',
    CREDENTIALS_MANAGER_USER: 'Automatic credentials manager'
}
