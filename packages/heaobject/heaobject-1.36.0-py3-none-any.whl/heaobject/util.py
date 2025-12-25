"""
Various utility functions that may be useful throughout heaobject.
"""
from collections import UserList
from collections.abc import Iterable
from datetime import datetime, timezone, tzinfo, date, timedelta
from tzlocal import get_localzone
import locale
from typing import Any, Generic, overload, TypeVar, cast
import importlib
import dateutil.parser


DEFAULT_LOCALE = 'en_US'


def parse_bool(string: str) -> bool:
    """
    Returns a bool that is appropriate for the given input string. Strings such as "True", "true", "yes", "T", "y",
    and "Y" will return True, and strings such as "False", "false", "no", "t", "n", "N", and "" will return False. If
    string is not recognized, False will be returned.
    """
    return str(string).strip().lower() in ('true', 't', 'yes', 'y')


def to_bool(b: Any) -> bool:
    """
    Returns a bool that is appropriate for the given input. If b is a bool, it is returned unaltered.
    Otherwise, it will convert the object to a str and call parse_bool on it.
    """
    if isinstance(b, bool):
        return b
    else:
        return parse_bool(str(b))


def now() -> datetime:
    """
    Returns the current datetime in UTC, with timezone information.

    :return: a datetime.
    """
    return datetime.now(timezone.utc)


def system_timezone() -> tzinfo:
    """
    Returns the system time zone.

    :return: a tzinfo object.
    """
    return get_localzone()


def is_timezone_naive(dt: datetime) -> bool:
    """
    Returns True if the datetime object has no timezone information, and False otherwise.

    :param dt: the datetime object to check.
    :return: a bool.
    """
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def is_timezone_aware(dt: datetime) -> bool:
    """
    Returns True if the datetime object has timezone information, and False otherwise.

    :param dt: the datetime object to check.
    :return: a bool.
    """
    return not is_timezone_naive(dt)


def make_timezone_aware(dt: datetime, tz: tzinfo | None = None) -> datetime:
    """
    Returns a timezone-aware datetime object. If dt is timezone-aware, it is returned unaltered.

    :param dt: the datetime object to make timezone-aware.
    :param tz: the timezone to convert to. If None or omitted, the system timezone is used.
    :return: a timezone-aware datetime object.
    """
    if is_timezone_naive(dt):
        return dt.replace(tzinfo=tz or system_timezone())
    else:
        return dt


_D = TypeVar('_D', bound=date)


@overload
def to_date_or_datetime(date_or_str: str | None, tz: tzinfo | None = None, make_timezone_aware_ = True) -> date | None:
    ...


@overload
def to_date_or_datetime(date_or_str: _D, tz: tzinfo | None = None, make_timezone_aware_ = True) -> _D:
    ...


def to_date_or_datetime(date_or_str: date | str | None, tz: tzinfo | None = None, make_timezone_aware_ = True) -> date | None:
    """
    Takes a date or datetime object (including subclasses), or parses a ISO 8601 formatted date string, and returns a
    date or datetime. If date_or_str is None, None is returned. If date_or_str is a date object or a datetime object
    with timezone information, it is returned unaltered. If date_or_str is a string, it is parsed as an ISO 8601
    formatted date string into a date object if no time information is present, or a timezone-aware datetime object if
    time information is present. For strings with time information, if timezone information is not present, the system
    timezone is assumed.
    """
    if date_or_str is None:
        return None
    else:
        match date_or_str:
            case datetime():
                return make_timezone_aware(date_or_str, tz=tz) if make_timezone_aware_ else date_or_str
            case date():
                return date_or_str
            case _:
                return parse_isoformat(str(date_or_str), tz=tz, make_timezone_aware_= make_timezone_aware_)

def to_datetime(dt_or_str: datetime | str | None, tz: tzinfo | None = None, make_timezone_aware_ = True) -> datetime | None:
    """
    Takes a datetime object, or parses a ISO 8601 formatted date string, and returns a datetime. If dt_or_str is
    None, None is returned. If dt_or_str is a datetime object with timezone information, it is
    returned unaltered. If dt_or_str is a string, it is parsed as an ISO 8601 formatted date string into a
    datetime object if no time information is present, or a timezone-aware datetime object if time information is
    present. For strings with time information, if timezone information is not present, the system timezone is assumed.
    """
    if dt_or_str is None:
        return None
    else:
        match dt_or_str:
            case datetime():
                return make_timezone_aware(dt_or_str, tz=tz) if make_timezone_aware_ else dt_or_str
            case _:
                d = parse_isoformat(str(dt_or_str), tz=tz, make_timezone_aware_= make_timezone_aware_)
                if isinstance(d, datetime):
                    return d
                else:
                    raise TypeError('Expected datetime, but got date')


