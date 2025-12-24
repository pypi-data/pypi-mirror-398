"""
Implements logging utilities for the validation process.
"""


class LoggerConfig:
    """
    Defines the configuration for the logger.
    """
    INCLUDE_SYMBOLS = True
    SILENT = False


def set_symbol_condition(include: bool):
    """
    This sets the include_symbols to specify which logger to use throughout
    the validation process.

    Parameters
    ----------
    include: bool
        This is the condition to set include_symbols.
    """
    LoggerConfig.INCLUDE_SYMBOLS = include


def set_silent_condition(silent: bool):
    """
    This sets the silent condition to specify whether
    to log messages or not.

    Parameters
    ----------
    silent: bool
        This is the condition to set silent.
    """
    LoggerConfig.SILENT = silent


def logger(message: str, code: str = ''):
    """
    Logs information to the terminal of the following types.

    - Error
    - Warning
    - Info
    - Success

    Parameters
    ----------
    message: str
        The message to print to the terminal.
    code: str
        The type of the message (error, warning, info, success).
    """
    if not LoggerConfig.SILENT:
        if LoggerConfig.INCLUDE_SYMBOLS:
            logger_with_symbols(message, code)
        else:
            logger_no_symbols(message, code)


def logger_with_symbols(message: str, code: str = ''):
    """
    Logs information to the terminal of the following types.

    - Error
    - Warning
    - Info
    - Success

    Parameters
    ----------
    message: str
        The message to print to the terminal.
    code: str
        The type of the message (error, warning, info, success).
    """

    if code.upper() == 'ERROR':
        print(f'\t - ❌ {message}')
        exit(1)
    elif code.upper() == 'WARNING':
        print(f'\t - ⚠️ {message}')
    elif code.upper() == 'INFO':
        print(f'\t - ℹ️ {message}')
    elif code.upper() == 'SUCCESS':
        print(f'\t - ✅ {message}')
    else:
        print(f'\t - {message}')


def logger_no_symbols(message: str, code: str = ''):
    """
    Logs information to the terminal of the following types.

    - Error
    - Warning
    - Info
    - Success

    Parameters
    ----------
    message: str
        The message to print to the terminal.
    code: str
        The type of the message (error, warning, info, success).
    """
    if code.upper() == 'ERROR':
        print(f'\t - [ERROR]: {message}')
        exit(1)
    elif code.upper() == 'WARNING':
        print(f'\t - [WARNING]: {message}')
    elif code.upper() == 'INFO':
        print(f'\t - [INFO]: {message}')
    elif code.upper() == 'SUCCESS':
        print(f'\t - [SUCCESS]: {message}')
    else:
        print(f'\t - {message}')
