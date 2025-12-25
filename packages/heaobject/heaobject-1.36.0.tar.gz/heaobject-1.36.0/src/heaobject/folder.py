"""
Implementation of folder and item objects as they would appear in a traditional operating system's file system. Folders
are directories in a file system. Items are views of a desktop object and are returned in place of the object in
requests for a folder's items. This is done so that requests for a folder's items return a list of desktop objects
that are all the same type. Items are also intended to be lightweight objects that can be retrieved quickly. Use the
item's actual_object_* properties to get the actual desktop object.

Folder and Item objects have a path attribute representing the absolute path to that object within a volume. See the
documentation for the HasPath class below for more details.

There is a base Folder class, which you can use directly. You can also subclass Folder to support different file
systems where folders may have extra attributes or attributes with special validation logic.

HEA microservices for folders must at least support read-only requests for folders and a folder's items.
Microservices may also support create and delete requests, moving a folder and its contents, copying a folder and its
contents, or updating a folder's attributes other than its path. Any copy, move, update, or delete requests for an
item must also affect the corresponding desktop object.
"""

import abc

from .project import AWSS3Project
from .root import AbstractDesktopObject, HasSize
from .data import DataObject, SameMimeType
from .aws import S3StorageClassDetailsMixin, s3_uri, S3_URI_PATTERN, S3_URI_BUCKET_PATTERN, S3Object, S3EventLiteral
from .awss3key import is_folder, KeyDecodeException, encode_key, decode_key
from .root import desktop_object_type_for_name, View, is_desktop_object_type
from .data import AWSS3FileObject
from .bucket import AWSBucket
from .mimetype import DEFAULT_MIME_TYPE as _DEFAULT_MIME_TYPE
from .decorators import attribute_metadata
from typing import Optional, get_args, TYPE_CHECKING


class HasPath(abc.ABC):
    """
    A mixin that adds a path attribute to a class. A path is the absolute path of an object within a volume as if it
    were stored in a tradition filesystem with folders and files. The volume is not part of the path. Paths are
    Unix-style, with paths separated by forward slashes. Folder absolute paths must have a trailing forward slash.
    Microservices must not permit changes to a folder or item's path other than via move and copy operations.
    """

    PATH_SEPARATOR = '/'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__path: str | None = None

    @property
    def path(self) -> str | None:
        """
        The absolute path to the object, including itself, within a volume. The absolute path uses a forward slash
        separator, it always begins with a forward slash, and if the object is a folder or a view of a folder, it
        always ends with a forward slash.
        """
        return self.__path

    @path.setter
    def path(self, path: str | None):
        path_ = str(path) if path is not None else None
        if path_ is not None:
            if not path_.startswith(self.PATH_SEPARATOR):
                raise ValueError(f'Invalid path {path}')
            if self.__is_folder and not path_.endswith(self.PATH_SEPARATOR):
                raise ValueError(f'Folder path should end with a slash but was {path}')
            if not self.__is_folder and path_.endswith(self.PATH_SEPARATOR):
                raise ValueError(f'Non-folder path not end with a slash but was {path}')
        self.__path = path_

    @property
    def __is_folder(self):
        """
        Read-only attribute that returns whether the object is a folder or a view of a folder.
        """
        if isinstance(self, Folder):
            return True
        elif isinstance(self, View):
            assert self.actual_object_type_name is not None, 'actual_object_type_name is None'  # type: ignore[attr-defined]
            return is_desktop_object_type(self.actual_object_type_name, type_=Folder)
        else:
            return False


class S3HasPath(HasPath):
    """
    Mixin that customizes the path attribute for S3 objects. Assumes the object has a bucket_id attribute.
    """

    if TYPE_CHECKING:
        @property
        def bucket_id(self) -> Optional[str]:
            pass
        @bucket_id.setter
        def bucket_id(self, bucket_id: Optional[str]):
            pass

        @property
        def key(self) -> Optional[str]:
            pass
        @key.setter
        def key(self, key: Optional[str]):
            pass

    @property
    def path(self) -> Optional[str]:
        """
        The folder object's key. Setting this attribute will also set the key, name, and id properties.
        """
        if self.bucket_id is None:
            return None
        try:
            return f'/{self.bucket_id}/{self.key}'
        except AttributeError:  # Assume the key attribute is missing, which is expected for buckets.
            return f'/{self.bucket_id}'

    @path.setter
    def path(self, path: Optional[str]):
        if path is not None:
            if not path.startswith('/'):
                raise ValueError(f'Invalid path {path}')
            path_as_list = path.split(self.PATH_SEPARATOR)
            self.bucket_id = path_as_list[1]
            try:
                self.key = self.PATH_SEPARATOR.join(path_as_list[2:])
            except KeyDecodeException as e:
                raise ValueError(f'Invalid path {path}') from e
        else:
            self.bucket_id = None
            self.key = None


