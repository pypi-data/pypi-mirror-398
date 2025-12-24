#!/usr/bin/env python


class UnsupportedError(Exception):
    """
    Exception raised when an unsupported operation or feature is encountered.

    This error should be used to indicate that a particular functionality is not
    supported by the current implementation.
    """

    pass
