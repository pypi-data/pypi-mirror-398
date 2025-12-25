"""
Desktop and member objects that compose the HEA registry.
"""

from . import root
import yarl
import copy
from typing import Optional, Mapping, Union, Sequence
from .volume import DEFAULT_FILE_SYSTEM
from .user import ALL_USERS
from .util import to_bool
from .volume import MongoDBFileSystem
from .data import DataObject
import uritemplate
from uritemplate.orderedset import OrderedSet


DEFAULT_COLLECTION_MIME_TYPE = 'application/x.collection'


class Resource(root.AbstractMemberObject):
    """
    Metadata describing a REST API resource served by a HEA microservice.
    Resource objects each have a corresponding Collection desktop object that
    provides a convenient way to retrieve objects managed by the resource, or
    you can use the resource's get_resource_url() method to get a URL for
    working with desktop objects served by the resource.

    The resource metadata allows identifying the REST resource that serves a
    particular type of desktop object. Other metadata include a display name
    for the type of object served by the resource, the users who can create new
    desktop objects with the resource, the default shares for desktop objects
    created using the resource, and the users who can access this resource's
    collection object.
    """

    DEFAULT_COLLECTION_MIME_TYPE = DEFAULT_COLLECTION_MIME_TYPE

    def __init__(self, resource_type_name: Optional[str] = None,
                 base_path: str = '',
                 file_system_name: str = DEFAULT_FILE_SYSTEM,
                 file_system_type: str = MongoDBFileSystem.get_type_name(),
                 resource_collection_type_display_name: str | None = None):
        """
        Constructor, with the option to set the resource's properties.

        :param resource_type_name: the type name of HEAObject that is served by
        this resource.
        :param base_path: the path to be appended to the base URL or external
        base URL of the component when constructing a resource URL. See
        Component.get_resource_url(). The base path must not begin with a /.
        """
        super().__init__()
        if resource_type_name is not None and not root.is_heaobject_type(resource_type_name):
            raise ValueError(f'resource_type_name {resource_type_name} not a type of HEAObject')
        self.__resource_type_name: Optional[str] = str(resource_type_name) if resource_type_name is not None else None
        self.__base_path = str(base_path) if base_path is not None else ''
        self.__file_system_name: str = str(file_system_name) if file_system_name is not None else DEFAULT_FILE_SYSTEM
        self.__file_system_type: str = str(file_system_type) if file_system_type is not None else MongoDBFileSystem.get_type_name()
        self.__resource_collection_type_display_name = str(resource_collection_type_display_name) if resource_collection_type_display_name is not None else None
        self.__creator_users = set[str]()
        self.__creator_groups = set[str]()
        self.__collection_accessor_users = set[str]()
        self.__collection_accessor_groups = set[str]()
        self.__default_shares: list[root.Share] = []
        self.__manages_creators = False
        self.__display_in_system_menu = False
        self.__display_in_user_menu = False
        self.__collection_mime_type = self.DEFAULT_COLLECTION_MIME_TYPE

    @property
    def base_path(self) -> str:
        """
        The path to be appended to the base URL or external base URL of the component when constructing a resource URL.
        See Component.get_resource_url(). The base path must not begin with a / unless the component's base URL is
        None. The default base_path is the empty string. The base path may be a URI template. If so, it must support
        the following standard template keys:
            volume_id: the HEA Object's volume id
            id: the HEA object's unique id.
        """
        return self.__base_path

    @base_path.setter
    def base_path(self, base_path: str) -> None:
        if base_path is not None:
            u = yarl.URL(base_path)
            if not u.is_absolute() and base_path.startswith('/'):
                raise ValueError (f'relative base_path {base_path} cannot start with /')
        self.__base_path = str(base_path) if base_path is not None else ''

    @property
    def resource_type_name(self) -> str | None:
        """
        The type name of HEAObject that is served by this resource.
        """
        return self.__resource_type_name

    @resource_type_name.setter
    def resource_type_name(self, type_name: str | None):
        if type_name is not None and not root.is_heaobject_type(type_name):
            raise ValueError(f'type_name {type_name} not a type of HEAObject')
        self.__resource_type_name = str(type_name) if type_name is not None else None

    @property
    def resource_collection_type_display_name(self) -> str:
        """A display name for collections of this resource type. Defaults to the value of the resource_type_name attribute."""
        if self.__resource_collection_type_display_name is not None:
            return self.__resource_collection_type_display_name
        elif self.resource_type_name:
            return self.resource_type_name
        else:
            return 'Unknown'

    @resource_collection_type_display_name.setter
    def resource_collection_type_display_name(self, resource_collection_type_display_name: str):
        self.__resource_collection_type_display_name = str(resource_collection_type_display_name) if resource_collection_type_display_name is not None else None

    @property
    def file_system_name(self) -> str:
        """
        Optional file system name to which this resource applies. A value of None is equivalent to the default file
        system (see the heaobject.volume module).
        """
        return self.__file_system_name

    @file_system_name.setter
    def file_system_name(self, file_system_name: str | None) -> None:
        self.__file_system_name = str(file_system_name) if file_system_name is not None else DEFAULT_FILE_SYSTEM

    @property
    def file_system_type(self) -> str:
        """
        Optional file system type to which this resource applies. A value of None is equivalent to the default file
        system (see the heaobject.volume module).
        """
        return self.__file_system_type

    @file_system_type.setter
    def file_system_type(self, file_system_type: str | None) -> None:
        self.__file_system_type = str(file_system_type) if file_system_type is not None else MongoDBFileSystem.get_type_name()

    @property
    def manages_creators(self) -> bool:
        """Whether the microservice uses this resource to decide who can create new objects. The default is False. If
        True, the only users who can create new objects are those in the creator_users list or who are a member of a
        group in the creator_groups list."""
        return self.__manages_creators

    @manages_creators.setter
    def manages_creators(self, manages_creators: bool):
        self.__manages_creators = to_bool(manages_creators)

    @property
    def creator_users(self) -> list[str]:
        """
        Users who can create desktop objects managed by this resource. Used by HEA if the manages_creators attribute is
        True. Returns a de-duplicated list. This attribute and the add_*, remove_*, and is_* methods must all be
        overridden together.
        """
        return list(self.__creator_users)

    @creator_users.setter
    def creator_users(self, creator_users: list[str]):
        if creator_users is None:
            raise ValueError('creator_users cannot be None')
        if not all(isinstance(r, str) for r in creator_users):
            raise TypeError('creator_users must contain all user strings')
        self.__creator_users = set(creator_users)

    def add_creator_user(self, creator_user: str):
        """
        Adds the provided creator user to the creator users list.

        :param creator_user: the creator user.
        """
        self.__creator_users.add(str(creator_user))

    def remove_creator_user(self, creator_user: str):
        """
        Removes the provided creator user from the creator users list.

        :param creator_user: the creator user.
        :raises ValueError: if the user is not present.
        """
        self.__creator_users.remove(creator_user)

    def is_creator_user(self, sub: str) -> bool:
        """
        Returns whether the user is in the creator user list.

        :param sub: the user (required).
        :return: True or False.
        """
        return sub in self.__creator_users or sub == ALL_USERS

    @property
    def creator_groups(self) -> list[str]:
        """
        Groups that can create desktop objects managed by this resource. Used by HEA if the manages_creators attribute
        is True. Returns a de-duplicated list. This attribute and the add_*, remove_*, and is_* methods must all be
        overridden together.
        """
        return list(self.__creator_groups)

    @creator_groups.setter
    def creator_groups(self, creator_groups: list[str]):
        if creator_groups is None:
            raise ValueError('creator_groups cannot be None')
        if not all(isinstance(r, str) for r in creator_groups):
            raise TypeError('creator_groups must contain all user strings')
        self.__creator_groups = set(creator_groups)

    def add_creator_group(self, creator_group: str):
        """
        Adds the provided creator group to the creator groups list.

        :param creator_group: the creator group to add.
        """
        self.__creator_groups.add(str(creator_group))

    def remove_creator_group(self, creator_group: str):
        """
        Removes the provided creator group from the creator groups list.

        :param creator_group: the creator group to remove.
        :raises ValueError: if the group is not present.
        """
        self.__creator_groups.remove(creator_group)

    def is_creator_group(self, group: str) -> bool:
        """
        Returns whether the group is in the creator group list.

        :param sub: the group (required).
        :return: True or False.
        """
        return group in self.__creator_groups

    async def is_creator(self, context: root.PermissionContext) -> bool:
        """
        Returns whether the user can create desktop objects managed by this resource. This method checks the
        creator user and group lists, and the user's groups. It does not consider the manages_creators attribute.

        :param context: the permission context for the user (required).
        :return: True or False.
        """
        return self.is_creator_user(context.sub) or \
            bool(self.__creator_groups.intersection(await context.get_groups()))

    @property
    def collection_accessor_users(self) -> list[str]:
        """
        Users who can access desktop objects managed by this resource via a Collection. An empty list means no one can
        access these objects via a Collection. Getting the users will return a de-duplicated list. This attribute
        and the add_*, remove_*, and is_* methods must all be overridden together.
        """
        return list(self.__collection_accessor_users)

    @collection_accessor_users.setter
    def collection_accessor_users(self, collection_accessor_users: list[str]):
        if collection_accessor_users is None:
            raise ValueError('collection_accessor_users cannot be None')
        if not all(isinstance(r, str) for r in collection_accessor_users):
            raise TypeError('collection_accessor_users must contain all user strings')
        self.__collection_accessor_users = set(collection_accessor_users)

    def add_collection_accessor_user(self, collection_accessor_user: str):
        """
        Adds the provided user to the collection accessor user list.

        :param collection_accessor_user: the user.
        """
        self.__collection_accessor_users.add(str(collection_accessor_user))

    def remove_collection_accessor_user(self, collection_accessor_user: str):
        """
        Removes the provided user from the collection accessor user list.

        :param collection_accessor_user: the user.
        :raises ValueError: if the user is not present.
        """
        self.__collection_accessor_users.remove(collection_accessor_user)

    def is_collection_accessor_user(self, sub: str) -> bool:
        """
        Returns whether the user is in the collection accessor user list.

        :param sub: the user sub (required).
        :return: True or False.
        """
        return bool({sub, root.ALL_USERS}.intersection(self.__collection_accessor_users))

    @property
    def collection_accessor_groups(self) -> list[str]:
        """
        Groups who can access desktop objects managed by this resource via a Collection. An empty list means no one can
        access these objects via a Collection. Getting the groups will return a de-duplicated list. This attribute
        and the add_*, remove_*, and is_* methods must all be overridden together.
        """
        return list(self.__collection_accessor_groups)

    @collection_accessor_groups.setter
    def collection_accessor_groups(self, collection_accessor_groups: list[str]):
        if collection_accessor_groups is None:
            raise ValueError('collection_accessor_groups cannot be None')
        if not all(isinstance(r, str) for r in collection_accessor_groups):
            raise TypeError('collection_accessor_groups must contain all group strings')
        self.__collection_accessor_groups = set(collection_accessor_groups)

    def add_collection_accessor_group(self, collection_accessor_group: str):
        """
        Adds the provided group to the collection accessor group list.

        :param collection_accessor_group: the group.
        """
        self.__collection_accessor_groups.add(str(collection_accessor_group))

    def remove_collection_accessor_group(self, collection_accessor_group: str):
        """
        Removes the provided group from the collection accessor group list.

        :param collection_accessor_group: the group.
        :raises ValueError: if the group is not present.
        """
        self.__collection_accessor_groups.remove(collection_accessor_group)

    async def is_collection_accessor_group(self, context: root.PermissionContext) -> bool:
        """
        Returns whether any of the user's groups is in the collection accessor group list.

        :param context: the user context (required).
        :return: True or False.
        """
        return bool(self.__collection_accessor_groups.intersection(await context.get_groups()))

    async def is_collection_accessor(self, context: root.PermissionContext) -> bool:
        """
        Returns whether the user can access the collection of desktop objects represented by this resource, consulting
        both the collection accessor users and groups.

        :param context: the permission context for the user (required).
        :return: True or False.
        """
        return self.is_collection_accessor_user(context.sub) or await self.is_collection_accessor_group(context)

    def get_collection_shares(self) -> list[root.Share]:
        """
        Returns the shares for this collection.

        :return: the user's shares for this collection, if any.
        """
        shares = list[root.Share]()
        for user in self.collection_accessor_users:
            share: root.Share = root.ShareImpl()
            share.user = user
            share.permissions = [root.Permission.VIEWER]
            shares.append(share)
        for group in self.collection_accessor_groups:
            share = root.ShareImpl()
            share.group = group
            share.permissions = [root.Permission.VIEWER]
            shares.append(share)
        return shares

    @property
    def default_shares(self) -> list[root.Share]:
        """
        Default permissions for desktop objects managed by this resource.
        """
        return copy.deepcopy(self.__default_shares)

    @default_shares.setter
    def default_shares(self, shares: list[root.Share]):
        if shares is None:
            raise ValueError('shares cannot be None')
        if not all(isinstance(r, root.Share) for r in shares):
            raise TypeError('shares must contain all Share objects')
        self.__default_shares = list(copy.deepcopy(r) for r in shares)

    def add_default_share(self, share: root.Share) -> None:
        """
        Adds a Share to the default shares for desktop objects managed by this resource.

        :param value: a Share object.
        """
        if not isinstance(share, root.Share):
            raise TypeError('value must be a Share')
        self.__default_shares.append(copy.deepcopy(share))

    def remove_default_share(self, share: root.Share) -> None:
        """
        Removes a Share from the default shares for desktop objects managed by this resource.

        :param value: a Share object.
        :raises ValueError if the share is not present.
        """
        if not isinstance(share, root.Share):
            raise TypeError('value must be a Share')
        self.__default_shares.remove(share)

    @property
    def display_in_system_menu(self) -> bool:
        """
        Whether the collection corresponding to this resource should be displayed in the
        system menu. The default is False. Regardless of this setting, the collection will
        only be displayed if the user has permission to view it.
        """
        return self.__display_in_system_menu

    @display_in_system_menu.setter
    def display_in_system_menu(self, display_in_system_menu: bool) -> None:
        self.__display_in_system_menu = to_bool(display_in_system_menu)

    @property
    def display_in_user_menu(self) -> bool:
        """
        Whether the collection corresponding to this resource should be displayed in the user
        menu. The default is False. Regardless of this setting, the collection will only be
        displayed if the user has permission to view it.
        """
        return self.__display_in_user_menu

    @display_in_user_menu.setter
    def display_in_user_menu(self, display_in_user_menu: bool) -> None:
        self.__display_in_user_menu = to_bool(display_in_user_menu)

    @property
    def collection_mime_type(self) -> str:
        """
        The mime type of the collection corresponding to this resource. The default is
        'application/x.collection'.
        """
        return self.__collection_mime_type

    @collection_mime_type.setter
    def collection_mime_type(self, collection_mime_type: str) -> None:
        self.__collection_mime_type = str(collection_mime_type) if collection_mime_type is not None else self.DEFAULT_COLLECTION_MIME_TYPE