def to_date(dt_or_str: date | str | None) -> date | None:
    """
    Takes a date object (only year, month, and/or day) or parses an ISO 8601 formatted date string with, and returns a
    date. If dt_or_str is None, None is returned. If dt_or_str is a string, it is parsed as an ISO 8601 formatted date
    string into a date object. The ISO-formatted string can have a resolution of at most one day.
    """
    if dt_or_str is None:
        return None
    else:
        match dt_or_str:
            case date():
                if dt_or_str.resolution >= timedelta(days=1):
                    return dt_or_str
                else:
                    raise ValueError(f'Invalid ISO 8601 date string {dt_or_str}')
            case _:
                return parse_isoformat(str(dt_or_str), date_only=True)


def seconds_since_epoch(dt: datetime | None = None) -> float:
    """
    Returns an approximation of the time in seconds since the Unix epoch (January 1, 1970 at midnight UTC time). If no
    dt argument is provided or it is None, the current time is used. If the dt argument is timezone-naive, it is
    assumed to be in the system timezone. Dates before the epoch are represented by negative numbers.

    Typically, the accuracy of this function depends on the underlying platform and python implementation. For
    example, most modern operating systems assume that 1 day = 24 * 60 * 60 = 86400 seconds, not taking leap seconds
    into account.

    :return: a float with fractions of a second after the decimal point.
    """
    return (make_timezone_aware(dt) if dt else now()).timestamp()
posix_timestamp = seconds_since_epoch
unix_time = posix_timestamp


def milliseconds_since_epoch(dt: datetime | None = None) -> int:
    """
    Returns an approximation of the time in milliseconds since the Unix epoch (January 1, 1970 at midnight UTC time).
    If no dt argument is provided or it is None, the current time is used. If the dt argument is timezone-naive, it is
    assumed to be in the system timezone. Dates before the epoch are represented by negative numbers.

    Typically, the accuracy of this function depends on the underlying platform and python implementation. For
    example, most modern operating systems assume that 1 day = 24 * 60 * 60 = 86400 seconds, not taking leap seconds
    into account. Additional factors may include multitasking and system overhead.

    :return: an integer.
    """
    return int(seconds_since_epoch(dt) * 1000)
millis_since_epoch = milliseconds_since_epoch


def parse_isoformat(date_string: str, tz: tzinfo | None = None, make_timezone_aware_ = True, date_only=False) -> date:
    """
    Parses an ISO 8601 formatted date string and returns a date object. If date_string has no time information, the
    returned object is a date object. If it has time information, the returned object is a datetime object with
    timezone information. If timezone information is not present, the system timezone is assumed.

    :param date_string: the ISO 8601 formatted date string.
    :param tz: the timezone to assign to the returned datetime object if no timezone information is in date_string.
    :param make_timezone_aware_: assign the returned datetime object the given timezone, or if None, the system
    timezone, if no timezone information is in date_string. If tz is provided and make_timezone_aware_ is False, tz is
    ignored.
    :param date_only: if True, assume date_string is a date with at most year, month, and day information. If True,
    tz and make_timezone_aware_ are ignored.
    :return: a date object.
    """
    try:
        return date.fromisoformat(date_string)
    except ValueError:
        try:
            return datetime.strptime(date_string, '%Y-%m').date()
        except ValueError:
            try:
                return datetime.strptime(date_string, '%Y').date()
            except ValueError:
                if date_only:
                    raise
                else:
                    try:
                        if make_timezone_aware_:
                            return make_timezone_aware(dateutil.parser.isoparse(date_string), tz=tz) # datetime.fromisoformat(date_string)
                        else:
                            return dateutil.parser.isoparse(date_string)
                    except AssertionError as e:
                        raise ValueError(f'Invalid datetime {date_string}') from e


def raise_if_none_or_empty_string(the_string: str | None) -> str:
    """
    Raises a ValueError if the_string is None or an empty string, otherwise returns the_string.

    :param the_string: the object to check.
    :return: the_string.
    """
    if not the_string:
        raise ValueError('cannot be None nor the empty string')
    else:
        return the_string


def raise_if_empty_string(the_string: str | None) -> str | None:
    """
    Raises a ValueError if the_string is an empty string, otherwise returns the_string.

    :param the_string: the object to check.
    :return: the_string.
    """
    if the_string == '':
        raise ValueError('cannot be the empty string')
    else:
        return the_string


T = TypeVar('T')


def raise_if_none(the_object: T | None) -> T:
    """
    Raises a ValueError if the_object is None, otherwise returns the_object.

    :param the_object: the object to check.
    :return: the_object.
    """
    if the_object is None:
        raise ValueError('Cannot be None')
    else:
        return the_object


class Sentinel:
    """A class for creating unique sentinel objects for use in default arguments when distinguishing between omitted
    keyword arguments and arguments when some value like None is passed. This module has a singleton, SENTINEL, that
    is available as a convenience for this purpose."""
    pass

