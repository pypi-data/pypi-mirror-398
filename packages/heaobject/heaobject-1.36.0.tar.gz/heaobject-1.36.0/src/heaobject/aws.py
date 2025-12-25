"""
Utility classes and functions for working with AWS.
"""
import abc
from heaobject import root
from typing import Literal, Optional
import re
from datetime import datetime
from .util import to_datetime
from .awss3key import KeyDecodeException, encode_key, decode_key
from .decorators import attribute_metadata


# Per https://stackoverflow.com/questions/50480924/regex-for-s3-bucket-name plus
# https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html.
# This disallows dots, which are in fact permitted unless you turn on S3 Transfer Acceleration.
S3_BUCKET_NAME_REGEX = re.compile(r'(?!(^xn--|^sthree-|^amzn-s3-demo|.+-s3alias$|.+--ol-s3$|.+\.mrap|.+--x-s3$|.+--table-s3))^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$')

class S3StorageClass(root.EnumWithDisplayName):
    """
    The S3 storage classes. The list of storage classes is documented at
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_objects_v2, and
    each storage class is explained in detail at
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html.
    """
    STANDARD = 'Standard'
    DEEP_ARCHIVE = 'Glacier Deep Archive'
    GLACIER = 'Glacier Flexible Retrieval'
    GLACIER_IR = 'Glacier Instant Retrieval'
    REDUCED_REDUNDANCY = 'Reduced Redundancy'
    ONEZONE_IA = 'One Zone-IA'
    STANDARD_IA = 'Standard-IA'
    INTELLIGENT_TIERING = 'Intelligent Tiering'
    OUTPOSTS = 'Outposts'

    @property
    def archive_storage_class(self) -> bool:
        """Whether the storage class is an archive storage class."""
        return self in (self.DEEP_ARCHIVE, self.GLACIER, self.GLACIER_IR)

    @property
    def requires_restore(self) -> bool:
        """Whether the storage class is immediately retrievable (False) or requires a restore (True)."""
        return self in (self.DEEP_ARCHIVE, self.GLACIER)

    @property
    def _default_archive_state(self) -> Optional['S3ArchiveDetailState']:
        """The default archive detail state for the storage class. None means undefined."""
        if self.archive_storage_class:
            if self.requires_restore:
                return None
            else:
                return S3ArchiveDetailState.ARCHIVED
        else:
            return S3ArchiveDetailState.NOT_ARCHIVED


class S3ArchiveDetailState(root.EnumWithDisplayName):
    """Detailed archive state of an S3 object."""

    NOT_ARCHIVED = 'Not Archived'
    ARCHIVED = 'Archived'
    RESTORING = 'Restoring'
    RESTORED = 'Restored'

    @property
    def retrievable(self) -> bool | None:
        """Whether the object is available for retrieval."""
        if self in (self.NOT_ARCHIVED, self.RESTORED):
            return True
        elif self in (S3ArchiveDetailState.ARCHIVED, S3ArchiveDetailState.RESTORING):
            return False
        else:
            return None


def s3_uri(bucket: str | None, key: str | None = None) -> str | None:
    """
    Creates and returns a S3 URI from the given bucket and key.

    :param bucket: a bucket name (optional).
    :param key: a key (optional).
    :return: None if the bucket is None, else a S3 URI string.
    """
    if not bucket:
        return None
    return f"s3://{bucket}/{key if key is not None else ''}"


S3_URI_PATTERN = re.compile(r's3://(?P<bucket>[^/]+?)/(?P<key>.+)')
S3_URI_BUCKET_PATTERN = re.compile(r's3://(?P<bucket>[^/]+?)/')