class Folder(DataObject, SameMimeType, HasPath):
    """
    Represents a directory in the HEA desktop.

    The id "root" is reserved for the root folder of a volume or volume-like object, like an AWS S3 bucket. There is no
    root folder class, but it functions as a view of the volume or volume-like object.
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def get_mime_type(cls) -> str:
        """
        Returns the mime type of instances of the Folder class.

        :return: application/x.folder
        """
        return 'application/x.folder'

    @property
    def mime_type(self) -> str:
        """
        Read-only. Always returns 'application/x.folder'.
        """
        return type(self).get_mime_type()

    @property
    def type_display_name(self) -> str:
        return "Folder"


class AWSS3Folder(Folder, S3Object, S3HasPath):
    """
    Represents folders stored in AWS S3. AWSS3Folders may be either zero-size objects with a key that ends in a slash
    or a virtual object that is generated by HEA to mimic the behavior of a file system with hierarchical folders.
    Business logic for managing S3 folders may support modifying folders, which must be implemented as a copy followed
    by a delete operation of the folder object itself (if it exists on physical storage) and all its contents.
    """

    @property
    def id(self) -> Optional[str]:
        """
        The unique id of the folder among all folders in a bucket. The id is expected to be the folder's base
        64-encoded key. Setting this attribute will also set the name, path, and key properties.

        :raises ValueError: if the id cannot be decoded to a valid S3 key.
        """
        key_ = self.key
        return encode_key(key_) if key_ else None

    @id.setter
    def id(self, id_: Optional[str]):
        try:
            self.key = decode_key(id_) if id_ is not None else None
        except KeyDecodeException as e:
            raise ValueError(f'Invalid id {id_}') from e

    @property
    def name(self) -> Optional[str]:
        """
        The unique name of the folder among all folders in a bucket. The name is expected to be the folder's base 64-
        encoded key. Setting this attribute will also set the id, path, and key properties.

        :raises ValueError: if the name cannot be decoded to a valid S3 key.
        """
        key_ = self.key
        return encode_key(key_) if key_ else None

    @name.setter
    def name(self, name: Optional[str]):
        try:
            self.key = decode_key(name) if name is not None else None
        except KeyDecodeException as e:
            raise ValueError(f'Invalid name {name}') from e

    @property
    def key(self) -> Optional[str]:
        """
        The folder's key.
        """
        try:
            return self.__key
        except AttributeError:
            self.__key: str | None = None
            return self.__key

    @key.setter
    def key(self, key: Optional[str]):
        if key is not None:
            if not key.endswith('/'):
                raise ValueError('key is not a folder key (it does not end with a /)')
            self.__key = key
            key_: str | None = self.__key.rstrip('/')
            if key_ is not None:
                self.__display_name: str | None = key_.rsplit('/', maxsplit=1)[-1]
            else:
                self.__display_name = None

    @property
    def display_name(self) -> str:
        """
        The object's display name. It's the last part of the object's key, minus the trailing slash.
        """
        try:
            result = self.__display_name
        except AttributeError:
            self.__display_name = None
            result = self.__display_name
        return result if result is not None else super().display_name  # type: ignore

    @display_name.setter
    def display_name(self, display_name: str):
        if display_name is not None:
            if '/' in display_name:
                raise ValueError(f'display_name {display_name} cannot contain slashes')
            try:
                key = self.__key
            except AttributeError:
                key = None
            if key is not None:
                key_rsplit = key[:-1].rsplit('/', 1)
                if len(key_rsplit) > 1:
                    key = key_rsplit[-2] + f'/{display_name}/' if len(key_rsplit) > 1 else f'{display_name}/'
                else:
                    key = f'{display_name}/'
            else:
                key = f'{display_name}/'
            self.key = key

    @property
    def s3_uri(self) -> Optional[str]:
        """
        The object's S3 URI, computed from the bucket id and the id field.
        """
        return s3_uri(self.bucket_id, self.key)


class Item(AbstractDesktopObject, View, HasPath, HasSize):
    """
    Represents an item in a folder.
    """

    DEFAULT_MIME_TYPE = _DEFAULT_MIME_TYPE

    def __init__(self) -> None:
        super().__init__()
        self.__folder_id: Optional[str] = None
        self.__volume_id: Optional[str] = None
        self.__mime_type = type(self).DEFAULT_MIME_TYPE

    @property
    def folder_id(self) -> Optional[str]:
        """
        The id of this item's folder.
        """
        return self.__folder_id

    @folder_id.setter
    def folder_id(self, folder_id: Optional[str]) -> None:
        self.__folder_id = str(folder_id) if folder_id is not None else None

    @property
    def volume_id(self) -> Optional[str]:
        """
        The id of this item's volume.
        """
        return self.__volume_id

    @volume_id.setter
    def volume_id(self, volume_id: Optional[str]) -> None:
        self.__volume_id = str(volume_id) if volume_id is not None else None

    @property
    def mime_type(self) -> str:
        """The mime type of the file."""
        return self.__mime_type

    @mime_type.setter
    def mime_type(self, mime_type: str) -> None:
        if mime_type is None:
            self.__mime_type = type(self).DEFAULT_MIME_TYPE
        else:
            self.__mime_type = str(mime_type)



class AWSS3Item(Item, S3StorageClassDetailsMixin, S3HasPath, abc.ABC):
    @property
    @abc.abstractmethod
    def s3_uri(self) -> str | None:
        pass

    @s3_uri.setter
    @abc.abstractmethod
    def s3_uri(self, s3_uri: str | None):
        pass

    @property
    def bucket_id(self) -> Optional[str]:
        """
        The object's bucket name.
        """
        try:
            return self.__bucket_id
        except AttributeError:
            self.__bucket_id: str | None = None
            return self.__bucket_id

    @bucket_id.setter
    def bucket_id(self, bucket_id: Optional[str]):
        self.__bucket_id = bucket_id


class SearchItem(Item, abc.ABC):
    def __init__(self) -> None:
        super().__init__()
        self.__context_dependent_object_path: list[str] = []

    @property
    def context_dependent_object_path(self) -> list[str]:
        return list(self.__context_dependent_object_path)

    @context_dependent_object_path.setter
    def context_dependent_object_path(self, value: list[str]):
        if value is None:
            self.context_dependent_object_path = []
        elif not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError("context_dependent_object_path must be a list of strings")
        else:
            self.__context_dependent_object_path = [str(i) for i in value]


class AWSS3SearchItem(SearchItem, AWSS3Item, abc.ABC):
    pass

class AWSS3BucketItem(AWSS3Item):

    def __init__(self) -> None:
        super().__init__()
        self.__actual_object_type_name: str | None = None

    @property
    def id(self) -> Optional[str]:
        return self.bucket_id

    @id.setter
    def id(self, id_: Optional[str]):
        self.bucket_id = id_

    @property
    def name(self) -> Optional[str]:
        return self.bucket_id

    @name.setter
    def name(self, name: Optional[str]):
        self.bucket_id = name

    @property
    def display_name(self) -> str:
        _bucket_id = self.bucket_id
        if _bucket_id is not None:
            return _bucket_id
        else:
            # https://github.com/python/mypy/issues/8085
            return AWSS3Item.display_name.fget(self)  # type:ignore

    @display_name.setter
    def display_name(self, display_name: str):
        self.bucket_id = display_name

    @property
    def s3_uri(self) -> Optional[str]:
        """
        The object's S3 URI, computed from the bucket id field or set with this attribute.
        """
        return s3_uri(self.bucket_id)

    @s3_uri.setter
    def s3_uri(self, s3_uri: Optional[str]):
        match = S3_URI_BUCKET_PATTERN.fullmatch(s3_uri) if s3_uri else None
        if match:
            bucket_and_key = match.groupdict()
            self.bucket_id = bucket_and_key['bucket']
        elif s3_uri is not None:
            raise ValueError(f'Invalid s3 bucket URI {s3_uri}')
        else:
            self.bucket_id = None

    @property
    def actual_object_type_name(self) -> Optional[str]:
        return self.__actual_object_type_name

    @actual_object_type_name.setter
    def actual_object_type_name(self, actual_object_type_name: Optional[str]):
        if actual_object_type_name:
            desktop_object_type_for_name(actual_object_type_name, type_=AWSBucket)
            self.__actual_object_type_name = actual_object_type_name
        else:
            self.__actual_object_type_name = None

    @property
    def type_display_name(self) -> str:
        return "AWS S3 Bucket"


class AWSS3ItemInFolder(AWSS3Item):
    """
    Represents items stored in AWS S3 contained within a folder.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__type_display_name: str | None = None
        self.__actual_object_type_name: str | None = None

    @property
    def id(self) -> Optional[str]:
        key_ = self.key
        return encode_key(key_) if key_ else None

    @id.setter
    def id(self, id_: Optional[str]):
        try:
            self.key = decode_key(id_) if id_ is not None else None
        except KeyDecodeException as e:
            raise ValueError(f'Invalid id {id_}') from e

    @property
    def name(self) -> Optional[str]:
        key_ = self.key
        return encode_key(key_) if key_ else None

    @name.setter
    def name(self, name: Optional[str]):
        try:
            self.key = decode_key(name) if name is not None else None
        except KeyDecodeException as e:
            raise ValueError(f'Invalid name {name}') from e

    @property
    def key(self) -> Optional[str]:
        """
        The object's key.
        """
        try:
            return self.__key
        except AttributeError:
            self.__key: str | None = None
            return self.__key

    @key.setter
    def key(self, key: Optional[str]):
        if key:
            self.__key = key
            if self.__key is not None and is_folder(self.__key):
                key_: str | None = self.__key.strip('/')
            else:
                key_ = self.__key
            if key_ is not None:
                self.__display_name: str | None = key_.rsplit('/', maxsplit=1)[-1]
            else:
                self.__display_name = None
        else:
            self.__display_name = None

    @property
    def display_name(self) -> str:
        """
        The object's display name. It's the last part of the object's key, minus any trailing slash for folders.
        Setting this attribute will make this item a file.
        """
        try:
            result = self.__display_name
        except AttributeError:
            self.__display_name = None
            result = self.__display_name
        # https://github.com/python/mypy/issues/8085
        return result if result is not None else AWSS3Item.display_name.fget(self)  # type: ignore

    @display_name.setter
    def display_name(self, display_name: str):
        if display_name is not None:
            if '/' in display_name:
                raise ValueError(f'display_name {display_name} cannot contain slashes')
            try:
                key = self.__key
                old_key = key
            except AttributeError:
                key = None
                old_key = None
            key_end_part = f'{display_name}/' if self.actual_object_type_name and issubclass(
                desktop_object_type_for_name(self.actual_object_type_name), AWSS3Folder) else f'{display_name}'
            if key is not None:
                key_rsplit = key[:-1].rsplit('/', 1)
                if len(key_rsplit) > 1:
                    key = key_rsplit[-2] + f'/{key_end_part}' if len(key_rsplit) > 1 else key_end_part
                else:
                    key = f'{key_end_part}'
            else:
                key = f'{key_end_part}'
            if old_key and old_key.endswith('/'):
                self.key = key + '/' if not key.endswith('/') else ''
            else:
                self.key = key

    @property
    def s3_uri(self) -> Optional[str]:
        """
        The object's S3 URI, computed from the bucket id and the id field.
        """
        return s3_uri(self.bucket_id, self.key)

    @s3_uri.setter
    def s3_uri(self, s3_uri: Optional[str]):
        """
        The object's S3 URI, computed from the bucket id and the id field.
        """
        match = S3_URI_PATTERN.fullmatch(s3_uri) if s3_uri else None
        if match:
            bucket_and_key = match.groupdict()
            self.bucket_id = bucket_and_key['bucket']
            self.key = bucket_and_key['key']
        elif s3_uri is not None:
            raise ValueError(f'Invalid s3 URI {s3_uri}')
        else:
            self.bucket_id = None
            self.key = None

    @property
    def actual_object_type_name(self) -> Optional[str]:
        return self.__actual_object_type_name

    @actual_object_type_name.setter
    def actual_object_type_name(self, actual_object_type_name: Optional[str]):
        if actual_object_type_name:
            type_ = desktop_object_type_for_name(actual_object_type_name)
            if issubclass(type_, (AWSS3Folder, AWSS3Project)):
                key = self.key
                if key and not key.endswith('/'):
                    self.key = key + '/'
            elif issubclass(type_, AWSS3FileObject):
                key = self.key
                if key and key.endswith('/'):
                    self.key = key[:-1]
            else:
                raise TypeError(f'Type must be {AWSS3Folder}, {AWSS3Project}, or {AWSS3FileObject} but was {type_}')
            self.__actual_object_type_name = actual_object_type_name
        else:
            key = self.key
            if key and key.endswith('/'):
                self.key = key[:-1]
            self.__actual_object_type_name = None

    @property
    def type_display_name(self) -> str:
        if self.__type_display_name is not None:
            return self.__type_display_name
        if (actual := self.actual_object_type_name) is not None:
            return desktop_object_type_for_name(actual).__name__
        else:
            return 'Folder Item'

    @type_display_name.setter
    def type_display_name(self, type_display_name: str):
        self.__type_display_name = str(type_display_name) if type_display_name is not None else None


