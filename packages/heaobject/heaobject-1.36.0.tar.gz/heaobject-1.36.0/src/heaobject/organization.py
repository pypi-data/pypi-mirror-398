from collections.abc import Iterable, Sequence
import logging
import warnings

from .collaborator import Collaborators

from .attribute import CopyBehavior, IdListWithBackingSetAttribute, ListAttribute, StrOrNoneAttribute, UniqueListAttribute
from .root import AbstractMemberObject, Permission, NonCreatorSuperAdminDefaultPermissionsMixin
from .data import DataObject, SameMimeType
from .collaborator import CollaboratorsMixin
from .decorators import attribute_metadata
from typing import Optional
from enum import Enum
from .util import raise_if_none_or_empty_string, raise_if_empty_string


permission_id_dict = {
    'admin_ids': [Permission.COOWNER],
    'manager_ids': [Permission.VIEWER, Permission.EDITOR, Permission.SHARER],
    'member_ids': [Permission.VIEWER, Permission.SHARER],
    'collaborator_ids': [Permission.VIEWER]
}
COLLABORATOR_PERMS = [Permission.VIEWER]


class OrganizationGroup(Enum):
    MEMBER = 10
    MANAGER = 20
    ADMIN = 30


class OrganizationCollaborators(Collaborators):
    """
    Represents a collaborator with an organization.
    """
    account_id = StrOrNoneAttribute(doc='The id of the account involved in the collaboration (optional).')

    def __init__(self, account_id: Optional[str] = None, collaborator_ids: Optional[Sequence[str]] = None) -> None:
        super().__init__(collaborator_ids=collaborator_ids)
        self.account_id = account_id

    def get_resource_attributes(self) -> list[str]:
        return ['account_id']


