from collections.abc import Iterable
from heaobject.attribute import CopyBehavior, IdAttribute, IdListWithBackingSetAttribute, ListAttribute, StrOrNoneAttribute
from heaobject.decorators import attribute_metadata
from heaobject.root import AbstractDesktopObject, AbstractMemberObject, View
from typing import Generic, Optional, TypeVar, TYPE_CHECKING

from abc import ABC, abstractmethod


if TYPE_CHECKING:
    from heaobject.account import Account, AccountView
    from heaobject.organization import Organization
    from heaobject.person import Person

class CollaboratorAction(AbstractDesktopObject, View, ABC):

    account_id = IdAttribute(doc='The id of the account view involved in the collaboration (optional).')
    organization_id = IdAttribute(doc='The id of the organization involved in the collaboration (optional).')
    collaborator_id = IdAttribute(doc='The collaborator context.')
    preferred_name = StrOrNoneAttribute(doc='The preferred name of the collaborator (optional).')

    @abstractmethod
    def __init__(self, person: Optional['Person'] = None,
                 account: Optional['AccountView'] | 'Account' = None,
                 organization: Optional['Organization'] = None) -> None:
        """
        Creates a view of a person who is an organization's collaborator. It populates the view with information from
        the person, account, and organization objects.
        :param person: The person who is the collaborator (optional).
        :param account: The account view or account that the collaborator is associated with (optional).
        :param organization: The organization that the collaborator is associated with (optional).
        """
        super().__init__()
        from heaobject.person import Person  # Avoid circular import
        from heaobject.account import AccountView, Account
        from heaobject.organization import Organization
        if person is not None and not isinstance(person, Person):
            raise TypeError("person must be a Person or None")
        if account is not None and not isinstance(account, (AccountView, Account)):
            raise TypeError("account must be an AccountView, Account, or None")
        if organization is not None and not isinstance(organization, Organization):
            raise TypeError("organization must be an Organization or None")
        self.__display_name: str | None = None
        self.__overridden_display_name: str | None = None
        self.__last_name: str | None = None
        self.__first_name: str | None = None
        if person is not None:
            self.collaborator_id = person.id
            self.first_name = person.first_name
            self.last_name = person.last_name
            self.preferred_name = person.preferred_name
            self.actual_object_id = person.id
            self.actual_object_type_name = person.get_type_name()
        else:
            self.actual_object_type_name = Person.get_type_name()
        if account is not None:
            self.account_id = account.id if isinstance(account, View) else account.instance_id
        if organization is not None:
            self.organization_id = organization.id

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

    def __update_display_name(self):
        fname = self.first_name if self.first_name else ""
        lname = self.last_name if self.last_name else ""
        if fname or lname:
            self.__display_name = f"{fname}{' ' if fname and lname else ''}{lname}"
        else:
            self.__display_name = None


class AddingCollaborator(CollaboratorAction):
    """
    View of a person who is an organization's collaborator and whose access to the organization's data is being
    added.
    """
    def __init__(self, person: Optional['Person'] = None,
                 account: Optional['AccountView'] | 'Account' = None,
                 organization: Optional['Organization'] = None, **kwargs) -> None:
        super().__init__(person=person, account=account, organization=organization)


class RemovingCollaborator(CollaboratorAction):
    """
    View of a person who was an organization's collaborator and whose access to the organization's data is being
    removed.
    """
    def __init__(self, person: Optional['Person'] = None,
                 account: Optional['AccountView'] | 'Account' = None,
                 organization: Optional['Organization'] = None, **kwargs) -> None:
        super().__init__(person=person, account=account, organization=organization)


class AWSCollaboratorAction(CollaboratorAction, ABC):
    """
    View of a person who is an organization's collaborator and whose access to the organization's data is being
    added.
    """
    bucket_id = IdAttribute(doc='The id of the bucket involved in the collaboration (optional).')


class AWSAddingCollaborator(AWSCollaboratorAction, AddingCollaborator):
    """
    View of a person who is an organization's collaborator and whose access to the organization's data is being
    added.
    """
    pass


class AWSRemovingCollaborator(AWSCollaboratorAction, RemovingCollaborator):
    """
    View of a person who was an organization's collaborator and whose access to the organization's data is being
    removed.
    """
    pass


