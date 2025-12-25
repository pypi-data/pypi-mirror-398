"""
Classes for recording user activity. Examples include logins and actions on
desktop objects.

Subclassing any of the classes in this module is not supported.
"""
from abc import ABC, abstractmethod
from datetime import date
from humanize import naturaldelta
from enum import Enum
from typing import Optional
from .root import AbstractDesktopObject, View, NonCreatorSuperAdminDefaultPermissionsMixin
from .decorators import attribute_metadata
from .data import DataObject, SameMimeType
from .util import now, to_date_or_datetime
import uuid
from yarl import URL
from copy import copy


class Status(Enum):
    """
    The lifecycle of an action. Allowed sequences of statuses are:
    REQUESTED, IN_PROGRESS, and SUCCEEDED; and REQUESTED, IN_PROGRESS, and
    FAILED. Their values are ordered according to these sequences, for example,
    Status.REQUESTED.value < Status.IN_PROGRESS.value < Status.FAILED.value.
    However, comparing statuses directly, for example,
    Status.REQUESTED < Status.IN_PROGRESS does not work. Actions may
    instantaneously transition from REQUESTED to IN_PROGRESS, and instantaneous
    actions skip directly from REQUESTED to either SUCCEEDED or FAILED.
    """
    REQUESTED = 10
    IN_PROGRESS = 20
    SUCCEEDED = 30
    FAILED = 40


class Activity(NonCreatorSuperAdminDefaultPermissionsMixin, DataObject, SameMimeType, ABC):
    """
    Abstract base class for recording user activity. Activities have three
    statuses: requested, began, and ended. Subclasses may introduce additional
    statuses. Concrete implementations of Activity must at minimum provide
    implementations of the requested, began, and ended attributes. Note that
    these timestamps are different from the standard created and modified
    timestamps that all desktop objects have. Requested, began, and ended
    should be set by the service orchestrating the activity. The created and
    modified attributes are set when the activity is persisted.

    Activity objects, like other desktop objects, have an id attribute that is
    generated when the object is stored. Activity objects also have an
    application-generated id for situations where it is desirable to record
    changes in an action's state prior to the object being stored (such as when
    sending the object over an asynchronous message queue).
    """

    @abstractmethod
    def __init__(self) -> None:
        """
        Constructor for Activity objects. It generates a version 4 UUID and
        assigns it to the application_id attribute. The initial status is
        REQUESTED.
        """
        super().__init__()
        self.__user_id: str | None = None
        self.__application_id: str | None = None
        self.__request_url: str | None = None
        self.__context: str | None = None

    @property
    def application_id(self) -> str | None:
        """A uuid for identifying updates on the same activity. If
        activity objects are generated and sent over a message queue, the id
        field cannot be set until the receiver stores the object. The
        activity might have concluded before an id is generated. The
        application_id attribute serves as a stand-in for the id for the sender
        to identify updates on an activity independently of the receiver. See
        the docstring for DesktopObject.id for the distinction between
        application ids and database ids (the latter is stored in the
        DesktopObject.id attribute). The static method generate_application_id()
        may be used to create an application id that is reasonably guaranteed
        not to clash with other activity objects."""
        return self.__application_id

    @application_id.setter
    def application_id(self, application_id: str | None):
        self.__application_id = str(application_id) if application_id is not None else None

    def generate_application_id(self):
        """
        Generates a unique application id using python's built-in UUID
        generation.
        """
        # The python docs (https://docs.python.org/3.10/library/uuid.html)
        # recommend using uuid1 or 4, but 1 may leak IP addresses of server-
        # side processes, so I went with 4.
        self.application_id = str(uuid.uuid4())

    @property
    def mime_type(self) -> str:
        return type(self).get_mime_type()

    @property
    def user_id(self) -> Optional[str]:
        """The identifier of the user who began the activity. It may be
        different from the owner of the activity object so as to control the
        object's visibility."""
        return self.__user_id

    @user_id.setter
    def user_id(self, __user_id: Optional[str]) -> None:
        self.__user_id = str(__user_id) if __user_id is not None else None

    @property
    def request_url(self) -> str | None:
        """The URL of the request associated with this activity, if there was one."""
        return self.__request_url

    @request_url.setter
    def request_url(self, request_url: str | None):
        self.__request_url = str(URL(request_url)) if request_url is not None else None

    @property
    @abstractmethod
    def requested(self) -> date:
        """When the activity was requested. May be set using a date or an ISO-formatted string."""
        pass

    @requested.setter
    @abstractmethod
    def requested(self, requested: date):
        pass

    @property
    @abstractmethod
    def began(self) -> date | None:
        """When the activity began. May be set using a date or an ISO-formatted string."""
        pass

    @began.setter
    @abstractmethod
    def began(self, began: date | None):
        pass

    @property
    @abstractmethod
    def ended(self) -> date | None:
        """When the activity ended. May be set using a date or an ISO-formatted string."""
        pass

    @ended.setter
    @abstractmethod
    def ended(self, ended: date | None):
        pass

    @property
    def status_updated(self) -> date:
        """
        When the activity's status most recently progressed. It returns the
        value of the ended attribute if it is not None, then began, then
        requested.
        """
        if self.ended is not None:
            return self.ended
        elif self.began is not None:
            return self.began
        else:
            return self.requested

    @property
    def duration(self) -> int | None:
        """How long the activity took to complete or fail in seconds."""
        if self.began is not None and self.ended is not None:
            return (self.ended - self.began).seconds
        else:
            return None

    @property
    def human_readable_duration(self) -> str | None:
        """How long the activity took to complete or fail in human readable form."""
        if self.began is not None and self.ended is not None:
            return naturaldelta(self.ended - self.began)
        else:
            return None

    @property
    def context(self) -> str | None:
        """Client-defined context, such as the part of a user interface, where the activity occurred."""
        return self.__context

    @context.setter
    def context(self, context: str | None):
        self.__context = str(context) if context is not None else None