class  AWSS3SearchItemInFolder(AWSS3ItemInFolder, AWSS3SearchItem ):
    def __init__(self) -> None:
        super().__init__()
        self.__is_delete_marker: bool | None = None
        self.__version_id: str | None = None
        self.__account_id: str | None = None
        self.__event_name: S3EventLiteral | None = None

    @property
    def is_delete_marker(self) -> bool | None:
        """
        is_delete_marker signifies if the object has been deleted if true
        :return: delete marker flag
        """
        return self.__is_delete_marker

    @is_delete_marker.setter
    def is_delete_marker(self, is_delete_marker: bool):
        """
        Sets the flag is_delete_marker for the search item.

        :param value: A boolean of the state of the delete marker.
        """
        self.__is_delete_marker = is_delete_marker


    @property
    def version_id(self) -> str | None:
        """
        Retrieves the version ID of the S3 object associated with the search item.

        :return: The version ID as a string, or None if not set.
        """
        return self.__version_id

    @version_id.setter
    def version_id(self, value):
        """
        Sets the version ID for the search item.

        :param value: A string representing the version ID.
        """
        self.__version_id = value if value else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def account_id(self) -> str | None:
        """
        Retrieves the account ID associated with the S3 object.

        :return: The account ID as a string, or None if not set.
        """
        return self.__account_id

    @account_id.setter
    def account_id(self, value):
        """
        Sets the account ID for the search item.

        :param value: A string representing the account ID.
        """
        self.__account_id = value if value else None

    @property
    def event_name(self) -> S3EventLiteral | None:
        """Returns the bucket region"""
        return self.__event_name

    @event_name.setter
    def event_name(self, event_name: S3EventLiteral | None ) -> None:
        """Sets the bucket region"""
        if event_name is not None:
            event_name_ = str(event_name)
            literal_args = get_args(S3EventLiteral)
            if event_name_ not in literal_args:
                raise ValueError(f'Invalid event name {event_name_}; allowed values are {literal_args}')
        self.__event_name = event_name

