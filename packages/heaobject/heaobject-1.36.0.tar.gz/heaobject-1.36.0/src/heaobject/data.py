"""
This module contains HEA objects supporting items that are openable in the HEA desktop, called data objects (DataObject
below). HEA uses internet MIME types to provide additional information about the type of data in a DataObject. You can
read more about MIME types at https://www.iana.org/assignments/media-types/media-types.xhtml and
https://en.wikipedia.org/wiki/Media_type.

HEA defines the following custom MIME types that are intended only for internal use by the different parts of HEA:

application/x.folder: HEA folders (heaobject.folder.Folder)
application/x.item: HEA items (heaobject.folder.Item)
application/x.data-in-database: Data in a database (heaobject.data.DataInDatabase)
"""

from .root import TagsMixin
from . import root
from .awss3key import is_folder, KeyDecodeException, encode_key, decode_key
from abc import ABC, abstractmethod
from typing import Any, Optional
from humanize import naturalsize
from .mimetype import get_description, DEFAULT_MIME_TYPE as _DEFAULT_MIME_TYPE

from .aws import S3StorageClassDetailsMixin, s3_uri, S3_URI_PATTERN, S3Object


class DataObject(root.AbstractDesktopObject, ABC):
    """
    Interface for data objects, which are objects that are openable in the HEA desktop. The main difference between
    openable and other objects is the addition of two properties: a MIME type attribute, and an attribute containing a
    list of the MIME types that the object supports providing when it is opened.
    """

    @property
    @abstractmethod
    def mime_type(self) -> str:
        """
        The object's MIME type. Note that HEA uses '*/x.*' for all HEA-specific private
        MIME types that only need to be understood by the different parts of HEA, such as 'application/x.folder' for
        folders.
        """
        pass


class VersionedDataObject(DataObject, root.AbstractVersionedDesktopObject, ABC):
    """
    Interface for versioned data objects, which are objects that are openable in the HEA desktop and can have versions.
    The main difference between openable and other objects is the addition of two properties: a MIME type attribute,
    and an attribute containing a list of the MIME types that the object supports providing when it is opened.
    """
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """
        The object's MIME type. Note that HEA uses '*/x.*' for all HEA-specific private
        MIME types that only need to be understood by the different parts of HEA, such as 'application/x.folder' for
        folders.
        """
        pass


class SameMimeType(ABC):
    """
    Interface to add to DataObject classes in which instances always have the same mime type.
    """
    @classmethod
    @abstractmethod
    def get_mime_type(cls) -> str:
        """
        Returns the mime type of instances of the data class implementing this interface.

        :return: a mime type string.
        """
        pass


class DataFile(VersionedDataObject, root.HasSize):
    """
    Represents files on a file system.
    """

    DEFAULT_MIME_TYPE = _DEFAULT_MIME_TYPE

    def __init__(self):
        """
        Creates a file object.
        """
        super().__init__()
        self.__mime_type = DataFile.DEFAULT_MIME_TYPE

    @property
    def mime_type(self) -> str:
        """The mime type of the file."""
        return self.__mime_type

    @mime_type.setter
    def mime_type(self, mime_type: str) -> None:
        if mime_type is None:
            self.__mime_type = DataFile.DEFAULT_MIME_TYPE
        else:
            self.__mime_type = str(mime_type)

    @property
    def type_display_name(self) -> str:
        return get_type_display_name(self.mime_type)


class AWSS3FileObject(DataFile, S3Object, S3StorageClassDetailsMixin, TagsMixin):
    """
    Represents files stored in AWS S3.
    """

    @property
    def id(self) -> Optional[str]:
        """
        The unique id of the file object. It is computed from the key, and
        setting it sets the key.
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
        The unique name of the file object. It is the same as the id. It is
        computed from the key, and setting it sets the key.
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

    @property
    def display_name(self) -> str:
        """
        The object's display name. It's the last part of the object's key.
        It is computed from the key, and setting the display name updates the
        key. Passing a None value into this attribute does nothing.
        """
        key = self.key
        if key is not None and is_folder(key):
            key = key.strip('/')
        if key is not None:
            return key.rsplit('/', maxsplit=1)[-1]
        else:
            return super().display_name

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
                key_rsplit = key.rsplit('/', 1)
                if len(key_rsplit) > 1:
                    key = key_rsplit[-2] + f'/{display_name}' if len(key_rsplit) > 1 else display_name
                else:
                    key = f'{display_name}'
            else:
                key = f'{display_name}'
            self.key = key

    @property
    def s3_uri(self) -> Optional[str]:
        """
        The object's S3 URI, computed from the bucket id and the key field.
        """
        return s3_uri(self.bucket_id, self.key)


class DataInDatabase(DataObject, SameMimeType):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_mime_type(cls) -> str:
        """
        Returns the mime type of instances of the DataInDatabase class.

        :return: application/x.data-in-database
        """
        return 'application/x.data-in-database'

    @property
    def mime_type(self) -> str:
        """Read-only. The mime type for DataInDatabase objects, application/x.data-in-database."""
        return type(self).get_mime_type()

    @property
    def type_display_name(self) -> str:
        return "Data in Database"


class ClipboardData(DataObject):
    """
    Represents data to place on the client device's clipboard. While the class
    stores the data as a bytes object, when dumped as json the data is encoded
    as a base 64-encoded string. As a result, the client will need to decode
    the data back into its original form.
    """
    DEFAULT_MIME_TYPE = 'application/octet-stream'

    def __init__(self) -> None:
        super().__init__()
        self.__mime_type = ClipboardData.DEFAULT_MIME_TYPE
        self.__data: Any = None

    @property
    def mime_type(self) -> str:
        return self.__mime_type

    @mime_type.setter
    def mime_type(self, mime_type: str):
        self.__mime_type = str(mime_type) if mime_type is not None else ClipboardData.DEFAULT_MIME_TYPE

    @property
    def data(self) -> Any:
        """
        The data to put on the clipboard. The type of data must be that of the mime_type attribute.
        """
        return self.__data

    @data.setter
    def data(self, data: Any):
        self.__data = data

    @property
    def type_display_name(self) -> str:
        return "Clipboard Data"



def get_type_display_name(mime_type: str) -> str:
    result = get_description(mime_type)
    if result is None and mime_type != DataFile.DEFAULT_MIME_TYPE:
        result = mime_type
    return result if result is not None else 'Data File'