class Component(root.AbstractDesktopObject):
    """
    Metadata about a HEA microservice. The component's name must be its distribution package name. Components have one
    or more resources, which are REST API resources that provide access to desktop objects stored on a file system.
    Resources each host a collection of desktop objects of a distinct type.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__base_url: str | None = None
        self.__external_base_url: str | None = None
        self.__resources: list[Resource] = []

    @property
    def base_url(self) -> str | None:
        """
        The base URL of the service for HEA services to call each other. The attribute's setter accepts a string or a
        yarl URL. In the latter case, it converts the URL to a string. In resolving a resource URL with the
        get_resource_url() method, any path part of this attribute will be replaced by the resource's base path.
        """
        return self.__base_url

    @base_url.setter
    def base_url(self, value: str | None) -> None:
        if value is not None:
            if not isinstance(value, str):
                raise TypeError('value must be a str')
            self.__base_url = str(value)
        else:
            self.__base_url = None

    @property
    def external_base_url(self) -> str | None:
        """
        The base URL of the service for HEA services to call each other. The
        attribute's setter accepts a string or a yarl URL. In the latter case, it
        converts the URL to a string. In resolving a resource URL with the
        get_external_resource_url() method, any path part of this attribute will
        be replaced by the resource's base path.
        """
        return self.__external_base_url

    @external_base_url.setter
    def external_base_url(self, value: str | None) -> None:
        if value is not None:
            if not isinstance(value, str):
                raise TypeError('value must be a str')
            self.__external_base_url = str(value)
        else:
            self.__external_base_url = None

    @property
    def resources(self) -> list[Resource]:
        """
        The information that is served by this component. The attribute's setter accepts any iterable and converts it
        to a list. There must be no more than one Resource per Resource.resource_type_name.
        """
        return list(self.__resources)

    @resources.setter
    def resources(self, value: list[Resource]) -> None:
        if value is None:
            raise ValueError('value cannot be None')
        if not all(isinstance(r, Resource) for r in value):
            raise TypeError('value must contain all Resource objects')
        for r in value:
            r._set_parent_object(self)
        self.__resources = list(value)

    @property
    def super_admin_default_permissions(self) -> list[root.Permission]:
        """
        The default permissions that the super admin has for this object (VIEWER and EDITOR).
        """
        return [root.Permission.VIEWER, root.Permission.EDITOR]

    def add_resource(self, value: Resource) -> None:
        """
        Adds a REST resource to the list of resources that are served by this component.
        :param value: a Resource object.
        """
        if not isinstance(value, Resource):
            raise TypeError('value must be a Resource')
        value._set_parent_object(self)
        self.__resources.append(value)

    def remove_resource(self, value: Resource) -> None:
        """
        Removes a REST resource from the list of resources that are served by this component. Ignores None values.
        :param value: a Resource object.
        """
        if not isinstance(value, Resource):
            raise TypeError('value must be a Resource')
        self.__resources.remove(value)
        value._set_parent_object(None)

    def get_resource(self, type_name: str) -> Resource | None:
        """
        Returns the resource with the given type.

        :param type_name: a HEA object type or type name.
        :return: a Resource, or None if this service does not serve resources of the given type.
        :raises ValueError: if type_name is not a valid HEA object type.
        """
        if not root.is_heaobject_type(type_name):
            raise ValueError('type_name not a type of HEAObject')

        for resource in self.__resources:
            if type_name == resource.resource_type_name:
                return resource
        return None

    def get_resource_url(self, type_name: str,
                         parameters: Optional[Mapping[str, Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]]] = None,
                         **kwargs: Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]) -> str | None:
        """
        Returns the base URL of resources of the given type. It constructs the
        URL by combining the base_url of the component with the base path
        provided in the Resource object corresponding to this type.

        :param type_name: a HEA object type or type name.
        :param parameters: an optional dictionary of parameters for expanding the resource's base path.
        :param kwargs: alternative way of specifying parameters.
        :return: a URL string, or None if this service does not serve resources of the given type.
        :raises ValueError: if type_name is not a valid HEA object type.
        """
        return self.__get_resource_url(self.base_url, type_name, parameters, **kwargs)

    def get_external_resource_url(self, type_name: str,
                         parameters: Optional[Mapping[str, Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]]] = None,
                         **kwargs: Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]) -> str | None:
        """
        Returns the external base URL of resources of the given type. It
        constructs the URL by combining the external_base_url of the component
        with the base path provided in the Resource object corresponding to
        this type.

        :param type_name: a HEA object type or type name.
        :param parameters: an optional dictionary of parameters for expanding
        the resource's base path.
        :param kwargs: alternative way of specifying parameters.
        :return: a URL string, or None if this service does not serve resources
        of the given type.
        :raises ValueError: if type_name is not a valid HEA object type.
        """
        return self.__get_resource_url(self.external_base_url, type_name, parameters, **kwargs)

    def __get_resource_url(self, base_url: str | None, type_name: str,
                         parameters: Optional[Mapping[str, Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]]] = None,
                         **kwargs: Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]):
        """
        Constructs a REST resource URL from the given base URL and a
        base path from one of the component's Resource objects. The base path
        may contain URI template-style parameters.

        :param base_url: the base URL (required). If None, just the base path
        is used to construct a relative URL.
        :param type_name: the type name of the resource to use (required).
        :param parameters: If the base path has any URI template-style
        parameters, they will be substituted with the values in this mapping.
        :param kwargs: additional parameters may be specified as keyword
        arguments.
        :return a URL string, or None if no resource matched the type_name and
        file_system_name arguments.
        """
        resource = self.get_resource(type_name)
        parameters_ = dict(parameters or [])
        parameters_.update(kwargs)
        if resource is None:
            return None
        else:
            vars_ = uritemplate.variables(resource.base_path) if resource.base_path is not None else OrderedSet()
            if vars_ > parameters_.keys():
                raise ValueError(f'Missing parameters: {", ".join(v for v in vars_ if v not in parameters_.keys())}')
            base_path = resource.base_path
            if base_url:
                return str(yarl.URL(base_url) / uritemplate.expand(base_path, parameters_))
            else:
                return uritemplate.expand(base_path, parameters_)

    @property
    def type_display_name(self) -> str:
        return 'Registry Component'


class Property(root.NonCreatorSuperAdminDefaultPermissionsMixin, root.AbstractDesktopObject):
    """
    System or user configuration as key-value pairs. Use the owner and shares
    attributes to control to which users a attribute applies.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__value: str | None = None

    @property
    def value(self) -> str | None:
        return self.__value

    @value.setter
    def value(self, value: str | None):
        self.__value = str(value) if value is not None else None

    @property
    def type_display_name(self) -> str:
        return 'Property'