class Action(Activity, ABC):
    """
    Actions are user activities with a lifecycle indicated by the action's
    status attribute.

    The code attribute is used to store a code for the action. HEA defines a
    set of standard codes prefixed with hea-, and HEA reserves that prefix for
    its own use. Third parties may define their own prefix and action codes.

    The HEA-defined reserved codes are:
        hea-duplicate: object duplication.
        hea-move: object move.
        hea-delete: object delete.
        hea-get: object access.
        hea-update: object update.
        hea-create: object create.
        hea-archive: object archive.
        hea-unarchive: object unarchive.

    The description attribute is expected to be populated with a brief summary of the action.
    """
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.__began: date | None = None
        self.__ended: date | None = None
        self.__status: Status = Status.REQUESTED
        self.__code: str | None = None
        self.__requested: date = now()

    @property
    def requested(self) -> date:
        return self.__requested

    @requested.setter
    def requested(self, requested: date):
        if requested is None:
            raise ValueError('requested cannot be None')
        self.__requested = to_date_or_datetime(requested)

    @property
    def began(self) -> date | None:
        return self.__began

    @began.setter
    def began(self, began: date | None):
        self.__began = to_date_or_datetime(began)

    @property
    def ended(self) -> date | None:
        return self.__ended

    @ended.setter
    def ended(self, ended: date | None):
        self.__ended = to_date_or_datetime(ended)

    @property
    def status(self) -> Status:
        """The action's lifecycle status as a Status enum value. If setting it to a string value, it will attempt to
        parse the string into a Status enum value. The default value is Status.REQUESTED."""
        return self.__status

    @status.setter
    def status(self, status: Status) -> None:
        old_status = self.__status
        if status is None:
            ___status = Status.REQUESTED
        elif isinstance(status, Status):
            ___status = status
        else:
            try:
                ___status = Status[status]
            except KeyError as e:
                raise ValueError(str(e)) from e
        if ___status.value < old_status.value:
            raise ValueError(f'Invalid status changed {old_status} to {___status}')
        self.__status = ___status
        now_ = now()
        if old_status == Status.REQUESTED and self.__status.value > Status.REQUESTED.value and self.began is None:
            self.began = now_
        if self.ended is None:
            if old_status.value < Status.SUCCEEDED.value and self.__status == Status.SUCCEEDED:
                self.ended = now_
            if old_status.value < Status.FAILED.value and self.__status == Status.FAILED:
                self.ended = now_

    @property
    def code(self) -> str | None:
        return self.__code

    @code.setter
    def code(self, code: str | None):
        self.__code = str(code) if code is not None else None