class S3StorageClassMixin:
    """
    Mixin for adding a storage class attribute and related methods to a desktop object.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__storage_class: S3StorageClass | None = None

    @property
    def storage_class(self) -> S3StorageClass | None:
        """The AWS S3 storage class of this file."""
        return self.__storage_class

    @storage_class.setter
    def storage_class(self, storage_class: S3StorageClass | None):
        if storage_class is None or isinstance(storage_class, S3StorageClass):
            storage_class = storage_class
        else:
            try:
                storage_class = S3StorageClass[str(storage_class)]
            except KeyError:
                raise ValueError(f'Invalid storage class {storage_class}')
        self.__storage_class = storage_class

    def set_storage_class_from_str(self, storage_class: Optional[str]):
        """
        Sets the storage class attribute to the storage class corresponding to the provided string.
        """
        if storage_class is None:
            self.storage_class = None
        else:
            try:
                self.storage_class = S3StorageClass[str(storage_class)]
            except KeyError:
                raise ValueError(f'Invalid storage class {storage_class}')

    @property
    def archive_storage_class(self) -> bool | None:
        """Whether or not the object's storage class is an archive storage class. None means undefined and is the
        default value."""
        storage_class = self.storage_class
        return storage_class.archive_storage_class if storage_class else None


class S3StorageClassDetailsMixin(S3StorageClassMixin):
    """
    Mixin for adding a storage class attribute to an S3 object, plus properties for indicating restore status and
    more.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__storage_class: S3StorageClass | None = None
        self.__archive_detail_state: S3ArchiveDetailState | None = None
        self.__available_until: datetime | None = None

    @property
    def storage_class(self) -> S3StorageClass | None:
        """The AWS S3 storage class of this file. Setting the storage class updates the archive_detail_state attribute
        to an appropriate value."""
        return self.__storage_class

    @storage_class.setter
    def storage_class(self, storage_class: S3StorageClass | None):
        if storage_class is None or isinstance(storage_class, S3StorageClass):
            storage_class = storage_class
        else:
            try:
                storage_class = S3StorageClass[str(storage_class)]
            except KeyError:
                raise ValueError(f'Invalid storage class {storage_class}')
        self.__storage_class = storage_class
        if storage_class:
            if not storage_class.archive_storage_class:
                self.archive_detail_state = S3ArchiveDetailState.NOT_ARCHIVED
            elif storage_class.requires_restore:
                self.archive_detail_state = None
            else:
                self.archive_detail_state = S3ArchiveDetailState.ARCHIVED

    @property
    def archive_detail_state(self) -> S3ArchiveDetailState | None:
        """The AWS S3 archive state of this object. None means undefined and is the default value. An attempt to set
        this attribute to None are ignored if the storage class is an archive storage class that does not require a
        restore."""
        return self.__archive_detail_state

    @archive_detail_state.setter
    def archive_detail_state(self, archive_detail_state: S3ArchiveDetailState | None):
        if archive_detail_state is None or isinstance(archive_detail_state, S3ArchiveDetailState):
            archive_detail_state_ = archive_detail_state
        else:
            try:
                archive_detail_state_ = S3ArchiveDetailState[str(archive_detail_state)]
            except KeyError:
                raise ValueError(f'Invalid archive detail state {archive_detail_state}')
        storage_class = self.storage_class
        if storage_class and storage_class.archive_storage_class and not storage_class.requires_restore:
            if not archive_detail_state_:
                return
            if archive_detail_state_ in (S3ArchiveDetailState.RESTORING, S3ArchiveDetailState.RESTORED):
                self.storage_class = None
        if archive_detail_state_  in (S3ArchiveDetailState.ARCHIVED, S3ArchiveDetailState.RESTORING, S3ArchiveDetailState.NOT_ARCHIVED):
            self.available_until = None
        if archive_detail_state_ is S3ArchiveDetailState.NOT_ARCHIVED and storage_class and \
            storage_class.archive_storage_class and storage_class.requires_restore:
            self.storage_class = None
        if archive_detail_state_ is not S3ArchiveDetailState.NOT_ARCHIVED and storage_class and not storage_class.archive_storage_class:
            self.storage_class = None
        self.__archive_detail_state = archive_detail_state_

    @property
    def human_readable_archive_detail_state(self) -> str:
        """A human-readable representation of the archive detail state."""
        archive_detail_state = self.archive_detail_state
        return str(archive_detail_state) if archive_detail_state else "Undefined"

    def set_archive_detail_state_from_str(self, archive_detail_state: Optional[str]):
        """
        Sets the archive detail state attribute to the archive detail state corresponding to the provided string.
        """
        if archive_detail_state is None:
            self.archive_detail_state = None
        else:
            try:
                self.archive_detail_state = S3ArchiveDetailState[str(archive_detail_state)]
            except KeyError:
                raise ValueError(f'Invalid archive detail state {archive_detail_state}')

    @property
    def retrievable(self) -> bool | None:
        """The AWS S3 retrieval availability of this object. None means undefined and is the default value."""
        storage_class = self.storage_class
        if not storage_class or storage_class.requires_restore:
            archive_detail_state = self.archive_detail_state
            return archive_detail_state.retrievable if archive_detail_state else None
        else:
            return True

    @property
    def available_until(self) -> datetime | None:
        """The datetime until which the object is available for retrieval. None means forever if the storage class is
        S3StorageClass.STANDARD, otherwise None is undefined. Setting available_until to a datetime value sets the
        archive detail state to S3ArchiveDetailState.RESTORED. If the storage class is not an archive class or is an
        archive class that does not support restores, the storage class is set to None."""
        return self.__available_until

    @available_until.setter
    def available_until(self, available_until: datetime | None):
        available_until = to_datetime(available_until)
        if available_until:
            storage_class = self.storage_class
            if storage_class:
                if not storage_class.archive_storage_class or not storage_class.requires_restore:
                    self.storage_class = None
            self.archive_detail_state = S3ArchiveDetailState.RESTORED
        self.__available_until = available_until