class AWSS3FolderMetadata(AbstractDesktopObject):
    def __init__(self) -> None:
        super().__init__()
        self.__bucket_id: str | None = None
        self.__encoded_key: str | None = None
        self.__parent_folder_encoded_key: str | None = None
        self.__actual_object_type_name: str | None = None

    @property
    def bucket_id(self) -> Optional[str]:
        """
        The object's bucket name.
        """
        return self.__bucket_id

    @bucket_id.setter
    def bucket_id(self, bucket_id: Optional[str]):
        self.__bucket_id = str(bucket_id) if bucket_id is not None else None

    @property
    def encoded_key(self) -> str | None:
        """
        The object's encoded key.
        """
        return self.__encoded_key

    @encoded_key.setter
    def encoded_key(self, encoded_key: str | None):
        self.__encoded_key = str(encoded_key) if encoded_key is not None else None

    @property
    def parent_folder_encoded_key(self) -> str | None:
        """
        The encoded key of the object's parent folder, or None to represent the
        root folder of a bucket.
        """
        return self.__parent_folder_encoded_key

    @parent_folder_encoded_key.setter
    def parent_folder_encoded_key(self, parent_folder_encoded_key: str | None):
        self.__parent_folder_encoded_key = str(parent_folder_encoded_key) if parent_folder_encoded_key is not None else None

    @property
    def actual_object_type_name(self) -> str | None:
        return self.__actual_object_type_name

    @actual_object_type_name.setter
    def actual_object_type_name(self, actual_object_type_name: str | None):
        self.__actual_object_type_name = str(actual_object_type_name) if actual_object_type_name is not None else None