class Collection(DataObject):
    """
    A group of desktop objects of the same type.
    """

    DEFAULT_MIME_TYPE = DEFAULT_COLLECTION_MIME_TYPE

    def __init__(self) -> None:
        super().__init__()
        self.__url: str | None = None
        self.__collection_type_name: str | None = None
        self.__file_system_type: str = MongoDBFileSystem.get_type_name()
        self.__file_system_name: str = DEFAULT_FILE_SYSTEM
        self.__display_in_system_menu = False
        self.__display_in_user_menu = False
        self.__mime_type = self.DEFAULT_MIME_TYPE

    @property
    def mime_type(self) -> str:
        return self.__mime_type

    @mime_type.setter
    def mime_type(self, mime_type: str) -> None:
        if mime_type is not None:
            self.__mime_type = str(mime_type)
        else:
            self.__mime_type = self.DEFAULT_MIME_TYPE

    @property
    def url(self) -> str | None:
        """The URL for retrieving the objects in the collection. If a relative
        URL, it may not be prefixed with a forward slash."""
        return self.__url

    @url.setter
    def url(self, url: str | None):
        if url is not None:
            u = yarl.URL(url)
            if not u.is_absolute() and url.startswith('/'):
                raise ValueError(f'relative url {url} cannot start with /')
        self.__url = str(url) if url is not None else None

    @property
    def collection_type_name(self) -> str | None:
        """The type name of the desktop objects in the collection."""
        return self.__collection_type_name

    @collection_type_name.setter
    def collection_type_name(self, collection_type_name: str | None):
        self.__collection_type_name = str(collection_type_name) if collection_type_name is not None else None

    @property
    def file_system_name(self) -> str:
        """
        Optional file system name to which this resource applies. A value of None is equivalent to the default file
        system (see the heaobject.volume module).
        """
        return self.__file_system_name

    @file_system_name.setter
    def file_system_name(self, file_system_name: str | None) -> None:
        self.__file_system_name = str(file_system_name) if file_system_name is not None else DEFAULT_FILE_SYSTEM

    @property
    def file_system_type(self) -> str:
        """
        Optional file system type to which this resource applies. A value of None is equivalent to the default file
        system (see the heaobject.volume module).
        """
        return self.__file_system_type

    @file_system_type.setter
    def file_system_type(self, file_system_type: str | None) -> None:
        self.__file_system_type = str(file_system_type) if file_system_type is not None else MongoDBFileSystem.get_type_name()

    @property
    def type_display_name(self) -> str:
        return 'Collection'

    @property
    def display_in_system_menu(self) -> bool:
        """
        Whether this collection should be displayed in the system menu. The default is False.
        Regardless of this setting, the collection will only be displayed if the user has
        permission to view it.
        """
        return self.__display_in_system_menu

    @display_in_system_menu.setter
    def display_in_system_menu(self, display_in_system_menu: bool) -> None:
        self.__display_in_system_menu = bool(display_in_system_menu)

    @property
    def display_in_user_menu(self) -> bool:
        """
        Whether this collection should be displayed in the user menu. The default is False.
        Regardless of this setting, the collection will only be displayed if the user has
        permission to view it.
        """
        return self.__display_in_user_menu

    @display_in_user_menu.setter
    def display_in_user_menu(self, display_in_user_menu: bool) -> None:
        self.__display_in_user_menu = bool(display_in_user_menu)

    @property
    def super_admin_default_permissions(self) -> list[root.Permission]:
        """
        The default permissions that the super admin has for this object (VIEWER, EDITOR, and CREATOR).
        """
        return [root.Permission.VIEWER, root.Permission.EDITOR, root.Permission.CREATOR]

    @classmethod
    def get_owner_permissions(cls):
        """
        Returns the permissions that owners of objects of this class have. Returns all permissions.
        """
        return list(root.Permission)
