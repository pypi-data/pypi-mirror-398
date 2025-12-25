"""
Module enumerating all possible exceptions raised
directly by Rug.
"""


class RugException(Exception):
    """
    Base exception which is extended by every other Rug exception.
    """


class HttpException(RugException):
    """
    General HTTP exception which is raised when something goes
    wrong - for example the connection was refused.
    """


class SymbolNotFound(RugException):
    """
    Specific exception indicating requested data for the given
    symbol was not found because the symbol doesn't exist.
    """


class DataException(RugException):
    """
    Generic exception for cases where scraped data from the net
    are not as we expect them.
    """