class DesktopObjectAction(Action):
    """A user action on a desktop object. Compared to the Action class, it
    provides fields for the object's original URI and its URI after the action
    completes successfully.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__old_object_uri: str | None = None
        self.__new_object_uri: str | None = None
        self.__old_volume_id: str | None = None
        self.__new_volume_id: str | None = None
        self.__old_object_id: str | None = None
        self.__new_object_id: str | None = None
        self.__old_object_type_name: str | None = None
        self.__new_object_type_name: str | None = None
        self.__old_context_dependent_object_path: list[str] | None = None
        self.__new_context_dependent_object_path: list[str] | None = None
        self.__old_object_display_name: str | None = None
        self.__new_object_display_name: str | None = None
        self.__old_object_description: str | None = None
        self.__new_object_description: str | None = None

    @classmethod
    def get_mime_type(cls) -> str:
        return 'application/x.desktopobjectaction'

    @property
    def old_object_uri(self) -> str | None:
        """The URL of the object prior to the action being performed, if any. It should be set while the activity has
        a REQUESTED status. The URL must be relative, without a leading slash, to an API gateway for accessing the
        object."""
        return self.__old_object_uri

    @old_object_uri.setter
    def old_object_uri(self, old_object_uri: str | None):
        self.__old_object_uri = str(URL(old_object_uri)) if old_object_uri is not None else None

    @property
    def new_object_uri(self) -> str | None:
        """The URL of the object after the action has completed successfully, if any. It is only set if the activity
        has a SUCCEEDED status. The URL must be relative, without a leading slash, to an API gateway for accessing the
        object."""
        return self.__new_object_uri

    @new_object_uri.setter
    def new_object_uri(self, new_object_uri: str | None):
        self.__new_object_uri = str(URL(new_object_uri)) if new_object_uri is not None else None

    @property
    def old_volume_id(self) -> str | None:
        """The volume id of the object prior to the action being performed, if any. It should be set while the
        activity has a REQUESTED status."""
        return self.__old_volume_id

    @old_volume_id.setter
    def old_volume_id(self, old_volume_id: str | None):
        self.__old_volume_id = str(old_volume_id) if old_volume_id is not None else None

    @property
    def new_volume_id(self) -> str | None:
        """The volume id of the object after the action has completed successfully, if any. It is only set if the
        activity has a SUCCEEDED status."""
        return self.__new_volume_id

    @new_volume_id.setter
    def new_volume_id(self, new_volume_id: str | None):
        self.__new_volume_id = str(new_volume_id) if new_volume_id is not None else None

    @property
    def old_object_id(self) -> str | None:
        """The object id of the object prior to the action being performed, if any. It should be set while the
        activity has a REQUESTED status."""
        return self.__old_object_id

    @old_object_id.setter
    def old_object_id(self, old_object_id: str | None):
        self.__old_object_id = str(old_object_id) if old_object_id is not None else None

    @property
    def new_object_id(self) -> str | None:
        """The object id of the object after the action has completed successfully, if any. It is only set if the
        activity has a SUCCEEDED status."""
        return self.__new_object_id

    @new_object_id.setter
    def new_object_id(self, new_object_id: str | None):
        self.__new_object_id = str(new_object_id) if new_object_id is not None else None

    @property
    def old_object_type_name(self) -> str | None:
        """The type name of the object prior to the action being performed, if any. It should be set while the
        activity has a REQUESTED status."""
        return self.__old_object_type_name

    @old_object_type_name.setter
    def old_object_type_name(self, old_object_type_name: str | None):
        self.__old_object_type_name = str(old_object_type_name) if old_object_type_name is not None else None

    @property
    def new_object_type_name(self) -> str | None:
        """The type name of the object after the action has completed successfully, if any. It is only set if
        the activity has a SUCCEEDED status."""
        return self.__new_object_type_name

    @new_object_type_name.setter
    def new_object_type_name(self, new_object_type_name: str | None):
        self.__new_object_type_name = str(new_object_type_name) if new_object_type_name is not None else None

    @property
    def type_display_name(self) -> str:
        return "Desktop Object Action"

    @property
    def old_context_dependent_object_path(self) -> list[str] | None:
        """Path to the object. None means no path was recorded."""
        return copy(self.__old_context_dependent_object_path)

    @old_context_dependent_object_path.setter
    def old_context_dependent_object_path(self, old_context_dependent_object_path: list[str] | None):
        if old_context_dependent_object_path is None:
            self.__old_context_dependent_object_path = None
        else:
            self.__old_context_dependent_object_path = list(str(i) for i in old_context_dependent_object_path)

    @property
    def new_context_dependent_object_path(self) -> list[str] | None:
        """Path to the object. None means no path was recorded."""
        return copy(self.__new_context_dependent_object_path)

    @new_context_dependent_object_path.setter
    def new_context_dependent_object_path(self, new_context_dependent_object_path: list[str] | None):
        if new_context_dependent_object_path is None:
            self.__new_context_dependent_object_path = None
        else:
            self.__new_context_dependent_object_path = list(str(i) for i in new_context_dependent_object_path)

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def old_object_display_name(self) -> str | None:
        """The old object's display name."""
        return self.__old_object_display_name

    @old_object_display_name.setter
    def old_object_display_name(self, old_object_display_name: str | None):
        self.__old_object_display_name = str(old_object_display_name) if old_object_display_name is not None else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def new_object_display_name(self) -> str | None:
        """The new object's display name."""
        return self.__new_object_display_name

    @new_object_display_name.setter
    def new_object_display_name(self, new_object_display_name: str | None):
        self.__new_object_display_name = str(new_object_display_name) if new_object_display_name is not None else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def old_object_description(self) -> str | None:
        """The old object's description."""
        return self.__old_object_description

    @old_object_description.setter
    def old_object_description(self, old_object_description: str | None):
        self.__old_object_description = str(old_object_description) if old_object_description is not None else None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def new_object_description(self) -> str | None:
        """The new object's description."""
        return self.__new_object_description

    @new_object_description.setter
    def new_object_description(self, new_object_description: str | None):
        self.__new_object_description = str(new_object_description) if new_object_description is not None else None

    def copy_old_to_new(self):
        """Copies the values of the old object properties to the new object properties."""
        self.new_object_uri = self.old_object_uri
        self.new_volume_id = self.old_volume_id
        self.new_object_id = self.old_object_id
        self.new_object_type_name = self.old_object_type_name
        self.new_context_dependent_object_path = self.old_context_dependent_object_path
        self.new_object_display_name = self.old_object_display_name
        self.new_object_description = self.old_object_description

