"""
Utility functions for handling the mime types of heaobject.data.Data objects.
"""
from xdg import Mime


DEFAULT_MIME_TYPE = 'application/octet-stream'


def guess_mime_type(url: str) -> str:
    """
    Returns the mime type for the given URL, file name, or path, based on the file extension.

    :param url: the file path or URL (required).
    :returns: the mime type.
    """
    if url is None:
        raise ValueError("The 'url' parameter must not be None.")
    try:
        result = str(Mime.get_type2(url))
    except Exception:
        result = None

    return result or DEFAULT_MIME_TYPE

def get_description(mime_type: str) -> str | None:
    """
    Returns a human-readable description for a given MIME type.

    :param mime_type: The MIME type to describe.
    :returns: A friendly description string, or None if unknown.
    """
    try:
        mimetype_obj = Mime.MIMEtype(*mime_type.split('/'))
        if str(mimetype_obj) == 'application/octet-stream':
            raise ValueError  # No description for generic binary data
        result = mimetype_obj.get_comment()
    except:
        return None

    if result == str(mimetype_obj):
        return result
    else:
        return ' '.join(word[0].upper() + word[1:] for word in result.split())
