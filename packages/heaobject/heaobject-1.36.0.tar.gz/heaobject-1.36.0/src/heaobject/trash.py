"""
Classes for HEA's trash facility. The trash is a location to delete desktop
objects where they can be put back later if the user realizes the deletion was
a mistake.
"""
from abc import ABC, abstractmethod

from yarl import URL
from heaobject.attribute import StrListAttribute
from heaobject.aws import S3_BUCKET_NAME_REGEX, S3_URI_PATTERN, AWSDesktopObject, s3_uri, S3StorageClassMixin
from heaobject.awss3key import KeyDecodeException, decode_key, encode_key, is_folder
from heaobject.data import AWSS3FileObject
from heaobject.decorators import AttributeMetadata
from heaobject.folder import AWSS3Folder, AWSS3Project
from .root import AbstractDesktopObject, HasSize, View, desktop_object_type_for_name
from datetime import date
from typing import Optional
from dateutil import parser as dateparser

class TrashItem(AbstractDesktopObject, View, ABC):
    """
    Abstract base class for trash items. Trash items are an alternative
    representation of the desktop object that was put in the trash.
    """

    parent_uris = StrListAttribute(disallow_empty_strings=True,
                                   doc='The ids of the parent containers of this trash item. If the object has a '
                                       'natural parent container, such as a folder, use that, otherwise use the '
                                       'object\'s account if any, otherwise use the object\'s collection.',
                                   attribute_metadata=AttributeMetadata(read_only=True))

    @abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.__deleted: date | None = None

    def add_parent_uri(self, parent_uri: str):
        """
        Adds a parent URI to the list of parent URIs.
        """
        type(self).parent_uris.add(self, parent_uri)

    def remove_parent_uri(self, parent_uri: str):
        """
        Removes a parent URI from the list of parent URIs.
        """
        type(self).parent_uris.remove(self, parent_uri)

    @property
    @abstractmethod
    def original_location(self) -> str | None:
        """
        The object's original location. The format of the location string is
        unique for different subclasses.
        """
        pass

    @original_location.setter
    @abstractmethod
    def original_location(self, original_location: str | None):
        pass

    @property
    def deleted(self) -> Optional[date]:
        """
        The date the deleted object was deleted (the date the objects' delete marker was created).
        """
        return self.__deleted


    @deleted.setter
    def deleted(self, deleted: date | None):
        if deleted is None or isinstance(deleted, date):
            self.__deleted = deleted
        else:
            self.__deleted = dateparser.isoparse(deleted) # TODO Use datetime.fromisoformat after we switch to python 3.11.

    @property
    def human_readable_original_location(self) -> str | None:
        """
        The object's original location in human readable form. By default, it
        mirrors the value of the original_location attribute.
        """
        return self.original_location

    @human_readable_original_location.setter
    def human_readable_original_location(self, human_readable_original_location: str | None):
        self.original_location = human_readable_original_location

    @property
    def type_display_name(self) -> str:
        return "Trash Item"


class InVolumeTrashItem(TrashItem, HasSize, ABC):
    """
    Abstract base class for trash items in a volume's trash.
    """
    PATH_SEPARATOR = '/'

    @abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.__volume_id: str | None = None

    @property
    def volume_id(self) -> str | None:
        """
        The id of this item's volume.
        """
        return self.__volume_id

    @volume_id.setter
    def volume_id(self, volume_id: str | None) -> None:
        self.__volume_id = str(volume_id) if volume_id is not None else None



