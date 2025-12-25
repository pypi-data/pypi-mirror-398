from typing import Optional, get_args, final

from .attribute import IdAttribute, IdListWithBackingSetAttribute
from .util import parse_bool
from .data import DataObject, SameMimeType
from .root import AbstractDesktopObject, TagsMixin, Permission, View
from abc import ABC
from .aws import s3_uri, RegionLiteral, AWSDesktopObject
from .decorators import attribute_metadata
import logging


class Bucket(DataObject, ABC):
    """
    Abstract base class for user accounts.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__size: Optional[float] = None
        self.__object_count: Optional[int] = None
        self.__collaborator_ids: list[str] = []

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

    @property
    def id(self) -> Optional[str]:
        return self.bucket_id

    @id.setter
    def id(self, id: Optional[str]):
        self.bucket_id = id

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
            return DataObject.display_name.fget(self)  # type:ignore

    @display_name.setter
    def display_name(self, display_name: str):
        self.bucket_id = display_name

    @property
    def collaborator_ids(self) -> list[str]:
        return list(self.__collaborator_ids)

    @collaborator_ids.setter
    def collaborator_ids(self, collaborator_ids: list[str]):
        if collaborator_ids is None:
            self.__collaborator_ids = []
        elif not isinstance(collaborator_ids, str):
            self.__collaborator_ids = [str(i) for i in collaborator_ids]
        else:
            self.__collaborator_ids = [str(collaborator_ids)]

    @property
    def size(self) -> Optional[float]:
        """Returns the bucket size"""
        return self.__size

    @size.setter
    def size(self, size: float) -> None:
        """Sets the bucket size"""
        self.__size = float(size) if size is not None else None

    @property
    def object_count(self) -> Optional[int]:
        """Returns the number of objects in the bucket"""
        return self.__object_count

    @object_count.setter
    def object_count(self, object_count: int) -> None:
        """Sets the number of objects in the bucket"""
        self.__object_count = int(object_count) if object_count is not None else None

    def add_collaborator_id(self, collaborator_id: str):
        self.__collaborator_ids.append(str(collaborator_id))

    def remove_collaborator_id(self, collaborator_id: str):
        self.__collaborator_ids.remove(str(collaborator_id))


class BucketCollaborators(AbstractDesktopObject, View):
    """
    View of a bucket with its collaborators and limited other metadata.
    """
    collaborator_ids = IdListWithBackingSetAttribute(doc='The ids of the collaborators with access to this bucket.')
    bucket_id = IdAttribute(doc='The id of the bucket.')

    def __init__(self) -> None:
        super().__init__()

    @property
    def id(self) -> Optional[str]:
        return self.bucket_id

    @id.setter
    def id(self, id: Optional[str]):
        self.bucket_id = id

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
            return AbstractDesktopObject.display_name.fget(self)  # type:ignore

    @display_name.setter
    def display_name(self, display_name: str):
        self.bucket_id = display_name

    def add_collaborator_id(self, collaborator_id: str):
        type(self).collaborator_ids.add(self, str(collaborator_id))

    def remove_collaborator_id(self, collaborator_id: str):
        type(self).collaborator_ids.remove(self, str(collaborator_id))


class AWSBucket(Bucket, AWSDesktopObject, SameMimeType, TagsMixin):
    """
    Represents an AWS Bucket in the HEA desktop. Contains functions that allow access and setting of the value.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__arn: Optional[str] = None
        self.__encrypted: Optional[bool] = None
        self.__versioned: Optional[bool] = None
        self.__locked: Optional[bool] = None
        self.__region: Optional[RegionLiteral] = None

    @property
    def s3_uri(self) -> Optional[str]:
        """
        The object's S3 URI, computed from the bucket id field or set with this attribute.
        """
        return s3_uri(self.bucket_id)

    @classmethod
    def get_mime_type(cls) -> str:
        """
        Returns the mime type for AWSBucket objects.

        :return: application/x.awsbucket
        """
        return 'application/x.awsbucket'

    @property
    def mime_type(self) -> str:
        """Read-only. The mime type for AWSBucket objects, application/x.awsbucket."""
        return self.get_mime_type()

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def arn(self) -> Optional[str]:
        """Returns the aws arn str for identifying resources on aws"""
        return self.__arn

    @arn.setter
    def arn(self, arn: Optional[str]) -> None:
        """Sets the numerical account identifier"""
        self.__arn = str(arn) if arn is not None else None

    @property
    def encrypted(self) -> Optional[bool]:
        """Returns the is encrypted flag for bucket"""
        return self.__encrypted

    @encrypted.setter
    def encrypted(self, encrypted: Optional[bool]) -> None:
        """Sets the is encrypted flag for bucket"""
        if encrypted is None:
            self.__encrypted = None
        elif isinstance(encrypted, bool):
            self.__encrypted = encrypted
        else:
            self.__encrypted = parse_bool(encrypted)  # type: ignore

    @property
    def versioned(self) -> Optional[bool]:
        """Returns the is versioned flag for bucket"""
        return self.__versioned

    @versioned.setter
    def versioned(self, versioned: Optional[bool]) -> None:
        """Sets the is versioned flag for bucket"""
        if versioned is None or isinstance(versioned, bool):
            self.__versioned = versioned
        else:
            self.__versioned = parse_bool(versioned)  # type: ignore

    @property
    def locked(self) -> Optional[bool]:
        """Returns the  flag that objects are 'locked' for bucket"""
        return self.__locked

    @locked.setter
    def locked(self, locked: Optional[bool]) -> None:
        """Sets the flag that objects are 'locked'"""
        if locked is None or isinstance(locked, bool):
            self.__locked = locked
        else:
            self.__locked = parse_bool(locked)  # type: ignore

    @property
    def region(self) -> Optional[RegionLiteral]:
        """Returns the bucket region"""
        return self.__region

    @region.setter
    def region(self, region: Optional[RegionLiteral]) -> None:
        """Sets the bucket region"""
        if region is not None:
            region_ = str(region)
            literal_args = get_args(RegionLiteral)
            if region_ not in literal_args:
                raise ValueError(f'Invalid region {region_}; allowed values are {literal_args}')
        self.__region = region

    @property
    def type_display_name(self) -> str:
        return 'AWS S3 Bucket'

    def dynamic_permission(self, sub: str) -> list[Permission]:
        """
        Returns permissions if the sub is in the member_ids list, or an empty list if not.

        :param sub: the user id (required).
        :return: A list containing Permissions or the empty list.
        """
        logger = logging.getLogger(__name__)
        try:
            perms: set[Permission] = set()
            for collaborator_id in self.collaborator_ids:
                if collaborator_id == sub:
                    perms.add(Permission.VIEWER)
                    break
            return list(perms)
        except:
            logger.exception('Permissions are not correctly configured...returning empty permissions set')
            return []

    @property
    def resource_type_and_id(self) -> str | None:
        """
        The object's Amazon Resource Name resource type and ID.
        """
        bucket_id = self.bucket_id
        return bucket_id if bucket_id else None
