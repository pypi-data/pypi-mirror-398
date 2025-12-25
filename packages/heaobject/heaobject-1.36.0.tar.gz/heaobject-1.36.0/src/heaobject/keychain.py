"""
Classes supporting the management of user credentials and certificates.
"""
from datetime import datetime, timedelta, tzinfo
from typing import Optional, TypeVar

from heaobject.decorators import attribute_metadata
from . import root
from dateutil import parser as dateparser # Change to use datetime.fromisoformat when we stop supporting Python 3.10.
from .util import now, Sentinel, SENTINEL, make_timezone_aware, to_bool, get_locale, system_timezone, to_datetime
from .aws import AmazonResourceName
from enum import Enum
from io import StringIO, TextIOBase
from babel.dates import format_datetime
from locale import getlocale, LC_TIME
import math

class CredentialsLifespanClass(Enum):
    """Lifespan classes. SHORT_LIVED refers to access tokens and other dynamically generated credentials with a
    typically short-term expiry and may automatically refresh. LONG_LIVED refers to manually created credentials that
    have no expiry or a long-term expiry and do not refresh automatically."""
    SHORT_LIVED = 10
    LONG_LIVED = 20


class Credentials(root.AbstractDesktopObject):
    """
    Stores a user's secrets, passwords, and keys, and makes them available to applications.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__account: str | None = None
        self.__where: str | None = None
        self.__password: str | None = None
        self.__role: str | None = None
        self.__expiration: datetime | None = None
        self.__lifespan_class = CredentialsLifespanClass.LONG_LIVED
        self.__lifespan: float | None = None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    def account(self) -> Optional[str]:
        """
        The username or account name.
        """
        return self.__account

    @account.setter  # type: ignore
    def account(self, account: Optional[str]) -> None:
        self.__account = str(account) if account is not None else None

    @property  # type: ignore
    def where(self) -> Optional[str]:
        """
        The hostname, URL, service, or other location of the account.
        """
        return self.__where

    @where.setter  # type: ignore
    def where(self, where: Optional[str]) -> None:
        self.__where = str(where) if where is not None else None

    @attribute_metadata(sensitive=True, needs_encryption=True)  # type: ignore[prop-decorator]
    @property  # type: ignore
    def password(self) -> Optional[str]:
        """
        The account password or secret. Non-None values are encrypted if an Encryption object is passed to the
        to_dict() method.
        """
        return self.__password

    @password.setter  # type: ignore
    def password(self, password: Optional[str]) -> None:
        self.__password = str(password) if password is not None else None

    @property
    def type_display_name(self) -> str:
        return "Credentials"

    @property
    def role(self) -> str | None:
        """A role to assume while logged in with these credentials."""
        return self.__role

    @role.setter
    def role(self, role: str | None):
        self.__role = str(role) if role is not None else None

    @property
    def expiration(self) -> datetime | None:
        """
        The session's expiration time. Setting this attribute to an ISO 8601 string will also work -- the ISO string
        will be parsed automatically as a datetime object. If the provided datetime has no timezone information, it is
        assumed to be in local time, and it will be made timezone-aware. Setting this to a datetime further in the
        future than the current value of the maximum_lifespan attribute will raise a ValueError. A None expiration may
        mean that the expiration has not been set yet, so None values do not fail validation. Also, these objects test
        expiration validity at the time their attributes are set, so the expiration may become invalid by the time the
        credentials are used to connect to a resource.
        """
        return self.__expiration

    @expiration.setter
    def expiration(self, expiration: str | datetime | None) -> None:
        date_obj = to_datetime(expiration)
        self.raise_if_expiration_invalid(expiration=date_obj)
        self.__expiration = date_obj

    @property
    def maximum_duration(self) -> float | None:
        """
        The maximum possible lifespan in seconds of these credentials. This implementation returns None to signify no
        maximum.
        """
        return self.maximum_duration_for(self.lifespan_class)

    def has_expired(self, exp_diff = 0.0) -> bool:
        """
        Returns whether these credentials have expired. If this object's expiration attribute is None, has_expired()
        returns False.

        :param exp_diff: the difference between expiration and current time in minutes (default to zero).
        :return: whether these credentials have expired or not.
        """
        if seconds := self.time_to_expire:
            minutes = seconds / 60.0
            return minutes < exp_diff or math.isclose(minutes, exp_diff)
        else:
            return False  # if expiration attribute not set, allow credentials to generate it

    @property
    def time_to_expire(self) -> float | None:
        """
        Seconds until the credentials expire. If the expiration attribute is None, this attribute is also None.
        Negative values mean the credentials have expired.
        """
        if not (expiration_ := self.expiration):
            return None
        else:
            return (expiration_ - now()).total_seconds()

    @property
    def lifespan(self) -> float | None:
        """
        The credentials' lifespan in seconds.
        """
        return self.__lifespan

    @lifespan.setter
    def lifespan(self, lifespan: float | None):
        if lifespan is not None:
            lifespan_ = float(lifespan)
            if (max_dur := self.maximum_duration_for(self.lifespan_class)) is not None and max_dur < lifespan_:
                raise ValueError(f'{lifespan} is beyond the maximum lifespan for {self.maximum_duration_for(self.lifespan_class)} credentials')
            self.__lifespan = lifespan_
        else:
            self.__lifespan = None
        self.__lifespan = lifespan

    def extend(self, duration: int | None = None) -> None:
        """
        Resets the expiration of the credentials by the given duration in seconds. If unspecified or None, the last
        set lifespan is used. If there is None, nothing happens.
        """
        if expiration_ := self.expiration:
            now_ = now().astimezone(expiration_.tzinfo)
        else:
            now_ = now()
        if duration is not None:
            self.expiration = now_ + timedelta(seconds=duration)
        elif (lifespan := self.lifespan) is not None:
            self.expiration = now_ + timedelta(seconds=lifespan)
        else:
            self.expiration = expiration_

    @property
    def lifespan_class(self) -> CredentialsLifespanClass:
        """The credentials' lifespan class, by default CredentialsLifespanClass.LONG_LIVED. SHORT_LIVED generally means
        temporary credentials that must be refreshed frequently, like AWS temporary credentials or a short-lived access
        token. For ordinary username and password combinations with no expiration or a fixed expiration in the distant
        future, use LONG_LIVED."""
        return self.__lifespan_class

    @lifespan_class.setter
    def lifespan_class(self, lifespan_class: CredentialsLifespanClass):
        lifespan_class_ = lifespan_class if isinstance(lifespan_class, CredentialsLifespanClass) else CredentialsLifespanClass[str(lifespan_class)]
        self.raise_if_expiration_invalid(lifespan_class=lifespan_class_)
        self.__lifespan_class = lifespan_class_

    def set_lifespan_class_from_str(self, lifespan_class: str):
        """
        Sets the lifespan class from a string.

        :param lifespan_class: CredentialsLifespanClass.SHORT_LIVED or CredentialsLifespanClass.LONG_LIVED.
        """
        self.lifespan_class = CredentialsLifespanClass[str(lifespan_class)]

    def maximum_duration_for(self, lifespan_class: CredentialsLifespanClass | None = None) -> float | None:
        """
        The maximum possible lifespan in seconds for the given lifespan enum value. This implementation returns None
        to signify no maximum.

        :param: the lifespan enum value to check. If None, the object's lifespan attribute value is checked.
        :return: the maximum lifespan for the given lifespan enum value.
        """
        return None

    def raise_if_expiration_invalid(self, expiration: datetime | Sentinel | None = SENTINEL, **kwargs) -> None:
        """
        Check if a non-None expiration attribute value is valid, and raise a ValueError if not.

        :param expiration: the expiration datetime to check. If None, the object's expiration attribute is checked.
        A value of SENTINEL, or omitting this parameter, will use the object's current expiration.
        :param kwargs: attribute values needed to determine the maximum allowed lifespan as computed by the
        maximum_lifespan_for() method. For any omitted attributes, the object's current attribute value is used.
        :raises ValueError: if the expiration is invalid.
        """
        if expiration is None:
            new_expiration_: datetime | None = None
        elif isinstance(expiration, Sentinel):
            new_expiration_ = self.expiration
        else:
            new_expiration_ = expiration
        if new_expiration_ is not None:
            lifespan_args = {k: v if v is not None else getattr(self, k) for k, v in kwargs.items()}
            maximum_lifespan_ = self.maximum_duration_for(**lifespan_args)
            if maximum_lifespan_ is not None and new_expiration_.astimezone() - now() > timedelta(seconds=maximum_lifespan_):
                raise ValueError(f'{new_expiration_} is beyond the maximum lifespan of {maximum_lifespan_} seconds')


CredentialTypeVar = TypeVar('CredentialTypeVar', bound=Credentials)


class AWSCredentials(Credentials):
    """
    Credentials object extended with AWS-specific attributes. The role attribute should contain the role ARN.
    """

    class State(Enum):
        """Represents internal state."""
        DEFAULT = 0
        TEMPORARY = 10
        MANAGED = 20

    def __init__(self) -> None:
        super().__init__()
        self.__session_token: Optional[str] = None
        self.__arn: AmazonResourceName | None = None
        self.__state = AWSCredentials.State.DEFAULT
        self.__for_presigned_url = False

    @attribute_metadata(sensitive=True, needs_encryption=True)  # type: ignore[prop-decorator]
    @property
    def session_token(self) -> Optional[str]:
        """
        The session token.
        """
        return self.__session_token

    @session_token.setter
    def session_token(self, session_token: Optional[str]):
        self.__session_token = str(session_token) if session_token is not None else None

    @property
    def state(self) -> State:
        """The state of the credentials, by default AWSCredentials.State.DEFAULT. If the credentials are temporary, the
        state is AWSCredentials.State.TEMPORARY. If the credentials are managed, the state is
        AWSCredentials.State.MANAGED. This attribute is read-only and should not be overridden."""
        return self.__state

    @property
    def lifespan_class(self) -> CredentialsLifespanClass:
        """The credentials' lifespan, by default CredentialsLifespanClass.LONG_LIVED. Long-term AWS credentials are
        LONG_LIVED. Temporary credentials are SHORT_LIVED. Setting this attribute to SHORT_LIVED will automatically set
        temporary to True, and setting it to LONG_LIVED will automatically set temporary to False. Setting this
        attribute to SHORT_LIVED will also set the for_presigned_url attribute to False."""
        match self.__state:
            case AWSCredentials.State.DEFAULT | AWSCredentials.State.MANAGED:
                return CredentialsLifespanClass.LONG_LIVED
            case AWSCredentials.State.TEMPORARY:
                return CredentialsLifespanClass.SHORT_LIVED

    @lifespan_class.setter
    def lifespan_class(self, lifespan_class: CredentialsLifespanClass):
        if isinstance(lifespan_class, CredentialsLifespanClass):
            lifespan_class_ = lifespan_class
        else:
            lifespan_class_ = CredentialsLifespanClass[str(lifespan_class)]
        self.raise_if_expiration_invalid(lifespan_class=lifespan_class_)
        if (lifespan_ := self.lifespan) is not None and (max_ := self.maximum_duration_for(lifespan_class_)) is not None and max_ < lifespan_:
            raise ValueError(f'Lifespan {lifespan_} is beyond the maximum lifespan for {lifespan_class_}')
        match lifespan_class_:
            case CredentialsLifespanClass.SHORT_LIVED:
                self.__state = AWSCredentials.State.TEMPORARY
                self.for_presigned_url = False
            case CredentialsLifespanClass.LONG_LIVED if not self.managed:
                self.__state = AWSCredentials.State.DEFAULT

    @property
    def temporary(self) -> bool:
        """Whether or not to use AWS' temporary credentials generation mechanism. The default value is False. Setting
        this attribute to False sets the lifespan_class attribute to LONG_LIVED. Setting it to True sets the
        lifespan_class attribute to SHORT_LIVED and sets the for_presigned_url attribute to False. Likewise, setting
        the lifespan_class attribute to LONG_LIVED sets this attribute to False, and setting the lifespan_class
        attribute to SHORT_LIVED sets this attribute to True. AWSCredentials cannot be both temporary and managed."""
        match self.__state:
            case AWSCredentials.State.DEFAULT | AWSCredentials.State.MANAGED:
                return False
            case AWSCredentials.State.TEMPORARY:
                return True

    @temporary.setter
    def temporary(self, temporary: bool):
        match to_bool(temporary):
            case True:
                self.raise_if_expiration_invalid(lifespan_class=CredentialsLifespanClass.SHORT_LIVED, managed=False)
                self.__state = AWSCredentials.State.TEMPORARY
                self.for_presigned_url = False
            case False if not self.managed:
                self.raise_if_expiration_invalid(lifespan_class=CredentialsLifespanClass.LONG_LIVED)
                self.__state = AWSCredentials.State.DEFAULT

    @property
    def managed(self) -> bool:
        """Flag to determine if AWS credential's lifecycle is managed by system. The default value is False.
        AWSCredentials cannot be both temporary and managed."""
        match self.__state:
            case AWSCredentials.State.TEMPORARY | AWSCredentials.State.DEFAULT:
                return False
            case AWSCredentials.State.MANAGED:
                return True

    @managed.setter
    def managed(self, managed: bool):
        match to_bool(managed):
            case True:
                self.raise_if_expiration_invalid(lifespan_class=CredentialsLifespanClass.LONG_LIVED, managed=True)
                self.__state = AWSCredentials.State.MANAGED
            case False if self.__state is AWSCredentials.State.MANAGED:
                self.__state = AWSCredentials.State.DEFAULT

    @property
    def for_presigned_url(self) -> bool:
        """Whether or not these credentials are for generating presigned URLs. The default value is False. Setting this
        attribute to True also sets the managed attribute to True and the state attribute to MANAGED."""
        return self.__for_presigned_url

    @for_presigned_url.setter
    def for_presigned_url(self, presigned_url: bool):
        match to_bool(presigned_url):
            case True:
                self.__for_presigned_url = True
                self.__state = AWSCredentials.State.MANAGED
            case False:
                self.__for_presigned_url = False

    @property
    def type_display_name(self) -> str:
        return "AWS Credentials"

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def role(self) -> str | None:
        """The role ARN string. If overridden, you must also override the role_arn attribute."""
        return str(self.__arn) if self.__arn is not None else None

    @role.setter
    def role(self, role: str | None):
        if role is not None:
            self.__arn = AmazonResourceName.from_arn_str(role)
        else:
            self.__arn = None

    @property
    def role_arn(self) -> AmazonResourceName | None:
        """The role ARN."""
        return self.__arn

    @property
    def aws_role_name(self) -> str | None:
        """The role name extracted from the role attribute."""
        if self.role_arn is not None:
            r_index = self.role_arn.resource_type_and_id.rindex('/') + 1
            role_name = self.role_arn.resource_type_and_id[r_index:]
            return role_name
        else:
            return None

    @attribute_metadata(sensitive=True)  # type: ignore[prop-decorator]
    @property
    def account_id(self) -> str | None:
        """The AWS account number extracted from the role ARN."""
        return self.role_arn.account_id if self.role_arn is not None else None

    def maximum_duration_for(self, lifespan_class: CredentialsLifespanClass | None = None, managed: bool | None = None) -> float | None:
        """
        Returns 12 hours in seconds for temporary credentials and None for other credentials.
        """
        match lifespan_class if lifespan_class is not None else self.lifespan_class:
            case CredentialsLifespanClass.SHORT_LIVED:
                return float(12 * 60 * 60)
            case CredentialsLifespanClass.LONG_LIVED:
                return None
            case _:
                raise ValueError(f'Invalid lifespan {lifespan_class}')

    def has_expired(self, exp_diff = 0):
        """
        In the case of temporary credentials, returns True when expiration is None.

        :param exp_diff: the difference between expiration and current time in minutes (default to zero).
        :return: whether these credentials have expired or not.
        """
        if not self.expiration and self.temporary:
            return True
        else:
            return super().has_expired(exp_diff=exp_diff)

    def to_credentials_file(self, fp: TextIOBase, locale_: str | None = None, tz: tzinfo | None = None) -> None:
        """
        Writes the credentials as a CLI credentials file to a write-supporting file-like object. It calls the file-like
        object's .writelines() method.

        :param fp: the file-like object to write to.
        :param locale_: the locale to use for formatting the expiration date. If unspecified, the system locale is
        used, and if the system locale is unset, the default locale is used (en_US).
        :param tz: the timezone to use for formatting the expiration date. If unspecified, the system timezone is used.
        :raises OSError: if there is an IO error writing to the file-like object.
        """

        if expiration_ := self.expiration:
            tzinfo_ = tz if tz is not None else system_timezone()
            time_locale = get_locale(locale_, LC_TIME)
            exp_local = f", expires {format_datetime(expiration_, locale=time_locale, tzinfo=tzinfo_)} {format_datetime(expiration_, format='z', locale=time_locale, tzinfo=tzinfo_)}"
        else:
            exp_local = ''
        fp.writelines([
            f'# {self.display_name}{exp_local}\n',
            '[tmp]\n',
            f'aws_access_key_id = {self.account}\n',
            f'aws_secret_access_key = {self.password}\n',
            (f'aws_session_token = {self.session_token}\n' if self.temporary else '')
        ])

    def to_credentials_file_str(self, locale_: str | None = None, tz: tzinfo | None = None) -> str:
        """
        Returns a string representation of the credentials suitable for writing to a credentials file.

        :param locale_: the locale to use for formatting the expiration date. If unspecified, the system locale is
        used, and if the system locale is unset, the default locale is used (en_US).
        :param tz: the timezone to use for formatting the expiration date. If unspecified, the system timezone is used.
        """
        with StringIO() as credentials_file:
            self.to_credentials_file(credentials_file, locale_=locale_, tz=tz)
            return credentials_file.getvalue()


class CredentialsView(root.AbstractDesktopObject, root.View):
    """
    A view of a Credentials object or its subclasses. The view's id is the instance_id of the credentials object it
    represents.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__actual_object_id: str | None = None
        self.__actual_object_type_name: str | None = None
        self.__type_display_name: str | None = None

    @property
    def actual_object_id(self) -> str | None:
        return self.__actual_object_id

    @actual_object_id.setter
    def actual_object_id(self, actual_object_id: str | None):
        self.__actual_object_id = str(actual_object_id) if actual_object_id is not None else None
        self.id = f'{self.actual_object_type_name}^{self.__actual_object_id}'

    @property
    def actual_object_type_name(self) -> str | None:
        return self.__actual_object_type_name

    @actual_object_type_name.setter
    def actual_object_type_name(self, actual_object_type_name: str | None):
        self.__actual_object_type_name = str(actual_object_type_name) if actual_object_type_name is not None else None
        self.id = f'{self.__actual_object_type_name}^{self.actual_object_id}'

    @property
    def type_display_name(self) -> str:
        if self.__type_display_name is not None:
            return self.__type_display_name
        if (actual := self.actual_object_type_name) is not None:
            return root.desktop_object_type_for_name(actual).__name__
        else:
            return 'Credentials'

    @type_display_name.setter
    def type_display_name(self, type_display_name: str):
        self.__type_display_name = str(type_display_name) if type_display_name is not None else None
