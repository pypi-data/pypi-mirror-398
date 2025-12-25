class HEAException(Exception):
    """Parent exception for custom exceptions raised by HEA."""
    pass

class HEAObjectException(HEAException):
    """Parent exception for any exception having to do with HEA objects."""
    pass


class DeserializeException(HEAObjectException):
    """Error while deserializing a HEA object."""
    pass

