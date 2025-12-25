from heaobject.data import DataObject, SameMimeType
from heaobject.aws import S3Object, s3_uri
from heaobject.awss3key import KeyDecodeException, decode_key, encode_key
from typing import final


class Project(DataObject, SameMimeType):
    """
    Represents a project on the HEA desktop.
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def get_mime_type(cls) -> str:
        """
        Returns the mime type of instances of the Project class.

        :return: application/x.project
        """
        return 'application/x.project'

    @property
    def mime_type(self) -> str:
        """
        Read-only. Always returns 'application/x.project'.
        """
        return type(self).get_mime_type()

    @property
    def type_display_name(self) -> str:
        return 'Project'


class AWSS3Project(Project, S3Object):
    """
    Represents folders stored in AWS S3. Microservices that manage S3 folders may support modifying folders, in which
    case they must only allow updating the folder's display name, which the microservice must implement as a copy
    operation. Changing a folder's path may only be implemented as a move request, which the microservice again must
    implement as a copy followed by a delete.
    """

    @property
    def id(self) -> str | None:
        """
        The unique id of the folder among all folders in a bucket. The id is expected to be the folder's base
        64-encoded key. Setting this attribute will also set the name, path, and key properties.

        :raises ValueError: if the id cannot be decoded to a valid S3 key.
        """
        key_ = self.key
        return encode_key(key_) if key_ else None

    @id.setter
    def id(self, id: str | None):
        try:
            self.key = decode_key(id) if id is not None else None
        except KeyDecodeException as e:
            raise ValueError(f'Invalid id {id}') from e

    @property
    def name(self) -> str | None:
        """
        The unique name of the folder among all folders in a bucket. The name is expected to be the folder's base 64-
        encoded key. Setting this attribute will also set the id, path, and key properties.

        :raises ValueError: if the name cannot be decoded to a valid S3 key.
        """
        key_ = self.key
        return encode_key(key_) if key_ else None

    @name.setter
    def name(self, name: str | None):
        try:
            self.key = decode_key(name) if name is not None else None
        except KeyDecodeException as e:
            raise ValueError(f'Invalid name {name}') from e

    @property
    def key(self) -> str | None:
        """
        The folder's key.
        """
        try:
            return self.__key
        except AttributeError:
            self.__key: str | None = None
            return self.__key

    @key.setter
    def key(self, key: str | None):
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
    def s3_uri(self) -> str | None:
        """
        The object's S3 URI, computed from the bucket id and the id field.
        """
        return s3_uri(self.bucket_id, self.key)