class Collaborators(AbstractMemberObject, ABC):
    """
    Abstract base class for collaborators. Subclasses are expected to define additional attributes that specify the
    resources the collaborator can access.
    """
    collaborator_ids = IdListWithBackingSetAttribute(doc='The id of the person involved in the collaboration (required).')

    def __init__(self, collaborator_ids: Optional[Iterable[str]] = None) -> None:
        super().__init__()
        self.collaborator_ids = collaborator_ids

    @property
    def type_display_name(self) -> str:
        return "Collaborator"

    def add_collaborator_id(self, value: str) -> None:
        """
        Adds a collaborator to this account. Duplicates are ignored.

        :param value: the id of the collaborator to add.
        """
        type(self).collaborator_ids.add(self, value)

    def remove_collaborator_id(self, value: str) -> None:
        """
        Removes a collaborator from this account.

        :param value: the id of the collaborator to remove.
        """
        type(self).collaborator_ids.remove(self, value)

    def has_collaborator_ids(self) -> bool:
        """Returns True if there are any collaborator ids."""
        return type(self).collaborator_ids.len(self) > 0

    @abstractmethod
    def get_resource_attributes(self) -> list[str]:
        pass

    def empty(self) -> bool:
        """Returns True if there are no collaborator ids."""
        return not self.has_collaborator_ids()

    def __contains__(self, item) -> bool:
        if type(self) != type(item):
            return False
        resource_attributes = self.get_resource_attributes()
        if resource_attributes != item.get_resource_attributes():
            return False
        if any(getattr(self, attr) != getattr(item, attr) for attr in resource_attributes):
            return False

        return set(item.collaborator_ids).issubset(self.collaborator_ids)


COLLAB = TypeVar('COLLAB', bound=Collaborators)


class CollaboratorsMixin(Generic[COLLAB], ABC):
    """
    A mixin for objects that have collaborators. Collaborator management will enforce runtime type checking if the
    collaborators_cls class attribute is set to the class of collaborators to check.
    """

    collaborators_cls = Collaborators
    __collaborators: ListAttribute[COLLAB]

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls.__collaborators = ListAttribute[COLLAB](doc='The ids of the collaborators in this organization.',
                                                    copy_behavior=CopyBehavior.DEEP_COPY, objtype=cls.collaborators_cls)
        cls.__collaborators.__set_name__(cls, f'_{cls.__name__}__collaborators')

    @property
    def collaborators(self) -> list[COLLAB]:
        """The list of collaborators associated with this organization. Each collaborator specifies a set of person ids
        and an optional account id."""
        return self.__collaborators

    @collaborators.setter
    def collaborators(self, collaborators: list[COLLAB]) -> None:
        if not isinstance(collaborators, Iterable):
            collaborators = [collaborators]
        self.clear_collaborators()
        for c in collaborators or []:
            self.add_collaborators_to(c)

    def add_collaborators_to(self, collaborator: COLLAB) -> None:
        """
        Adds the person ids to an existing collaborator object if the account id matches, otherwise adds a copy of the
        collaborator.

        :param collaborator: the collaborator(s) to add.
        """
        if collaborator.has_collaborator_ids():
            for c in self.collaborators:
                if all(getattr(c, attr) == getattr(collaborator, attr) \
                       for attr in collaborator.get_resource_attributes()):
                    type(self).__collaborators.remove(self, c)
                    for pid in collaborator.collaborator_ids:
                        c.add_collaborator_id(pid)
                    type(self).__collaborators.add(self, c)
                    break
            else:
                type(self).__collaborators.add(self, collaborator)

    def remove_collaborators_from(self, collaborator: COLLAB) -> None:
        """
        Removes the person ids from an existing collaborator object if the account id matches, otherwise does nothing.
        If the resulting collaborator has no person ids, it is removed. Specifying a collaborator object with no
        account id removes the collaborator ids entirely.

        :param collaborator: the collaborator(s) to remove.
        """
        for c in self.collaborators:
            if all(getattr(c, attr) is None or getattr(c, attr) == getattr(collaborator, attr) \
                   for attr in collaborator.get_resource_attributes()):
                type(self).__collaborators.remove(self, c)
                for pid in collaborator.collaborator_ids:
                    if pid in c.collaborator_ids:
                        c.remove_collaborator_id(pid)
                if c.has_collaborator_ids():
                    type(self).__collaborators.add(self, c)

    def clear_collaborators(self) -> None:
        """Removes all collaborators from this organization."""
        type(self).__collaborators.__set__(self, [])

    def has_collaborators(self, other: COLLAB) -> bool:
        if self.collaborators_cls != type(other):
            return False
        for c in self.collaborators:
            if other in c:
                return True
        return False
