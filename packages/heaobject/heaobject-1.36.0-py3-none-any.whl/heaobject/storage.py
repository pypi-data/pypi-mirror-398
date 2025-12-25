# This file contains the Storage class and its subclasses, which summarize the usage of a volume's storage.
from datetime import date, datetime
from .data import DataObject, SameMimeType
from .root import HasSize
from abc import ABC
from .util import now, to_date_or_datetime
from .aws import S3StorageClassMixin
from humanize import naturaldelta


class Storage(DataObject, HasSize, ABC):
    """
    Abstract base class for Storage objects that summarize usage of a volume's storage. Depending on the data meant to
    be summarized, object* attributes may be left unset. For example, if only the number of objects in a volume is
    requested, only the object_count attribute may be set. Similarly, data sources that do not populate a desktop
    object's created or modified timestamps should leave the object_earliest_created or object_last_modified
    attributes unset, as described in the attribute documentation below, unless through external information you can
    approximate those values in a way that is useful to users.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__volume_id: str | None = None
        self.__object_count: int | None = None
        self.__object_earliest_created: date | None = None
        self.__object_last_modified: date | None = None
        self.__object_average_duration: float | None = None
        self.__now = now()

    @property
    def volume_id(self) -> str | None:
        """The volume id."""
        return self.__volume_id

    @volume_id.setter
    def volume_id(self, volume_id: str | None) -> None:
        self.__volume_id = str(volume_id) if volume_id is not None else None

    @property
    def object_count(self) -> int | None:
        """This volume's total object count."""
        return self.__object_count

    @object_count.setter
    def object_count(self, object_count: int) -> None:
        self.__object_count = int(object_count) if object_count is not None else None

    @property
    def object_max_duration(self) -> float | None:
        """The longest duration in seconds an object has been stored in this volume, defined as the longest duration
        in seconds between an object's creation time and the present. If the volume's filesystem only supports modified
        timestamps and not created timestamps, this attribute's value is None."""
        created = self.object_earliest_created
        if created is None:
            return None
        match created:
            case datetime():
                return (self.__now - created).total_seconds()
            case date():
                return (self.__now - datetime(created.year, created.month, created.day)).total_seconds()
            case _:
                raise ValueError(f'unexpected date type {type(created)}')

    @property
    def human_readable_max_duration(self) -> str | None:
        if (d := self.object_max_duration) is not None:
            return naturaldelta(d)
        else:
            return None

    @property
    def object_min_duration(self) -> float | None:
        """The shortest duration in seconds an object has been stored in this volume, defined as the shortest duration
        in seconds between an object's modified time and the present. If the volume's filesystem only supports created
        timestamps and not modified timestamps, this attribute's value is None."""
        modified = self.object_last_modified
        if modified is None:
            return None
        match modified:
            case datetime():
                return (self.__now - modified).total_seconds()
            case date():
                return (self.__now - datetime(modified.year, modified.month, modified.day)).total_seconds()
            case _:
                raise ValueError(f'unexpected date type {type(modified)}')

    @property
    def human_readable_min_duration(self) -> str | None:
        if (d := self.object_min_duration) is not None:
            return naturaldelta(d)
        else:
            return None

    @property
    def object_average_duration(self) -> float | None:
        """The average "age" in seconds of the objects currently in this volume, calculated from the difference
        between each object's creation timestamp and the present time. If the volume's filesystem does not support
        created timestamps, leave this attribute unset."""
        return self.__object_average_duration

    @object_average_duration.setter
    def object_average_duration(self, value: float | None) -> None:
        self.__object_average_duration = float(value) if value is not None else None

    @property
    def human_readable_average_duration(self) -> str | None:
        if (d := self.object_average_duration) is not None:
            return naturaldelta(d)
        else:
            return None

    @property
    def object_earliest_created(self) -> date | None:
        """The creation timestamp of the earliest remaining desktop object stored in this volume. If the volume's
        filesystem does not support created timestamps, then this attribute should be unset."""
        return self.__object_earliest_created

    @object_earliest_created.setter
    def object_earliest_created(self, value: date | None) -> None:
        self.__object_earliest_created = to_date_or_datetime(value)

    @property
    def object_last_modified(self) -> date | None:
        """The modified timestamp of the most recently modified desktop object in this volume. If the volume's
        filesystem supports created timestamps but not modified timestamps, created timestamps may be used to
        populate this attribute if modifying an object means replacing it with a new object with a new created
        timestamp. Otherwise, leave this attribute unset."""
        return self.__object_last_modified

    @object_last_modified.setter
    def object_last_modified(self, value: date | None) -> None:
        self.__object_last_modified = to_date_or_datetime(value)

    @property
    def object_average_size(self) -> float | None:
        """The average size of the objects in this volume in bytes."""
        return self.size / self.object_count if self.object_count is not None and self.size is not None else None

    @property
    def type_display_name(self) -> str:
        return "Storage Summary"


class AWSStorage(Storage, ABC):
    """
    Abstract base class for summaries of the different kinds of AWS storage.
    """
    pass


class AWSS3Storage(AWSStorage, SameMimeType, S3StorageClassMixin):
    """
    Summary of an S3 storage class.
    """

    @classmethod
    def get_mime_type(cls) -> str:
        """
        Returns the mime type for AWSStorage objects.

        :return: application/x.awss3storage
        """
        return 'application/x.awss3storage'

    @property
    def mime_type(self) -> str:
        """Read-only. The mime type for AWSStorage objects, application/x.awsstorage."""
        return type(self).get_mime_type()
