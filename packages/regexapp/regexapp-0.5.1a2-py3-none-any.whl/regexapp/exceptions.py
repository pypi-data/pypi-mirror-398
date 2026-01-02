"""
regexapp.exceptions
===================
Exception classes for the regexapp project.

This module defines a hierarchy of custom exceptions used throughout
regexapp to handle errors related to pattern conversion, template
building, user/test data validation, and regex construction. These
exceptions provide more granular error reporting than built-in
exceptions, making debugging and error handling clearer.
"""


class PatternError(Exception):
    """Base exception for errors encountered during pattern conversion."""


class EscapePatternError(PatternError):
    """Raised when an error occurs while performing soft regex escaping."""


class PatternReferenceError(PatternError):
    """Raised when a PatternReference instance fails or is invalid."""


class TextPatternError(Exception):
    """Raised when text-based pattern conversion fails."""


class ElementPatternError(Exception):
    """Raised when element-level pattern conversion fails."""


class LinePatternError(PatternError):
    """Raised when line-based pattern conversion fails."""


class MultilinePatternError(PatternError):
    """Raised when multiline pattern conversion fails."""


class PatternBuilderError(PatternError):
    """Raised when errors occur during pattern building operations."""


class RegexBuilderError(Exception):
    """Raised when the RegexBuilder class encounters an error."""


class NoUserDataError(Exception):
    """Raised when required user data is missing or not provided."""


class NoTestDataError(Exception):
    """Raised when required test data is missing or not provided."""
