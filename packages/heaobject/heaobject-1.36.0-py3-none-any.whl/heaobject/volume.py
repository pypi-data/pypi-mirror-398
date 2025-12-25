"""
Defines volume and file system desktop object classes.

Volumes and file systems are defined analogously to operating system volumes (sometimes called mounts or drives) and
file systems. File systems are repositories of HEA objects. They may be actual file storage on the server running HEA,
a database, a web service, or a separate file server accessed via standard network protocols like SSH. Volumes provide
a connection to that database or service, possibly passing in credentials. Volumes and file systems are represented by
the Volume and FileSystem classes in this module, respectively. Volumes have a file_system_name attribute with a name
of a FileSystem instance.

Microservices that manage data or application state have a default data store, typically MongoDB, with its connection
information specified in a configuration file. To use the default data store for managing HEA desktop objects, if the
microservice supports it, create a volume with the file_system_name set to DEFAULT_FILE_SYSTEM or None. Or use variants
of the microservice's REST API calls that do not require passing in a volume id.

"""
from abc import ABC
from typing import Optional, TypeVar
from . import root
from .data import DataObject, SameMimeType
from .decorators import attribute_metadata


class FileSystem(root.NonCreatorSuperAdminDefaultPermissionsMixin, root.AbstractDesktopObject, ABC):
    """
    Represents a filesystem, which controls how data is stored and retrieved. In HEA, all filesystems are either
    databases or other storage for REST resource persistence.

    File systems must have a name attribute that is unique per concrete FileSystem subclass. The name is typically a
    connection string, account id, or similar field.
    """
    pass


FileSystemTypeVar = TypeVar('FileSystemTypeVar', bound=FileSystem)


class MongoDBFileSystem(FileSystem):
    """
    MongoDB-based file system.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__connection_string: Optional[str] = None
        self.__database_name: Optional[str] = None

    @property  # type: ignore
    def connection_string(self) -> Optional[str]:
        """The MongoDB connection string."""
        return self.__connection_string

    @connection_string.setter
    def connection_string(self, connection_string: Optional[str]):
        self.__connection_string = str(connection_string) if connection_string is not None else None

    @property  # type: ignore
    def database_name(self) -> Optional[str]:
        """The MongoDB database name"""
        return self.__database_name

    @database_name.setter
    def database_name(self, database_name: Optional[str]):
        self.__database_name = str(database_name) if database_name is not None else None

    @property
    def type_display_name(self) -> str:
        return "MongoDB File System"


class AWSFileSystem(FileSystem):
    """
    AWS-based file system. There can be at most one global AWS file system with name DEFAULT_FILE_SYSTEM, and users may
    have one volume for accessing their AWS account, with an association to a credentials object with the user's AWS
    key and secret.
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def type_display_name(self) -> str:
        return "AWS File System"


class KeycloakFileSystem(FileSystem):
    """
    Keycloak file system. There can be at most one global Keycloak file system with name DEFAULT_FILE_SYSTEM.
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def type_display_name(self) -> str:
        return "Keycloak File System"

class OpenSearchFileSystem(FileSystem):
    """
    OpenSearch file system. There can be at most one global AWS file system with name DEFAULT_FILE_SYSTEM, and users may
    have one volume for accessing their OpenSearch index.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__host: str | None = None
        self.__port: int | None = None
        self.__index: str | None = None

    @property  # type: ignore
    def host(self) -> Optional[str]:
        """The OpenSearch hostname."""
        return self.__host

    @host.setter
    def host(self, host: Optional[str]):
        self.__host = str(host) if host is not None else None

    @property  # type: ignore
    def port(self) -> Optional[int]:
        """The OpenSearch port number."""
        return self.__port

    @port.setter
    def port(self, port: Optional[str]):
        self.__port = int(port) if port is not None else None

    @property  # type: ignore
    def index(self) -> Optional[str]:
        """The OpenSearch index."""
        return self.__index

    @index.setter
    def index(self, index: Optional[str]):
        self.__index = str(index) if index is not None else None

    @property
    def type_display_name(self) -> str:
        return "Open Search File System"



class MemoryFileSystem(FileSystem):
    """
    Represents in-memory desktop object storage.
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def type_display_name(self) -> str:
        return "Memory File System"

class NoFileSystem(FileSystem):
    """
    Represents a volume with no object storage.
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def type_display_name(self) -> str:
        return "No File System"

class Volume(DataObject, SameMimeType):
    """
    A single accessible storage area that stores a single filesystem. Some volumes may require providing credentials in
    order to access them.
    """

    @classmethod
    def get_mime_type(cls) -> str:
        return 'application/x.volume'

    def __init__(self) -> None:
        super().__init__()
        self.__file_system_name = DEFAULT_FILE_SYSTEM
        self.__file_system_type = MongoDBFileSystem.get_type_name()
        self.__credentials_id: Optional[str] = None
        self.__folder_id: Optional[str] = None
        self.__account_id: str | None = None

    @property
    def mime_type(self) -> str:
        return type(self).get_mime_type()

    @property  # type: ignore
    def folder_id(self) -> Optional[str]:
        """
        The id of the folder to open when opening this volume.
        """
        return self.__folder_id

    @folder_id.setter
    def folder_id(self, id_) -> None:
        self.__folder_id = str(id_) if id_ is not None else None

    @property  # type: ignore
    def file_system_name(self) -> str:
        """
        The unique name of this volume's file system (a FileSystem object). Defaults to the 'root' file system
        (DEFAULT_FILE_SYSTEM). Has the same value as the type attribute.
        """
        return self.__file_system_name

    @file_system_name.setter  # type: ignore
    def file_system_name(self, file_system_name: str) -> None:
        self.__file_system_name = str(file_system_name) if file_system_name is not None else DEFAULT_FILE_SYSTEM

    @property  # type: ignore
    def file_system_type(self) -> str:
        """
        The type name of this volume's file system (a FileSystem object). Defaults to a 'root' file system
        that is for HEA REST APIs that don't have a volume.
        """
        return self.__file_system_type

    @file_system_type.setter  # type: ignore
    def file_system_type(self, file_system_type: str) -> None:
        self.__file_system_type = str(file_system_type) if file_system_type is not None else MongoDBFileSystem.get_type_name()

    @property  # type: ignore
    def credentials_id(self) -> Optional[str]:
        """
        The id of the current user's credentials needed to open this volume (a CredentialsView object), if any.
        """
        return self.__credentials_id

    @credentials_id.setter  # type: ignore
    def credentials_id(self, credentials_id: Optional[str]) -> None:
        self.__credentials_id = str(credentials_id) if credentials_id is not None else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def account_id(self) -> str | None:
        """Id of the heaobject.account.AccountView associated with this volume, if any."""
        return self.__account_id

    @account_id.setter
    def account_id(self, account_id: str | None):
        self.__account_id = str(account_id) if account_id is not None else None

    @property
    def type_display_name(self) -> str:
        return "Volume"


DEFAULT_FILE_SYSTEM = 'DEFAULT_FILE_SYSTEM'