class AWSDesktopObject(root.DesktopObject, abc.ABC):
    """
    Marker interface for AWS object classes, such as
    heaobject.folder.AWSS3Folder and heaobject.data.AWSS3FileObject.
    """
    @property
    @abc.abstractmethod
    def resource_type_and_id(self) -> str | None:
        """The object's Amazon Resource Name resource type and ID."""
        pass


class S3Version(root.Version, AWSDesktopObject, S3StorageClassMixin):
    """
    Version information for S3 objects.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__key: Optional[str] = None
        self.__bucket_id: Optional[str] = None
        self.__display_name: Optional[str] = None

    @property
    def version_of_id(self) -> Optional[str]:
        """
        The unique id of the file object. It is computed from the key, and
        setting it sets the key.
        """
        key_ = self.key
        return encode_key(key_) if key_ else None

    @version_of_id.setter
    def version_of_id(self, id_: Optional[str]):
        try:
            self.key = decode_key(id_) if id_ is not None else None
        except KeyDecodeException as e:
            raise ValueError(f'Invalid id {id_}') from e

    @property
    def key(self) -> Optional[str]:
        """
        The object's key.
        """
        return self.__key

    @key.setter
    def key(self, key: Optional[str]):
        if key:
            self.__key = key

    @property
    def display_name(self) -> str:
        """
        The object's display name, by default in the form "Version <id>" where <id> is the value of the object's id
        attribute. Setting this attribute overrides the default display name behavior.
        """
        if self.__display_name is not None:
            return self.__display_name
        elif (id_ := self.id):
            return f"Version {id_}"
        else:
            return super().display_name

    @display_name.setter
    def display_name(self, display_name: str):
        self.__display_name = str(display_name) if display_name is not None else None

    @property
    def s3_uri(self) -> Optional[str]:
        """
        The object's S3 URI, computed from the bucket id and the key field.
        """
        return s3_uri(self.bucket_id, self.key)

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
    def resource_type_and_id(self) -> str | None:
        """
        The object's Amazon Resource Name resource type and ID.
        """
        bucket_id = self.bucket_id
        key = self.key
        id_ = self.id
        return f"{bucket_id}/{key}?versionId={id_}" if bucket_id and key and id_ else None


class S3Object(AWSDesktopObject, abc.ABC):
    """
    Marker interface for S3 object classes, such as heaobject.folder.AWSS3Folder and heaobject.data.AWSS3FileObject.
    Because S3 storage is not a hierarchical file system, subclasses of S3Object and related business logic provide a
    "view" of S3 objects as a virtual hierarchical file system. As such, AWSS3Folders may be either zero-size objects
    with a key that ends in a slash or a virtual object that is generated by HEA to mimic the behavior of a file system
    with hierarchical folders. AWSS3FileObjects always have underlying physical storage. AWSS3Project objects are
    stored as S3 folder objects, and metadata to denote the folder's key as a project must be stored elsewhere.

    S3Object instances may represent non-deleted S3 objects, or in the case of objects in a versioned bucket, all
    versions of an object created since the first delete marker or the beginning of the object's version history sorted
    in reverse chronological order. In the case of deleted objects in a versioned bucket, an S3Object represents a
    grouping of all versions of the object between delete markers or the earliest delete marker and the beginning of
    the object's version history. S3Objects have no version information. A specific version of an S3 object is
    represented by the S3Version class. The heaobject.trash.AWSS3FolderFileTrashItem class represents a view of an
    S3Object, with the S3Object representing one of the above groupings of deleted S3 object versions.

    The S3 object mixins in this module define optional additional attributes and methods for S3 objects.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__bucket_id: Optional[str] = None

    @property
    @abc.abstractmethod
    def key(self) -> Optional[str]:
        """
        The object's key.
        """
        pass

    @key.setter
    @abc.abstractmethod
    def key(self, key: Optional[str]):
        pass

    @property
    @abc.abstractmethod
    def s3_uri(self) -> Optional[str]:
        """
        The object's S3 URI, computed from the bucket id and the id field.
        """
        pass

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
    def resource_type_and_id(self) -> str | None:
        """
        The object's Amazon Resource Name resource type and ID.
        """
        bucket_id = self.bucket_id
        key = self.key
        return f"{bucket_id}/{key}" if bucket_id and key else None


