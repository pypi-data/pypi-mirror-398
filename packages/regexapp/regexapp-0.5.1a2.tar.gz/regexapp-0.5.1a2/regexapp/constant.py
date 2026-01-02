"""
regexapp.constant
=================

Centralized definitions of constants used throughout the `regexapp` package.

Notes
-----
Keeping constants in a dedicated module makes it easier to update
values globally and provides a single source of truth for the
application’s configuration and error handling.
"""

from genericlib.constant import ICSValue


class FWTYPE:
    """
    Enumeration of supported test framework types.

    This class defines symbolic constants for the test frameworks
    recognized by the application. Each constant is represented by
    an `ICSValue` instance, which provides both a canonical name
    and optional shorthand.

    Attributes
    ----------
    UNITTEST : ICSValue
        Represents the built-in Python `unittest` framework.
    PYTEST : ICSValue
        Represents the `pytest` framework.
    ROBOTFRAMEWORK : ICSValue
        Represents the `Robot Framework` testing tool. Includes both
        the full name ("robotframework") and shorthand ("rf").
    """
    UNITTEST = ICSValue('unittest')
    PYTEST = ICSValue('pytest')
    ROBOTFRAMEWORK = ICSValue('robotframework', 'rf')


class FORMATTYPE:
    """
    Enumeration of supported data format types.

    This class defines symbolic constants for the data formats
    recognized by the application. Each constant is represented by
    an `ICSValue` instance, which provides both a canonical name
    and optional shorthand.

    Attributes
    ----------
    CSV : ICSValue
        Represents the `CSV` (comma-separated values) format.
    JSON : ICSValue
        Represents the `JSON` (JavaScript Object Notation) format.
    YAML : ICSValue
        Represents the `YAML` format. Includes both the full name
        ("yaml") and shorthand ("yml").
    TEMPLATE : ICSValue
        Represents a generic `template` format used for custom
        or user-defined structures.
    """
    CSV = ICSValue('csv')
    JSON = ICSValue('json')
    YAML = ICSValue('yaml', 'yml')
    TEMPLATE = ICSValue('template')
