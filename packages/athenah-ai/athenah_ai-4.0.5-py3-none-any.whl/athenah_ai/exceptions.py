#!/usr/bin/env python
# coding: utf-8


class AppException(Exception):
    """
    Base class for all exceptions in the application.
    """

    def __init__(self, message, error_code=0, detail=""):
        """
        Initialize the exception.

        :param message: The message to display to the user.
        :param error_code: The error code to return to the user.
        :param detail: The detailed message to display to the user.
        """
        super(AppException, self).__init__(message)

        self.error_code = error_code
        self.detail = detail
        self.message = message


class AuthorizationException(AppException):
    """
    Exception for authorization errors.
    """

    def __str__(self):
        """
        Return the string representation of the exception.

        :return: The string representation of the exception.
        """
        return (
            "Firebase Auth Exception: " + self.message + " \n\n" + self.detail
        )  # noqa


class UnsupportedException(AppException):
    """
    Exception for unsupported errors.
    """

    pass


class GeneralException(AppException):
    """
    Exception for general errors.
    """

    pass


class ValidationException(AppException):
    """
    Exception for validation errors.
    """

    pass


class SevereException(AppException):
    """
    Exception for severe errors.
    """

    pass


class InternalServerException(AppException):
    """
    Exception for internal server errors.
    """

    pass


class NotFoundException(AppException):
    """
    Exception for not found errors.
    """

    pass
