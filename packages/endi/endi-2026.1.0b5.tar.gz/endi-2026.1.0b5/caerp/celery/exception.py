# -*- coding: utf-8 -*-
"""
Custom exceptions
"""


class BaseMessageException(Exception):
    def __init__(self, message=""):
        self.message = message


class FileNameException(BaseMessageException):
    pass


class MissingMandatoryArgument(BaseMessageException):
    """
    Raised when a mandatory argument is missing
    """

    pass


class InstanceNotFound(BaseMessageException):
    """
    Raised when no instance could be found
    """

    pass


class MultipleInstanceFound(BaseMessageException):
    """
    Raised when no instance could be found
    """

    pass