class RecentlyAccessedView(AbstractDesktopObject, View):
    """
    View of a desktop object indicating when it was last accessed.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__accessed: date | None = None
        self.__context: str | None = None
        self.__context_dependent_object_path: list[str] | None = None

    @property
    def accessed(self) -> date | None:
        """When the desktop object was last accessed. May be set using a date or an ISO-formatted string. None means
        the object has been accessed but the time is not known."""
        return self.__accessed

    @accessed.setter
    def accessed(self, accessed: date | None):
        self.__accessed = to_date_or_datetime(accessed)

    @property
    def type_display_name(self) -> str:
        return "Recently Accessed View"

    @property
    def context(self) -> str | None:
        """Client-defined context, such as the part of a user interface, where the object was last touched."""
        return self.__context

    @context.setter
    def context(self, context: str | None):
        self.__context = str(context) if context is not None else None

    @property
    def context_dependent_object_path(self) -> list[str] | None:
        """Path to the object when it was last accessed by a client. None means no path was recorded."""
        return copy(self.__context_dependent_object_path)

    @context_dependent_object_path.setter
    def context_dependent_object_path(self, context_dependent_object_path: list[str] | None):
        if context_dependent_object_path is None:
            self.__context_dependent_object_path = None
        else:
            self.__context_dependent_object_path = list(str(i) for i in context_dependent_object_path)


class DesktopObjectSummaryStatus(Enum):
    """
    The status of a desktop object as recorded in the activity log.
    """
    PRESENT = 10
    DELETED = 20


class DesktopObjectSummaryView(AbstractDesktopObject, View):
    """
    View of a desktop object with its status as recorded in the activity log, and some metadata about the time the
    object was last accessed.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__accessed: date | None = None
        self.__status: DesktopObjectSummaryStatus = DesktopObjectSummaryStatus.PRESENT
        self.__context: str | None = None
        self.__context_dependent_object_path: list[str] | None = None

    @property
    def accessed(self) -> date | None:
        """When the desktop object was last accessed. May be set using a date or an ISO-formatted string. None means
        the object has been accessed but the time is not known."""
        return self.__accessed

    @accessed.setter
    def accessed(self, accessed: date | None):
        self.__accessed = to_date_or_datetime(accessed)

    @property
    def status(self) -> DesktopObjectSummaryStatus:
        """Whether the desktop object is present or deleted. The default value is PRESENT"""
        return self.__status

    @status.setter
    def status(self, status: DesktopObjectSummaryStatus):
        if status is None:
            self.__status = DesktopObjectSummaryStatus.PRESENT
        elif isinstance(status, DesktopObjectSummaryStatus):
            self.__status = status
        else:
            self.__status = DesktopObjectSummaryStatus[str(status)]

    @property
    def context(self) -> str | None:
        """Client-defined context, such as the part of a user interface, where the object was last touched."""
        return self.__context

    @context.setter
    def context(self, context: str | None):
        self.__context = str(context) if context is not None else None

    @property
    def context_dependent_object_path(self) -> list[str] | None:
        """Path to the object when it was last accessed by a client. None means no path was recorded."""
        return copy(self.__context_dependent_object_path)

    @context_dependent_object_path.setter
    def context_dependent_object_path(self, context_dependent_object_path: list[str] | None):
        if context_dependent_object_path is None:
            self.__context_dependent_object_path = None
        else:
            self.__context_dependent_object_path = list(str(i) for i in context_dependent_object_path)

    @property
    def type_display_name(self) -> str:
        return "Desktop Object Summary View"