class AWSS3FolderFileTrashItem(AWSDesktopObject, InVolumeTrashItem, S3StorageClassMixin):
    """
    Trash items from Amazon Web Services Simple Storage Service buckets. They are views of an S3 object, which
    represents a grouping of S3 object versions.
    @see: heaobject.aws.S3Object
    """

    def __init__(self) -> None:
        super().__init__()
        self.__version: str | None = None
        self.__actual_object_type_name: str | None = None
        self.__type_display_name: str | None = None
        self.__bucket_id: str | None = None

    @property
    def id(self) -> str | None:
        key_ = self.key
        version_ = self.version
        return encode_key(key_) + ',' + version_ if key_ and version_ else None

    @id.setter
    def id(self, id_: str | None):
        try:
            id__ = str(id_) if id_ is not None else None
            if id__ is not None and ',' not in id__:
                raise ValueError(f'Invalid value {id_}')
            key_, version_ = id__.split(',', 1) if id__ is not None else (None, None)
            self.key = decode_key(key_) if key_ is not None else None
            self.version = version_ if version_ is not None else None
        except KeyDecodeException as e:
            raise ValueError(f'Invalid value {id_}') from e

    @property
    def name(self) -> str | None:
        return self.id

    @name.setter
    def name(self, name: str | None):
        self.id = name

    @property
    def version(self) -> str | None:
        return self.__version

    @version.setter
    def version(self, version: str | None):
        self.__version = str(version) if version is not None else None

    @property
    def key(self) -> str | None:
        """
        The object's key.
        """
        try:
            return self.__key
        except AttributeError:
            self.__key: str | None = None
            return self.__key

    @key.setter
    def key(self, key: str | None):
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
        return result if result is not None else super().display_name  # type: ignore

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
    def s3_uri(self) -> str | None:
        """
        The object's S3 URI, computed from the bucket id and the id field.
        """
        return s3_uri(self.bucket_id, self.key)

    @s3_uri.setter
    def s3_uri(self, s3_uri: str | None):
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
    def bucket_id(self) -> Optional[str]:
        """
        The object's bucket name. The s3_uri field is computed from it.
        """
        return self.__bucket_id

    @bucket_id.setter
    def bucket_id(self, bucket_id: Optional[str]):
        if bucket_id is not None:
            bucket_id_ = str(bucket_id)
            if S3_BUCKET_NAME_REGEX.match(bucket_id_):
                self.__bucket_id = bucket_id_
            else:
                raise ValueError(f'Invalid bucket name {bucket_id}. See https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html for rules.')
        else:
            self.__bucket_id = None

    @property
    def actual_object_id(self) -> str | None:
        """
        Gets the id of the actual object in the trash. It is always the same
        as this object's id. Setting this attribute also sets the id attribute
        and vice versa.
        """
        key_ = self.key
        return encode_key(key_) if key_ is not None else None

    @actual_object_id.setter
    def actual_object_id(self, actual_object_id: str | None):
        self.key = decode_key(actual_object_id) if actual_object_id is not None else None

    @property
    def actual_object_type_name(self) -> str | None:
        return self.__actual_object_type_name

    @actual_object_type_name.setter
    def actual_object_type_name(self, actual_object_type_name: str | None):
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
    def original_location(self) -> str | None:
        return f'/{self.bucket_id}/{self.key}' if self.bucket_id and self.key else None

    @original_location.setter
    def original_location(self, original_location: str | None):
        if original_location is None:
            self.bucket_id = None
            self.key = None
        else:
            path_as_list = original_location.split(self.PATH_SEPARATOR)
            self.bucket_id = path_as_list[1]
            try:
                self.key = self.PATH_SEPARATOR.join(path_as_list[2:])
            except KeyDecodeException as e:
                raise ValueError(f'Invalid original location {original_location}') from e

    @property
    def type_display_name(self) -> str:
        if self.__type_display_name is not None:
            return self.__type_display_name
        if (actual := self.actual_object_type_name) is not None:
            return desktop_object_type_for_name(actual).__name__
        else:
            return 'Trash Item'

    @type_display_name.setter
    def type_display_name(self, type_display_name: str):
        self.__type_display_name = str(type_display_name) if type_display_name is not None else None

    @property
    def resource_type_and_id(self) -> str | None:
        """
        The object's Amazon Resource Name resource type and ID.
        """
        bucket_id = self.bucket_id
        key = self.key
        result = f"{bucket_id}/{key}" if bucket_id and key else None
        if result and (v := self.version) is not None:
            result += f'?versionId={v}'
        return result
