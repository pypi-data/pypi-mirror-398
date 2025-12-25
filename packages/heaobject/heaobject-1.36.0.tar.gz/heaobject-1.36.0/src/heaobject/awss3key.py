'''
Functions for manipulating Amazon Simple Storage Service (S3) keys. None and the empty string are both considered the
root "folder" of a bucket.
'''

import binascii
from base64 import urlsafe_b64encode, urlsafe_b64decode
from typing import Optional
from os.path import split as _split


S3_BUCKET_OBJECT_KEY_ENCODING = 'utf-8'


class KeyDecodeException(Exception):
    """
    Raised if decoding an HEAObject id or name string to an AWS S3 bucket object key failed. A possible nested
    exception may provide more details about why, but the types of nested exception raised are specific to the
    decoding algorithm implementation and are not part of HEA's public API.
    """
    pass


def encode_key(key: str) -> str:
    """
    Encodes an AWS S3 bucket object key to a string that can be inserted into URL paths. Bucket keys are /-separated
    paths, and URLs with escaped slashes are rejected or handled incorrectly by many servers and clients. This
    function encodes bucket keys using URL-safe base 64 encoding described in the IETF RFC 4648 specification section
    5, which replaces '+' with '-' and '/' with '_' in the base 64 alphabet, and UTF-8 string encoding.

    :param key: an AWS S3 bucket key.
    :return: the encoded string.
    """
    return urlsafe_b64encode(key.encode(S3_BUCKET_OBJECT_KEY_ENCODING)).decode(S3_BUCKET_OBJECT_KEY_ENCODING)


def decode_key(encoded_key: str) -> str:
    """
    Decodes the provided string to an AWS S3 object bucket key. This implementation uses URL-safe base 64 decoding,
    described in the IETF RFC 4648 specification section 5, which replaces '+' with '-' and '/' with '_' in the base 64
    alphabet, and UTF-8 string encoding.

    :param encoded_key: the encoded key (required).
    :return: the actual AWS S3 bucket key.
    :raises KeyDecodeException: if the provided string could not be decoded.
    """
    try:
        return urlsafe_b64decode(encoded_key.encode(S3_BUCKET_OBJECT_KEY_ENCODING)).decode(S3_BUCKET_OBJECT_KEY_ENCODING)
    except (UnicodeDecodeError, binascii.Error) as e:
        raise KeyDecodeException(f'Failed to decode {encoded_key} to an AWS S3 bucket key') from e


def is_folder(key: Optional[str]) -> bool:
    """
    Returns whether the provided key represents a folder (ends with a / or is None or the empty string).

    :param key: the key.
    :return: True if the key represents a folder, False if not.
    """
    key_ = str(key) if key else ''
    return (not key_) or key_.endswith('/')


def split(key: str | None) -> tuple[str, str]:
    """
    Splits the key's pathname into a pair, (head, tail), where tail is the last pathname component and head is
    everything leading up to that. Splitting the root folder of a bucket ('' or None) will return ('', '').

    :param key: the key to split.
    :return: a two-tuple containing the head and the tail. If the object is at the root of the bucket, then the head
    will be the empty string.
    """

    def is_non_root_folder(key: str | None) -> bool:
        return is_folder(key) and not is_root(key)

    # None is not a non-root folder.
    if is_non_root_folder(key):
        key_ = key.rstrip('/')  # type:ignore[union-attr]
    else:
        key_ = key
    result = _split(key_ if key_ else '')
    return result[0] + ('/' if result[0] else ''), (result[1] + '/') if is_non_root_folder(key) else result[1]


def display_name(key: str) -> str:
    """
    Returns the object's display name. Equivalent to split(key)[1].rstrip('/').
    """
    return split(key)[1].rstrip('/')


def join(head: str | None, tail: str | None) -> str:
    """
    Join a folder head to an object tail.

    :param head: the head. If None or the empty string, the head is assumed to be the root folder of a bucket.
    :param tail: the tail. None and the empty string are equivalent.
    :return: the resulting key.
    :raises ValueError: if the head is not a folder.
    """
    if head and not head.endswith('/'):
        raise ValueError(f'head must be a folder but was {head}')
    return f'{head if head else ""}{tail if tail else ""}'


def suffix(prefix: str | None, key: str | None) -> str | None:
    """
    Remove the prefix folder from the key. If the prefix folder is None, the key is returned.

    :param prefix: the prefix folder, or None or the empty string to indicate the root of the bucket.
    :param key: the key (required).
    :return: the resulting key.
    """
    if prefix is None:
        return key
    if prefix and not is_folder(prefix):
        raise ValueError('prefix must be a folder')
    return (key or '').removeprefix(prefix)


def replace_parent_folder(source_key: str | None, target_key: str | None, source_key_folder: str | None) -> str:
    """
    Replace a source key's folder with the target key folder, such as in an object copy.

    :param source_key: the source key (required). None or the empty string means the root folder of a bucket.
    :param target_key: the key of the target folder (required). None or the empty string means the root folder of a
    bucket.
    :param source_key_folder: the source folder whose contents to copy. None or the empty string means the root folder
    of a bucket.
    :return: the resulting key.
    """
    if not is_folder(target_key):
        raise ValueError(f'target_key {target_key} must be a folder')
    if source_key_folder and source_key and not source_key.startswith(source_key_folder):
        raise ValueError(f'Mismatched source_key {source_key} and source_key_folder {source_key_folder}')
    if source_key is None and source_key_folder is not None:
        raise ValueError(f'Mismatched source_key {source_key} and source_key_folder {source_key_folder}')
    return join(target_key, suffix(source_key_folder, source_key))


def is_in_root_of_bucket(key: str) -> bool:
    """
    Whether the given key is in the root "folder" of the bucket.

    :param key: a key (required).
    :return: whether the key is in the root "folder" of the bucket.
    """
    return split(key if key else '')[0] == ''


def is_root(key) -> bool:
    """
    Return whether the given key is the root folder of the bucket ('' or None).
    :return True or False.
    """
    return not key


def parent(key: str | None) -> str:
    """
    Gets the parent folder of the object with the given key.

    :param key: the key.
    :return: the parent folder.
    """
    if not key:
        return ''
    return split(key)[0]


def is_object_in_folder(key: str | None, folder_key: str | None) -> bool:
    """
    Returns whether an object is in the given folder. This function does not query S3. It answers the question using
    only the relationship between the object's key and folder's key. It only checks the parent folder and not any of
    its subfolders.

    :param key: the object's key.
    :param folder_key: the folder's key.
    """
    try:
        return parent(key) == (folder_key or '')
    except ValueError:
        return False