class Organization(CollaboratorsMixin[OrganizationCollaborators], NonCreatorSuperAdminDefaultPermissionsMixin, DataObject, SameMimeType):
    """
    Represents a directory in the HEA desktop.

    NOTE: THE admin_group_ids, manager_group_ids, and member_group_ids are deprecated and will be removed in a future
    release.
    """

    collaborators_cls = OrganizationCollaborators

    def __init__(self) -> None:
        super().__init__()
        # id is a super field
        self.__account_ids: set[str] = set()
        self.__principal_investigator_id: Optional[str] = None  # this would be a people id
        self.__admin_ids: list[str] = []  # list of user ids to be admins
        self.__manager_ids: list[str] = []  # list of user ids to be managers
        self.__member_ids: list[str] = []  # list of user ids to be members
        # super's name and display name would be used as org name(required)
        self.__admin_group_ids: list[str] = []
        self.__manager_group_ids: list[str] = []
        self.__member_group_ids: list[str] = []

    @classmethod
    def get_mime_type(cls) -> str:
        """
        Returns the mime type of instances of the Organization class.

        :return: application/x.organization
        """
        return 'application/x.organization'

    @property
    def mime_type(self) -> str:
        """Read-only. The mime type for Organization objects, application/x.organization."""
        return type(self).get_mime_type()

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def account_ids(self) -> list[str]:
        """The list of accounts owned by this organization. Duplicates are resolved."""
        return list(self.__account_ids)

    @account_ids.setter
    def account_ids(self, account_ids: list[str]):
        self.__account_ids.clear()
        if account_ids:
            self.__account_ids.update(str(account_id) for account_id in account_ids)

    def add_account_id(self, account_id: str):
        self.__account_ids.add(str(account_id))

    def remove_account_id(self, account_id: str):
        try:
            self.__account_ids.remove(str(account_id))
        except KeyError as e:
            raise ValueError(f'{account_id} not in account_ids') from e

    @property
    def principal_investigator_id(self) -> Optional[str]:
        """
        The principal investigator person ID. The id cannot be the empty string.
        """
        return self.__principal_investigator_id

    @principal_investigator_id.setter
    def principal_investigator_id(self, principal_investigator_id: Optional[str]) -> None:
        raise_if_empty_string(principal_investigator_id)
        self.__principal_investigator_id = str(principal_investigator_id) \
            if principal_investigator_id is not None else None

    @property
    def admin_ids(self) -> list[str]:
        """
        The organization manager ids. No id can be the empty string.
        """
        return [i for i in self.__admin_ids] if self.__admin_ids else []

    @admin_ids.setter
    def admin_ids(self, admin_ids: list[str]) -> None:
        if admin_ids is None:
            self.__admin_ids = []
        elif not isinstance(admin_ids, str):
            self.__admin_ids = [raise_if_none_or_empty_string(str(i) if i is not None else None) for i in admin_ids]
        else:
            self.__admin_ids = [raise_if_empty_string(admin_ids)]

    def add_admin_id(self, admin_id: str) -> None:
        if not admin_id:
            raise ValueError('admin_id cannot be None nor the empty string')
        self.__admin_ids.append(str(admin_id))

    def remove_admin_id(self, value: str) -> None:
        """
        Removes a REST manager id from the list of ids that are served by this organization. Ignores None values.
        :param value:  str representing the manager id.
        """
        self.__admin_ids.remove(str(value))

    @property
    def manager_ids(self) -> list[str]:
        """
        The organization manager ids. No id can be the empty string.
        """
        return [i for i in self.__manager_ids] if self.__manager_ids else []

    @manager_ids.setter
    def manager_ids(self, manager_ids: list[str]) -> None:
        if manager_ids is None:
            self.__manager_ids = []
        elif not isinstance(manager_ids, str):
            self.__manager_ids = [raise_if_none_or_empty_string(str(i) if i is not None else None) for i in manager_ids]
        else:
            self.__manager_ids = [raise_if_empty_string(manager_ids)]

    def add_manager_id(self, manager_id: str) -> None:
        if not manager_id:
            raise ValueError('manager_id cannot be None nor the empty string')
        self.__manager_ids.append(str(manager_id))

    def remove_manager_id(self, value: str) -> None:
        """
        Removes a REST manager id from the list of ids that are served by this organization. Ignores None values.
        :param value:  str representing the manager id.
        """
        self.__manager_ids.remove(str(value))

    @property
    def member_ids(self) -> list[str]:
        """
        The organization member ids. No id can be the empty string.
        """
        return [i for i in self.__member_ids]

    @member_ids.setter
    def member_ids(self, member_ids: list[str]) -> None:
        if member_ids is None:
            self.__member_ids = []
        elif not isinstance(member_ids, str):
            self.__member_ids = [raise_if_none_or_empty_string(str(i) if i is not None else None) for i in member_ids]
        else:
            self.__member_ids = [raise_if_empty_string(member_ids)]

    def add_member_id(self, member_id: str) -> None:
        if not member_id:
            raise ValueError('member_id cannot be None nor the empty string')
        self.__member_ids.append(str(member_id))

    def remove_member_id(self, value: str) -> None:
        """
        Removes a REST member id from the list of member ids that are served by this organization. Ignores None values.
        :param value: a str representing the member id.
        """
        self.__member_ids.remove(str(value))

    @property
    def dynamic_permission_supported(self):
        """True because organization objects have dynamic permissions."""
        return True

    def dynamic_permission(self, sub: str) -> list[Permission]:
        """
        Returns permissions if the sub is in the member_ids list, or an empty list if not.

        :param sub: the user id (required).
        :return: A list containing Permissions or the empty list.
        """
        logger = logging.getLogger(__name__)
        try:
            perms: set[Permission] = set()
            if sub == self.principal_investigator_id:
                perms.update(permission_id_dict['manager_ids'])
            for p_id in permission_id_dict:
                if sub in getattr(self, p_id):
                    perms.update(permission_id_dict[p_id])
            return list(perms)
        except:
            logger.exception('Permissions are not correctly configured...returning empty permissions set')
            return []

    def dynamic_attribute_permission(self, attribute: str, sub: str) -> list[Permission] | None:
        """
        Restricts attribute access for users who are not the organization's owner, are not a super admin, and do not
        have a user share nor a group share. This implementation restricts access to organization-specific attributes
        and then calls the super class' custom_attribute_permissions method for any other attributes.

        :param attribute: the attribute to check.
        :param sub: the user.
        :return: the permissions for the attribute, or None if this method does not calculate permissions for the given
        attribute.
        """
        match attribute:
            case 'principal_investigator_id':
                """Only admins and the PI can change the principal investigator id."""
                if sub != self.principal_investigator_id and sub not in self.admin_ids:
                    return [Permission.VIEWER]
                else:
                    return [Permission.VIEWER, Permission.EDITOR]
            case 'account_ids' | 'admin_ids' | 'admin_group_ids' | 'manager_group_ids' | 'member_group_ids':
                """Only admins can change these attributes."""
                if sub not in self.admin_ids:
                    return [Permission.VIEWER]
                else:
                    return [Permission.VIEWER, Permission.EDITOR]
            case 'manager_ids' | 'member_ids':
                """Only admins,  managers, and the PI can change these attributes."""
                if sub not in self.admin_ids and sub not in self.manager_ids and sub != self.principal_investigator_id:
                    return [Permission.VIEWER]
                else:
                    return [Permission.VIEWER, Permission.EDITOR]
            case 'display_name':
                """Only admins can change the display name."""
                if sub not in self.admin_ids:
                    return [Permission.VIEWER]
                else:
                    return [Permission.VIEWER, Permission.EDITOR]
            case 'collaborator_ids':
                """Everyone can view collaborator ids but no one can edit them (it's a read-only attribute)."""
                return [Permission.VIEWER]
        return super().dynamic_attribute_permission(attribute, sub)

    @property
    def member_group_ids(self) -> list[str]:
        """
        The Keycloak groups this organization's members are part of.
        """
        return list(self.__member_group_ids)

    @member_group_ids.setter
    def member_group_ids(self, member_group_ids: list[str]):
        if member_group_ids is None:
            self.__member_group_ids = []
        elif not isinstance(member_group_ids, str):
            self.__member_group_ids = [str(i) for i in member_group_ids]
        else:
            self.__member_group_ids = [str(member_group_ids)]

    def add_member_group_id(self, value: str) -> None:
        """
        Adds a group that this organization's members are part of.

        :param value: the group to add.
        """
        self.__member_group_ids.append(str(value))

    def remove_member_group_id(self, value: str) -> None:
        """
        Removes a group that this organization's members are part of.

        :param value: a str representing the member id.
        """
        self.__member_group_ids.remove(str(value))

    @property
    def manager_group_ids(self) -> list[str]:
        """
        The Keycloak groups this organization's managers are part of.
        """
        return list(self.__manager_group_ids)

    @manager_group_ids.setter
    def manager_group_ids(self, manager_group_ids: list[str]):
        if manager_group_ids is None:
            self.__manager_group_ids = []
        elif not isinstance(manager_group_ids, str):
            self.__manager_group_ids = [str(i) for i in manager_group_ids]
        else:
            self.__manager_group_ids = [str(manager_group_ids)]

    def add_manager_group_id(self, value: str) -> None:
        """
        Adds a group that this organization's managers are part of.

        :param value: the group to add.
        """
        self.__manager_group_ids.append(str(value))

    def remove_manager_group_id(self, value: str) -> None:
        """
        Removes a group that this organization's managers are part of.

        :param value: the group to remove.
        """
        self.__manager_group_ids.remove(str(value))

    @property
    def admin_group_ids(self) -> list[str]:
        """
        The Keycloak groups this organization's admins are part of.
        """
        return list(self.__admin_group_ids)

    @admin_group_ids.setter
    def admin_group_ids(self, admin_group_ids: list[str]):
        if admin_group_ids is None:
            self.__admin_group_ids = []
        elif not isinstance(admin_group_ids, str):
            self.__admin_group_ids = [str(i) for i in admin_group_ids]
        else:
            self.__admin_group_ids = [str(admin_group_ids)]

    def add_admin_group_id(self, value: str) -> None:
        """
        Adds a group that this organization's admins are part of.

        :param value: the group to add.
        """
        self.__admin_group_ids.append(str(value))

    def remove_admin_group_id(self, value: str) -> None:
        """
        Removes a group that this organization's admins are part of.

        :param value: the group to remove.
        """
        self.__admin_group_ids.remove(str(value))

    def get_groups(self, sub: str) -> list[str]:
        """
        Gets the groups that the provided user is a part of. This attribute is deprecated.

        :param sub: the user id.
        :return: a list of groups.
        """
        groups: set[str] = set()
        if sub in self.member_ids:
            groups.update(self.member_group_ids)
        if sub in self.manager_group_ids or sub == self.principal_investigator_id:
            groups.update(self.manager_group_ids)
        if sub in self.admin_group_ids:
            groups.update(self.admin_group_ids)
        return list(groups)

    @property
    def collaborator_ids(self) -> list[str]:
        """
        The ids of the collaborators who can work with this organization's data. Setting this attribute does not
        identify the accounts on which the person is collaborating and is deprecated.
        """
        result = set[str]()
        for c in self.collaborators:
            result.update(c.collaborator_ids)
        return list(result)

    @collaborator_ids.setter
    def collaborator_ids(self, collaborator_ids: list[str]):
        warnings.warn('Setting the collaborator_ids attribute is deprecated. Use the collaborators attribute instead.')
        collabs: list[OrganizationCollaborators] = [OrganizationCollaborators(collaborator_ids=collaborator_ids)]
        self.collaborators = collabs

    def add_collaborator_id(self, value: str) -> None:
        """
        Adds a collaborator to this organization with unknown account id. Duplicates are ignored. This adder exists for
        backwards compatibility with the old collaborator_ids attribute.

        :param value: the id of the collaborator to add.
        """
        warnings.warn('add_collaborator_id is deprecated. Use add_collaborators_to instead.')
        self.add_collaborators_to(OrganizationCollaborators(collaborator_ids=[value]))

    def remove_collaborator_id(self, value: str) -> None:
        """
        Removes a collaborator entirely from this organization.

        :param value: the id of the collaborator to remove.
        """
        for c in self.collaborators:
            if value in c.collaborator_ids:
                self.remove_collaborators_from(OrganizationCollaborators(account_id=c.account_id,
                                                                         collaborator_ids=[value]))

    def add_collaborators_to(self, collaborator: OrganizationCollaborators) -> None:
        """
        Adds the person ids to an existing collaborator object if the account id matches, otherwise adds a copy of the
        collaborator.

        :param collaborator: the collaborator(s) to add.
        """
        if collaborator.has_collaborator_ids():
            if collaborator.account_id:
                self.add_account_id(collaborator.account_id)
        super().add_collaborators_to(collaborator)

    @property
    def type_display_name(self) -> str:
        return "Organization"