RegionLiteral = Literal['af-south-1', 'ap-east-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3', 'ap-south-1',
                        'ap-south-2', 'ap-southeast-1', 'ap-southeast-2', 'ap-southeast-3', 'ca-central-1',
                        'cn-north-1', 'cn-northwest-1', 'eu-central-1', 'eu-south-2', 'eu-north-1', 'eu-south-1',
                        'eu-west-1', 'eu-west-2', 'eu-west-3', 'me-south-1', 'sa-east-1', 'us-gov-east-1',
                        'us-gov-west-1', 'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'EU',
                        'ap-southeast-4', 'ap-southeast-5', 'eu-central-2', 'il-central-1', 'me-central-1']
S3EventLiteral = Literal[
    'TestEvent', 'ObjectCreated:*', 'ObjectCreated:Put', 'ObjectCreated:Post', 'ObjectCreated:Copy', 'ObjectCreated:CompleteMultipartUpload',
    'ObjectRemoved:*', 'ObjectRemoved:Delete', 'ObjectRemoved:DeleteMarkerCreated',
    'ObjectRestore:*', 'ObjectRestore:Post', 'ObjectRestore:Completed', 'ObjectRestore:Delete','ReducedRedundancyLostObject',
    'Replication:*', 'Replication:OperationFailedReplication', 'Replication:OperationMissedThreshold',
    'Replication:OperationReplicatedAfterThreshold', 'Replication:OperationNotTracked',
    'LifecycleExpiration:*', 'LifecycleExpiration:Delete', 'LifecycleExpiration:DeleteMarkerCreated',
    'LifecycleTransition', 'IntelligentTiering','ObjectTagging:*', 'ObjectTagging:Put', 'ObjectTagging:Delete',
    'ObjectAcl:Put'
]


class AmazonResourceName(root.AbstractMemberObject):
    """
    An Amazon Resource Name (ARN). ARNs are used to uniquely identify AWS resources.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__partition = ''
        self.__service = ''
        self.__region = ''
        self.__account_id = ''
        self.__resource_type_and_id = ''

    @property
    def partition(self) -> str:
        return self.__partition

    @partition.setter
    def partition(self, partition: str):
        self.__partition = str(partition) if partition else ''

    @property
    def service(self) -> str:
        return self.__service

    @service.setter
    def service(self, service: str):
        self.__service = str(service) if service else ''

    @property
    def region(self) -> str:
        return self.__region

    @region.setter
    def region(self, region: str):
        self.__region = str(region) if region else ''

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def account_id(self) -> str:
        return self.__account_id

    @account_id.setter
    def account_id(self, account_id: str):
        self.__account_id = str(account_id) if account_id else ''

    @property
    def resource_type_and_id(self) -> str:
        return self.__resource_type_and_id

    @resource_type_and_id.setter
    def resource_type_and_id(self, resource_type_and_id: str):
        self.__resource_type_and_id = str(resource_type_and_id) if resource_type_and_id else ''

    def __iter__(self):
        return iter((self.partition, self.service, self.region, self.account_id, self.resource_type_and_id))

    def __getitem__(self, index: int):
        return (self.partition, self.service, self.region, self.account_id, self.resource_type_and_id)[index]

    def __str__(self) -> str:
        return f"arn:{self.partition}:{self.service}:{self.region}:{self.account_id}:{self.resource_type_and_id}"

    def to_arn_str(self) -> str:
        """
        Returns the ARN string representation of this ARN.
        """
        return str(self)

    @classmethod
    def from_arn_str(cls, arn: str) -> 'AmazonResourceName':
        """
        Extracts the partition, service, region, account ID, resource type, and resource ID from the given ARN.

        :param arn: an ARN string.
        """
        parts = arn.split(':', maxsplit=5)
        arn_ = cls()
        arn_.partition = parts[1]
        arn_.service = parts[2]
        arn_.region = parts[3]
        arn_.account_id = parts[4]
        arn_.resource_type_and_id = parts[5]
        return arn_