SENTINEL = Sentinel()


@overload
def type_name_to_type(name: str) -> type[Any]: ...


@overload
def type_name_to_type(name: str, *, type_: type[T]) -> type[T]: ...


@overload
def type_name_to_type(name: str, *, type_: None) -> type[Any]: ...


def type_name_to_type(name: str, *, type_: type[Any] | None = None) -> type[Any]:
    """
    Takes a type name, including package and module, and returns the type object. A type name without a module is
    assumed to be in the __builtins__ module.

    :param name: the name of the type.
    :return: the type of the returned object. If type_ is None, the type of the returned object is Any. No check is
    performed of the actual type that is returned.
    :raises TypeError: if the type doesn't exist.
    """
    name_parts = name.rsplit('.', 1)
    try:
        if len(name_parts) == 2:
            mod_str, cls_str = name_parts
            result = getattr(importlib.import_module(mod_str), cls_str)
        else:
            if isinstance(__builtins__, dict):
                result = __builtins__[name_parts[0]]
            else:
                result = cast(type[Any], getattr(__builtins__, name_parts[0]))
    except (NameError, AttributeError, ModuleNotFoundError, ValueError, KeyError) as e:
        raise TypeError(f'Type doesn\'t exist: {name}') from e
    return cast(type[Any], result)


def type_to_type_name(cls: type[Any]) -> str:
    """
    Takes a type object and returns its name, including package and module. If the type is a built-in type, the name
    is returned without the module.

    :param cls: the type object.
    :return: the name of the type.
    """
    if cls.__module__ == 'builtins':
        return cls.__name__
    else:
        return f'{cls.__module__}.{cls.__qualname__}'


def raise_if_not_subclass(cls: type[Any], cls_or_tuple: type[Any]):
    """
    Calls issubclass with the cls and cls_or_tuple arguments, and raises a TypeError if the result is not a subclass of
    cls_or_tuple.
    """
    if not issubclass(cls, cls_or_tuple):
        raise TypeError(f'result must be {cls_or_tuple}, but was {cls}')


def get_locale(locale_: str | None = None, category=locale.LC_CTYPE) -> str:
    """
    Returns the current locale of the given category (locale.LC_*) as a string. If the given locale is None, the system
    locale is returned.  If the system locale is unset, en_US is returned.

    :param locale: the current locale as a str.
    :param category: the category of locale (default is locale.LC_CTYPE).
    """
    if category is None:
        category_ = locale.LC_CTYPE
    else:
        category_ = int(category)
    if locale_ is not None:
        locale__ = locale_
    elif (system_locale := locale.getlocale(category_)[0]) is not None:
        locale__ = system_locale
    else:
        locale__ = DEFAULT_LOCALE
    return locale__


class ListWithBackingSet(UserList, Generic[T]):
    """
    A list with a backing set to ensure uniqueness of elements. This class.
    """

    def __init__(self, initial_data: Iterable[T] | None = None):
        """
        Constructor for ListWithBackingSet. If initial_data is provided, it is used to initialize the list and
        backing set. Duplicates in the initial data are removed.

        :param initial_data: an optional iterable of strings to initialize the list and backing set.
        """
        backing_set = set(initial_data) if initial_data is not None else set()
        super().__init__(backing_set)
        self.__backing_set = backing_set

    def __contains__(self, item: object) -> bool:
        """
        Checks if an item is in the list, using the backing set for O(1) lookup.
        """
        return item in self.__backing_set

    def append(self, item: T) -> None:
        """
        Appends an item to the list, ensuring uniqueness and using the backing set for O(1) lookup.
        """
        if item not in self.__backing_set:
            self.__backing_set.add(item)
            super().append(item)

    def remove(self, item: T) -> None:
        """
        Removes an item from the list, using the backing set for O(1) lookup. If the item is not present, this
        operation does nothing.
        """
        if item in self.__backing_set:
            self.__backing_set.remove(item)
            super().remove(item)

    def __eq__(self, other: object) -> bool:
        """
        Checks if this list is equal to another list or ListWithBackingSet, based on the backing set.

        :param other: the other list or ListWithBackingSet to compare to.
        :return: True if the lists are equal, False otherwise.
        """
        if isinstance(other, ListWithBackingSet):
            return self.__backing_set == other.__backing_set
        if isinstance(other, list):
            return self.__backing_set == set(other)
        return False


def mangled(cls: type | str, name: str) -> str:
    """
    Applies Python private variable name mangling to the given private variable name.

    :param cls: The class or class name.
    :param name: The private variable name.
    :return: The mangled variable name.
    """
    cls_name = cls.__name__ if isinstance(cls, type) else str(cls)
    return f'_{cls_name.lstrip("_")}{name}'
