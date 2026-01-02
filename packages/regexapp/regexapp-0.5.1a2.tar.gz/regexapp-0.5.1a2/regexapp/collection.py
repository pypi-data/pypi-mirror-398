"""
regexapp.collection
===================

Core collection of regex pattern classes and builders for the `regexapp`
library. This module defines abstractions for representing, composing,
and managing text patterns, enabling both programmatic construction and
user‑defined customization.

Classes
-------
TextPattern
    Represents a single regex pattern applied to plain text.
ElementPattern
    Encapsulates regex logic for structured elements (e.g., tokens, fields).
LinePattern
    Provides regex matching and validation at the line level.
MultilinePattern
    Supports multi‑line regex patterns with contextual awareness.
PatternBuilder
    Utility for dynamically constructing and combining regex patterns.
PatternReference
    Handles references to predefined or user‑customized regex patterns.

Notes
-----
- Patterns can be customized by end‑users via YAML configuration files:
  - System defaults: `system_references.yaml`
  - User overrides: `~/.geekstrident/regexapp/user_references.yaml`
- The module is designed to integrate with `regexapp.core.RegexBuilder`
  and `DynamicTestScriptBuilder` for generating test scripts and regex
  workflows.
- All classes follow a consistent API to support extensibility and
  maintainability across the application.
"""


import re
from typing import Optional, Type

import yaml
import string
from copy import copy

from regexapp.exceptions import EscapePatternError
from regexapp.exceptions import PatternReferenceError
from regexapp.exceptions import TextPatternError
from regexapp.exceptions import ElementPatternError
from regexapp.exceptions import LinePatternError
from regexapp.exceptions import MultilinePatternError
from regexapp.exceptions import PatternBuilderError
from regexapp.config import Data

import regexapp.utils as utils

from genericlib import File
from genericlib.text import WHITESPACE_CHARS
from genericlib.text import Line
from genericlib.text import dedent_and_strip
from genericlib.exceptions import raise_exception

import logging
logger = logging.getLogger(__file__)


def validate_pattern(
    pattern: str,
    flags: int = 0,
    exception_cls: Optional[Type[Exception]] = None
) -> re.Pattern | None:
    """
    Validate and compile a regular expression pattern.

    Attempts to compile the given regex pattern with optional flags.
    If compilation fails, raises the specified exception class with
    a descriptive error message.

    Parameters
    ----------
    pattern : str
        The regex pattern string to validate.
    flags : int, default 0
        Regex compilation flags (e.g., `re.IGNORECASE`, `re.MULTILINE`).
    exception_cls : Type[Exception], optional
        Custom exception class to raise on failure. Defaults to `Exception`.

    Returns
    -------
    re.Pattern or None
        The compiled regex pattern object if validation succeeds.

    Raises
    ------
    Exception
        If the pattern is invalid and cannot be compiled. The raised
        exception type is `exception_cls`.
    """
    exception_cls = exception_cls or Exception
    try:
        return re.compile(pattern, flags=flags)
    except re.error as ex:
        raise_exception(ex, cls=exception_cls)


def do_soft_regex_escape(pattern: str, is_validated: bool = True) -> str:
    """
    Escape special characters in a regex pattern string.

    This function provides a "soft" escape mechanism that ensures
    consistency across Python versions when invoking `re.escape`.
    It selectively escapes characters that are meaningful in regex
    syntax while leaving harmless punctuation unchanged.

    Parameters
    ----------
    pattern : str
        The input regex pattern string to escape.
    is_validated : bool, default True
        Whether to validate the escaped pattern using `validate_pattern`.
        If True, raises `EscapePatternError` on invalid patterns.

    Returns
    -------
    str
        A new regex pattern string with special characters escaped.

    Raises
    ------
    EscapePatternError
        If validation fails when `is_validated=True`.

    Notes
    -----
    - Characters in `string.punctuation` and whitespace are checked.
    - Regex metacharacters (e.g., `^`, `$`, `.`, `?`, `*`, `+`, `|`,
      `{}`, `[]`, `()`, `\\`) are always escaped.
    - Other punctuation is left as‑is for readability.
    """
    pattern = str(pattern)

    all_punct_or_space = string.punctuation + " "
    special_regex_chars = "^$.?*+|{}[]()\\"

    result = []
    for char in pattern:
        escaped = re.escape(char)
        if char in all_punct_or_space:
            result.append(escaped if char in special_regex_chars else char)
        else:
            result.append(escaped)

    new_pattern = "".join(result)

    if is_validated:
        validate_pattern(new_pattern, exception_cls=EscapePatternError)

    return new_pattern


class VarCls:
    """
    Container class for storing variables associated with regex patterns.

    This class encapsulates a variable name, its associated regex pattern,
    and an optional assignment option. It provides convenience properties
    for checking emptiness, formatting values, and generating a variable
    reference string.

    Parameters
    ----------
    name : str, optional
        The variable name. Default is an empty string.
    pattern : str, optional
        A regex pattern associated with the variable. Default is an empty string.
    option : str, optional
        An option string for value assignment. Underscores are normalized
        to commas, and capitalization is standardized. Default is an empty string.

    Attributes
    ----------
    name : str
        The variable name.
    pattern : str
        The regex pattern associated with the variable.
    option : str
        The normalized option string for value assignment.

    Methods
    -------
    is_empty() -> bool
        Returns True if the variable name is empty, False otherwise.
    value() -> str
        Returns a formatted string representation of the variable,
        including its option (if present), name, and pattern.
    var_name() -> str
        Returns the variable name wrapped in `${...}` syntax.
    """

    def __init__(self, name='', pattern='', option=''):
        self.name = str(name).strip()
        self.pattern = str(pattern)
        self.option = ','.join(re.split(r'\s*_\s*', str(option).title()))
        self.option = self.option.replace(' ', '')

    @property
    def is_empty(self):
        """
        Check whether the variable name is empty.

        This property evaluates whether the `name` attribute of the
        variable has been set. It is useful for quickly determining
        if the instance represents a defined variable or a placeholder.

        Returns
        -------
        bool
            True if the variable name is an empty string, False otherwise.
        """
        return self.name == ''

    @property
    def value(self):
        """
        Return a formatted string representation of the variable.

        If an option is present, it is normalized (underscores converted
        to commas, capitalization standardized, and spaces removed) and
        included in the output. Otherwise, only the variable name and
        pattern are shown.

        Returns
        -------
        str
            A formatted string describing the variable.
        """
        if self.option:
            return f"Value {self.option} {self.name} ({self.pattern})"
        else:
            return f"Value {self.name} ({self.pattern})"

    @property
    def var_name(self) -> str:
        """
        Return the variable name wrapped in `${...}` syntax.

        Returns
        -------
        str
            The variable name enclosed in `${}` for use in
            template or substitution contexts.
        """
        return f"${{{self.name}}}"


class PatternReference(dict):
    """
    Dictionary-like container for managing regular expression patterns.

    This class is used to load and store regex patterns defined in
    `system_references.yaml` and/or `user_references.yaml`. It provides
    utility methods for loading references, retrieving pattern layouts,
    validating input against patterns, and testing content.

    Attributes
    ----------
    sys_ref_loc : str
        Path to the system references YAML file.
    user_ref_loc : str
        Path to the user references YAML file.

    Methods
    -------
    load_reference(filename) -> None
        Load regex patterns from the specified YAML file into the reference
        dictionary.
    get_pattern_layout(name) -> str
        Retrieve the layout string for a given pattern name.
    is_violated(dict_obj) -> bool
        Check whether the provided dictionary violates any stored pattern rules.
    test(content) -> bool
        Test whether the given content matches the stored patterns.

    Raises
    ------
    PatternReferenceError
        Raised if the reference file does not exist, cannot be read, or
        contains an invalid format.
    """

    # regexp pattern - from system references
    sys_ref_loc = Data.system_reference_filename
    # regex patterns - from user references
    user_ref_loc = Data.user_reference_filename

    def __init__(self):
        super().__init__()
        self.load_sys_ref()
        self.load_reference(self.user_ref_loc)
        self.test_result = ''
        self.violated_format = ''

    def load_sys_ref(self):
        """
        Load system reference patterns from the YAML file.

        Reads the system reference file specified by `self.sys_ref_loc`
        using `utils.File.safe_load_yaml`, then updates the current
        `PatternReference` instance with the loaded patterns.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If `filename` is empty after normalization.
        OSError
            If the file cannot be opened or read.
        yaml.YAMLError
            If the YAML content is invalid or cannot be parsed.
        """
        yaml_obj = utils.File.safe_load_yaml(self.sys_ref_loc)
        self.update(yaml_obj)

    def load_reference(self, filename, is_warning=True):
        """
        Load reference patterns from a YAML file.

        Reads the specified YAML reference file, validates its structure,
        and updates the current `PatternReference` instance with the loaded
        patterns. If the file does not exist and corresponds to the user
        reference location, a sample file is created and copied before loading.

        Parameters
        ----------
        filename : str
            Path to the YAML reference file.
        is_warning : bool, optional
            If True (default), log a warning when duplicate keys are found
            and skipped. If False, suppress warnings.

        Returns
        -------
        None
            This method updates the instance in place and does not return a value.

        Raises
        ------
        PatternReferenceError
            If the file does not exist (and is not the user reference file),
            if the YAML content is invalid, or if the content is not a dictionary.
        ValueError
            If `filename` is empty after normalization.
        OSError
            If the file cannot be read.
        yaml.YAMLError
            If the YAML content is invalid or cannot be parsed.

        Notes
        -----
        - Duplicate keys are not updated unless the key is `'datetime'`.
        - When `filename` matches `self.user_ref_loc` and the file is missing,
          a sample user keywords file is created automatically.
        """

        if not File.is_exist(filename):
            if filename == self.user_ref_loc:
                sample_file = Data.sample_user_keywords_filename
                File.create(filename)
                File.copy_file(sample_file, filename)
            else:
                msg = f"File '{filename}' not found."
                raise PatternReferenceError(msg)

        try:
            yaml_obj = utils.File.safe_load_yaml(filename)
            if not yaml_obj:
                return

            if not isinstance(yaml_obj, dict):
                msg = f"File '{filename}' must have a dictionary structure."
                raise PatternReferenceError(msg)

            for key, value in yaml_obj.items():
                if key not in self:
                    self[key] = value
                else:
                    if key == 'datetime':
                        self[key] = value
                    else:
                        fmt = ("%r key already exists. "
                               "Will not update data for key %r.")
                        is_warning and logger.warning(fmt, key, value)
        except Exception as ex:
            raise_exception(ex, cls=PatternReferenceError)

    @classmethod
    def get_pattern_layout(cls, name: str) -> str:
        """
        Return a YAML layout template for a given pattern name.

        Parameters
        ----------
        name : str
            The name of the pattern. If it contains 'datetime',
            a format-based layout is returned; otherwise a
            regex-based layout is returned.

        Returns
        -------
        str
            A YAML layout template string.
        """
        layout1 = dedent_and_strip("""
            name_placeholder:
              ##################################################################
              # double back flash must be used in a value of pattern if needed
              # positive test and/or negative test is/are optional
              ##################################################################
              group: "replace_me"
              description: "replace_me"
              pattern: "replace_me"
              # positive test:
              #   change this positive test name: "replace_me -> (string or list of string)"
              # negative test:
              #   change this negative test name: "replace_me -> (string or list of string)"
        """)
        layout2 = dedent_and_strip("""
            name_placeholder:
              ##################################################################
              # double back flash must be used in a value of format if needed
              # positive test and/or negative test is/are optional
              ##################################################################
              group: "replace_me"
              description: "replace_me"
              format: "replace_me"
              # format1: "replace_me"
              # format2: "replace_me"
              # formatn: "replace_me"
              # positive test:
              #   change this positive test name: "replace_me -> (string or list of string)"
              # negative test:
              #   change this negative test name: "replace_me -> (string or list of string)"
        """)

        return layout2 if 'datetime' in name else layout1

    def is_violated(self, dict_obj: dict) -> bool:
        """
        Check whether a new pattern reference conflicts with system references.

        This method compares the keys in the provided dictionary against
        the system reference file (`system_references.yaml`). If a key
        already exists in the system reference (excluding those containing
        'datetime'), the method records the violation message and returns True.

        Parameters
        ----------
        dict_obj : dict
            Dictionary of new pattern references to validate.

        Returns
        -------
        bool
            True if a violation is detected (duplicate key found),
            False otherwise.

        Raises
        ------
        ValueError
            If `filename` is empty after normalization.
        OSError
            If the file cannot be read.
        yaml.YAMLError
            If the YAML content is invalid or cannot be parsed.

        Notes
        -----
        - Keys containing 'datetime' are exempt from violation checks.
        - When a violation occurs, the message is stored in
          `self.violated_format` for later inspection.
        """
        sys_ref = utils.File.safe_load_yaml(self.sys_ref_loc)
        for name in dict_obj:
            if 'datetime' not in name:
                if name in sys_ref:
                    msg = f"Keyword '{name}' already exists in system_references.yaml."
                    self.violated_format = msg
                    return True
        return False

    def test(self, content: str) -> bool | None:
        """
        Validate a YAML content string against system pattern references.

        This method attempts to parse the provided YAML content and checks
        whether it conforms to the expected dictionary structure and does
        not violate existing system references. The test result is recorded
        in `self.test_result` as either `'tested'` or `'not_tested'`.

        Parameters
        ----------
        content : str
            A string containing YAML-formatted content to validate.

        Returns
        -------
        bool or None
            True if the content is valid or empty (skipped), False is never
            returned explicitly since violations raise exceptions.

        Raises
        ------
        PatternReferenceError
            If the content is invalid YAML, not a dictionary, or violates
            existing system references.

        Notes
        -----
        - Empty or missing YAML content is skipped, and the result is marked
          as `'not_tested'`.
        - Keys containing `'datetime'` are exempt from violation checks.
        - On success, the result is marked as `'tested'`.
        """

        try:
            yaml_obj = yaml.safe_load(content)
            if not yaml_obj:
                logger.warning("Skipping test: YAML content is empty or missing.")
                self.test_result = 'not_tested'
                return True

            if not isinstance(yaml_obj, dict):
                msg = "YAML content must be a dictionary structure."
                raise PatternReferenceError(msg)

            if self.is_violated(yaml_obj):
                raise PatternReferenceError(self.violated_format)

            self.test_result = 'tested'
            return True
        except Exception as ex:
            raise_exception(ex, cls=PatternReferenceError)


class SymbolCls(dict):
    """
    Dictionary-like container for symbol references loaded from `symbols.yaml`.

    This class loads the contents of the `symbols.yaml` file at initialization
    and stores them as key-value pairs, providing direct dictionary-style
    access to symbol definitions.

    Attributes
    ----------
    filename : str
        Path to the symbol reference file (`symbols.yaml`).
    """

    filename = Data.symbol_reference_filename

    def __init__(self):
        yaml_obj = utils.File.safe_load_yaml(self.filename)
        super().__init__(yaml_obj)


REF = PatternReference()

SYMBOL = SymbolCls()


class TextPattern(str):
    """
    A string subclass for converting text data into regex patterns.

    The `TextPattern` class provides utilities to treat plain text as
    regular expression patterns. It supports whitespace handling,
    concatenation, and validation, while allowing text to be used
    directly as a regex pattern if desired.

    Attributes
    ----------
    text : str
        The original text string.
    as_is : bool
        Whether to keep the text as an "AS-IS" regex pattern without
        modification.

    Methods
    -------
    is_empty() -> bool
        Check if the pattern matches an empty string.
    is_empty_or_whitespace() -> bool
        Check if the pattern matches an empty string or only whitespace.
    is_whitespace() -> bool
        Check if the pattern matches whitespace characters.
    get_pattern(text: str) -> str
        Return a regex pattern string derived from the given text.
    lstrip(chars: str | None = None) -> TextPattern
        Return a copy with leading characters removed.
    rstrip(chars: str | None = None) -> TextPattern
        Return a copy with trailing characters removed.
    strip(chars: str | None = None) -> TextPattern
        Return a copy with leading and trailing characters removed.
    add(other: str, as_is: bool = True) -> TextPattern
        Append another string or pattern to the current text.
    concatenate(*other: str, as_is: bool = True) -> TextPattern
        Concatenate multiple strings or patterns into a single `TextPattern`.

    Raises
    ------
    TextPatternError
        Raised if the text cannot be converted into a valid regex pattern.
    """
    def __new__(cls, text, as_is=False):
        """
        Create a new `TextPattern` instance.

        Converts the given text into a regex pattern string unless `as_is`
        is set to True. When `as_is=True`, the text is preserved exactly
        without conversion. This ensures that `TextPattern` objects can be
        initialized either as raw strings or as regex‑ready patterns.

        Parameters
        ----------
        text : str
            Input text to be converted into a regex pattern or preserved
            as-is.
        as_is : bool, optional
            If True, keep the text unchanged as the pattern. If False
            (default), convert the text into a regex pattern using
            `TextPattern.get_pattern`.

        Returns
        -------
        TextPattern
            A new `TextPattern` instance containing either the original
            text or its regex pattern representation.

        Raises
        ------
        TextPatternError
            If the text cannot be converted into a valid regex pattern.
        """
        data = str(text)
        if as_is:
            return str.__new__(cls, data)
        text_pattern = cls.get_pattern(data) if data else ''
        return str.__new__(cls, text_pattern)

    def __init__(self, text, as_is=False):
        self.text = text
        self.as_is = as_is

    def __add__(self, other):
        """
        Concatenate this `TextPattern` with another string.

        Overrides the `+` operator to ensure that the result of concatenation
        is returned as a new `TextPattern` instance rather than a plain string.
        The concatenated result is preserved as-is without further regex
        conversion.

        Parameters
        ----------
        other : str
            The string to append to this `TextPattern`.

        Returns
        -------
        TextPattern
            A new `TextPattern` instance containing the concatenated text.
        """
        result = super().__add__(other)
        result_pat = TextPattern(result, as_is=True)
        return result_pat

    def __radd__(self, other):
        """
        Right-side concatenation with a `TextPattern`.

        Implements the reversed addition operator (`__radd__`) so that
        concatenation works when a `TextPattern` instance appears on the
        right-hand side of the `+` operator. This ensures consistent
        behavior whether the left operand is a plain string or another
        `TextPattern`.

        Parameters
        ----------
        other : str or TextPattern
            The left-hand operand to concatenate with this `TextPattern`.

        Returns
        -------
        TextPattern
            A new `TextPattern` instance containing the concatenated text.
        """
        if isinstance(other, TextPattern):
            return other.__add__(self)
        else:
            other_pat = TextPattern(other, as_is=True)
            return other_pat.__add__(self)

    @property
    def is_empty(self):
        """
        Check whether the pattern matches an empty string.

        This property evaluates if the current `TextPattern` instance
        represents an empty string or a regex pattern that can match
        an empty string. It is useful for quickly determining whether
        the pattern has any meaningful content.

        Returns
        -------
        bool
            True if the pattern is empty or matches an empty string,
            False otherwise.
        """
        if self == '':
            return True
        else:
            result = re.match(str(self), '')
            return bool(result)

    @property
    def is_space(self):
        """
        Determine whether the pattern matches a single space character.

        This property evaluates if the current `TextPattern` instance
        corresponds to a literal space (`' '`) or a regex that can match
        a space character. It is useful for distinguishing between patterns
        that represent spacing and those that do not.

        Returns
        -------
        bool
            True if the pattern matches a single space character,
            False otherwise.
        """
        is_space = bool(re.match(self, ' '))
        return is_space

    @property
    def is_empty_or_space(self):
        """
        Determine whether the pattern matches an empty string or a single space.

        This property evaluates if the current `TextPattern` instance
        corresponds to either an empty string or a regex pattern that
        matches a single space character. It is useful for identifying
        patterns that represent minimal or trivial spacing content.

        Returns
        -------
        bool
            True if the pattern matches an empty string or a single space,
            False otherwise.
        """
        is_empty = self.is_empty
        is_space = self.is_space
        return is_empty or is_space

    @property
    def is_whitespace(self):
        """
        Determine whether the pattern matches whitespace characters.

        This property evaluates if the current `TextPattern` instance
        corresponds to a regex pattern that can match all defined
        whitespace characters (e.g., spaces, tabs, newlines). It is
        useful for distinguishing patterns that represent only
        whitespace content.

        Returns
        -------
        bool
            True if the pattern matches all recognized whitespace
            characters, False otherwise.
        """
        is_ws = all(True for c in WHITESPACE_CHARS if re.match(self, c))
        return is_ws

    @property
    def is_empty_or_whitespace(self):
        """
        Determine whether the pattern matches an empty string or only whitespace.

        This property evaluates if the current `TextPattern` instance
        corresponds to either an empty string or a regex pattern that
        matches whitespace characters. It is useful for identifying
        patterns that represent minimal or non-substantive content.

        Returns
        -------
        bool
            True if the pattern matches an empty string or whitespace,
            False otherwise.
        """
        is_empty = self.is_empty
        is_ws = self.is_whitespace
        return is_empty or is_ws

    @classmethod
    def get_pattern(cls, text):
        """
        Convert text into a regex pattern string.

        This class method processes the input text and transforms it into
        a regex pattern. Line segments are converted individually, while
        newline sequences are represented with quantified regex groups.
        The resulting pattern is validated to ensure correctness.

        Parameters
        ----------
        text : str
            Input text to be converted into a regex pattern.

        Returns
        -------
        str
            A regex pattern string derived from the input text.

        Raises
        ------
        TextPatternError
            If the generated regex pattern is invalid.
        """
        text_pattern = ''
        start = 0
        m = None
        for m in re.finditer(r'[\r\n]+', text):
            pre_match = text[start:m.start()]
            if pre_match:
                text_pattern += Line(pre_match).convert_to_regex_pattern()
            match = m.group()
            multi = '{1,2}' if len(match) == len(set(match)) else '{2,}'
            text_pattern += f'[\\r\\n]{multi}'
        if m:
            post_match = text[m.end():]
            if post_match:
                text_pattern += Line(post_match).convert_to_regex_pattern()
        else:
            text_pattern = Line(text).convert_to_regex_pattern()

        validate_pattern(text_pattern, exception_cls=TextPatternError)
        return text_pattern

    @classmethod
    def get_pattern_bak(cls, text):
        """convert data to regex pattern

        Parameters
        ----------
        text (str): a text

        Returns
        -------
        str: a regex pattern.

        Raises
        ------
        TextPatternError: raise an exception if pattern is invalid.
        """
        start = 0
        result = []
        for item in re.finditer(r'\s+', text):
            before_matched = text[start: item.start()]
            before_matched and result.append(do_soft_regex_escape(before_matched))
            matched = item.group()
            total = len(matched)
            lst = list(matched)
            is_space = lst[0] == ' ' and len(set(lst)) == 1
            is_space and result.append(' ' if total == 1 else ' +')
            not is_space and result.append(r'\s' if total == 1 else r'\s+')
            start = item.end()
        else:
            if result:
                after_matched = text[start:]
                after_matched and result.append(do_soft_regex_escape(after_matched))
            else:
                result.append(do_soft_regex_escape(text))

        text_pattern = ''.join(result)

        validate_pattern(text_pattern, exception_cls=TextPatternError)
        return text_pattern

    def lstrip(self, chars=None):
        """
        Return a copy of the `TextPattern` with leading characters removed.

        By default, leading whitespace is removed. If `chars` is provided,
        all leading characters found in `chars` are removed instead. The
        result is returned as a new `TextPattern` instance.

        Parameters
        ----------
        chars : str, optional
            A string specifying the set of characters to remove from the
            beginning of the text. If None (default), leading whitespace
            characters are removed.

        Returns
        -------
        TextPattern
            A new `TextPattern` instance with leading characters removed.
        """

        new_text = self.text.lstrip() if chars is None else self.text.lstrip(chars)
        pattern = TextPattern(new_text)
        return pattern

    def rstrip(self, chars=None):
        """
        Return a copy of the `TextPattern` with trailing characters removed.

        By default, trailing whitespace is removed. If `chars` is provided,
        all trailing characters found in `chars` are removed instead. The
        result is returned as a new `TextPattern` instance.

        Parameters
        ----------
        chars : str, optional
            A string specifying the set of characters to remove from the
            end of the text. If None (default), trailing whitespace
            characters are removed.

        Returns
        -------
        TextPattern
            A new `TextPattern` instance with trailing characters removed.
        """
        new_text = self.text.rstrip() if chars is None else self.text.rstrip(chars)
        pattern = TextPattern(new_text)
        return pattern

    def strip(self, chars=None):
        """
        Return a copy of the `TextPattern` with leading and trailing characters removed.

        By default, both leading and trailing whitespace are removed. If `chars`
        is provided, all leading and trailing characters found in `chars` are
        removed instead. The result is returned as a new `TextPattern` instance.

        Parameters
        ----------
        chars : str, optional
            A string specifying the set of characters to remove from both
            ends of the text. If None (default), leading and trailing
            whitespace characters are removed.

        Returns
        -------
        TextPattern
            A new `TextPattern` instance with leading and trailing characters removed.
        """
        new_text = self.text.strip() if chars is None else self.text.strip(chars)
        pattern = TextPattern(new_text)
        return pattern

    def add(self, other, as_is=True):
        """
        Concatenate this `TextPattern` with another object.

        This method appends the given object(s) to the current `TextPattern`.
        If `other` is a string, sequence, or another `TextPattern`, it is
        converted into a `TextPattern` before concatenation. The `as_is` flag
        controls whether the input is preserved literally or converted into
        a regex pattern.

        Parameters
        ----------
        other : str, TextPattern, list, or tuple
            The object(s) to concatenate. If a sequence is provided, each
            element is processed and appended in order.
        as_is : bool, optional
            If True (default), preserve the input text as-is when converting
            to a `TextPattern`. If False, convert the input into a regex
            pattern.

        Returns
        -------
        TextPattern
            A new `TextPattern` instance containing the concatenated result.
        """
        if isinstance(other, TextPattern):
            result = self + other
        else:
            if isinstance(other, (list, tuple)):
                result = self
                for item in other:
                    if isinstance(item, TextPattern):
                        result = result + item
                    else:
                        item_pat = TextPattern(str(item), as_is=as_is)
                        result = result + item_pat
            else:
                other_pat = TextPattern(str(other), as_is=as_is)
                result = self + other_pat

        return result

    def concatenate(self, *other, as_is=True):
        """
        Concatenate this `TextPattern` with one or more objects.

        This method appends multiple objects to the current `TextPattern`.
        Each element in `other` is converted into a `TextPattern` before
        concatenation. The `as_is` flag controls whether inputs are preserved
        literally or converted into regex patterns.

        Parameters
        ----------
        other : str, TextPattern
            One or more objects to concatenate. Each element is processed
            and appended in order.
        as_is : bool, optional
            If True (default), preserve the input text as-is when converting
            to a `TextPattern`. If False, convert the input into a regex
            pattern.

        Returns
        -------
        TextPattern
            A new `TextPattern` instance containing the concatenated result.
        """
        result = self
        for item in other:
            result = result.add(item, as_is=as_is)
        return result


class ElementPattern(str):
    """
    A string subclass for converting element data into a regex pattern.

    The `ElementPattern` class provides utilities for building, validating,
    and manipulating regex patterns derived from element-like text input.
    It supports variable binding, optional emptiness (`or_empty`), and
    specialized pattern construction for different data types (e.g.,
    datetime, choice, raw text).

    Raises
    ------
    ElementPatternError
        Raised if the generated regex pattern is invalid.
    """
    # patterns
    word_bound_pattern = r'word_bound(_left|_right|_raw)?$'
    head_pattern = r'head(_raw|((_just)?_(whitespaces?|ws|spaces?)(_plus)?))?$'
    tail_pattern = r'tail(_raw|((_just)?_(whitespaces?|ws|spaces?)(_plus)?))?$'
    repetition_pattern = r'repetition_\d*(_\d*)?$'
    occurrence_pattern = r'({})(?P<is_phrase>_(group|phrase))?_occurrences?$'.format(
        '|'.join([
            r'((?P<fda>\d+)_or_(?P<lda>\d+))',
            r'((?P<fdb>\d+)_or_(?P<ldb>more))',
            r'(at_(?P<fdc>least|most)_(?P<ldc>\d+))',
            r'(?P<fdd>\d+)'
        ])
    )
    meta_data_pattern = r'^meta_data_\w+'
    _variable = None

    def __new__(cls, text, as_is=False):
        """
        Create a new `ElementPattern` instance from element text.

        This constructor initializes internal state and converts the given
        text into a regex pattern. By default, the text is processed through
        `get_pattern` to generate a validated regex. If `as_is` is True, the
        text is preserved literally as the regex pattern without transformation.

        Parameters
        ----------
        text : str
            The element text to be converted into a regex pattern.
        as_is : bool, optional
            If True, keep the text as an "AS-IS" regex pattern without
            transformation. Default is False.

        Returns
        -------
        ElementPattern
            A new `ElementPattern` instance containing the constructed regex
            pattern.

        Notes
        -----
        - Internal attributes `_variable`, `_or_empty`, `_prepended_pattern`,
          and `_appended_pattern` are initialized during construction.
        - If `text` is empty, the resulting pattern will be an empty string.
        """
        cls._variable = VarCls()
        cls._or_empty = False
        cls._prepended_pattern = ''
        cls._appended_pattern = ''
        data = str(text)

        if as_is:
            return str.__new__(cls, data)

        pattern = cls.get_pattern(data) if data else ''
        return str.__new__(cls, pattern)

    def __init__(self, text, as_is=False):
        self.text = text
        self.as_is = as_is
        self.variable = self._variable
        self.or_empty = self._or_empty
        self.prepended_pattern = self._prepended_pattern
        self.appended_pattern = self._appended_pattern

        # clear class variable after initialization
        self._variable = VarCls()
        self._or_empty = False
        self._prepended_pattern = ''
        self._appended_pattern = ''

    @classmethod
    def get_pattern(cls, text):
        """
        Convert element text into a validated regex pattern.

        This method parses the input text to determine whether it matches
        the format of a keyword followed by parameters (e.g., `keyword(params)`).
        If such a match is found, the pattern is constructed using
        `build_pattern`. Otherwise, the text is safely escaped for regex
        usage. The resulting pattern is validated before being returned.

        Parameters
        ----------
        text : str
            The element text to be converted into a regex pattern.

        Returns
        -------
        str
            A validated regex pattern string representing the input element.

        Raises
        ------
        ElementPatternError
            If the generated regex pattern is invalid.
        """
        sep_pat = r'(?P<keyword>\w+)[(](?P<params>.*)[)]$'
        match = re.match(sep_pat, text.strip())
        if match:
            keyword = match.group('keyword')
            params = match.group('params').strip()
            pattern = cls.build_pattern(keyword, params)
        else:
            pattern = do_soft_regex_escape(text)

        validate_pattern(pattern, exception_cls=ElementPatternError)
        return pattern

    @classmethod
    def build_pattern(cls, keyword, params):
        """
        Build a regex pattern from a keyword and its parameters.

        This method attempts to construct a regex pattern by delegating to
        specialized builders in a defined order. Each builder checks whether
        the given keyword and parameters match its criteria. If successful,
        the corresponding pattern is returned. If none of the specialized
        builders apply, a default pattern is generated.

        The order of evaluation is:
        1. Raw pattern
        2. Start-of-string pattern
        3. End-of-string pattern
        4. Symbol pattern
        5. Datetime pattern
        6. Choice pattern
        7. Data pattern
        8. Custom pattern
        9. Default pattern (fallback)

        Parameters
        ----------
        keyword : str
            A custom keyword that determines the type of regex pattern to build.
        params : str
            A string containing parameters associated with the keyword.

        Returns
        -------
        str
            A regex pattern string constructed from the keyword and parameters.

        Notes
        -----
        - Each specialized builder returns a tuple `(is_built, pattern)`.
          If `is_built` is True, the corresponding `pattern` is returned.
        - The method guarantees that a pattern is always returned, falling
          back to the default builder if no other builder succeeds.
        """
        is_built, raw_pattern = cls.build_raw_pattern(keyword, params)
        if is_built:
            return raw_pattern

        is_built, start_pattern = cls.build_start_pattern(keyword, params)
        if is_built:
            return start_pattern

        is_built, end_pattern = cls.build_end_pattern(keyword, params)
        if is_built:
            return end_pattern

        is_built, symbol_pattern = cls.build_symbol_pattern(keyword, params)
        if is_built:
            return symbol_pattern

        is_built, datetime_pattern = cls.build_datetime_pattern(keyword, params)
        if is_built:
            return datetime_pattern

        is_built, choice_pattern = cls.build_choice_pattern(keyword, params)
        if is_built:
            return choice_pattern

        is_built, data_pattern = cls.build_data_pattern(keyword, params)
        if is_built:
            return data_pattern

        is_built, custom_pattern = cls.build_custom_pattern(keyword, params)
        if is_built:
            return custom_pattern

        _, default_pattern = cls.build_default_pattern(keyword, params)
        return default_pattern

    @classmethod
    def build_custom_pattern(cls, keyword, params):
        """
        Build a custom regex pattern from a keyword and its parameters.

        This method constructs a regex pattern using a keyword defined in
        the reference dictionary (`REF`) and optional parameters. Parameters
        are parsed and interpreted to apply variable naming, word boundaries,
        start/end anchors, repetition, occurrence rules, metadata options,
        and conditional cases such as `or_empty` or space occurrences.
        The resulting pattern is assembled, decorated with anchors and
        variable names, and returned along with a success flag.

        Parameters
        ----------
        keyword : str
            A custom keyword that identifies the base regex pattern in `REF`.
        params : str
            A comma-separated string of parameters that modify the pattern
            (e.g., variable names, boundaries, repetition, occurrence rules).

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): True if a pattern was successfully built,
              False otherwise.
            - pattern (str): The constructed regex pattern string.

        Notes
        -----
        - If the keyword is not found in `REF`, the method returns `(False, '')`.
        - Parameters may include:
            * `var_<name>` → defines a variable name.
            * `word_bound`, `head`, `tail` → add boundaries or anchors.
            * `repetition`, `occurrence` → apply quantifiers.
            * `meta_data_*` → attach metadata options.
            * `or_empty` → allow optional emptiness.
            * `or_<case>` → handle conditional cases such as space repetition
              or occurrence.
        - Space-related cases (`repeat_spaces`, `occurrence_spaces`) are
          normalized into regex fragments and may be wrapped with alternation.
        - The final pattern is validated and normalized (e.g., replacing
          `__comma__` with `,`).
        """
        if keyword not in REF:
            return False, ''

        arguments = re.split(r' *, *', params) if params else []

        lst = [REF.get(keyword).get('pattern')]

        name, vpat = '', r'var_(?P<name>\w+)$'
        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''
        is_repeated = False
        is_occurrence = False
        is_or_either = False
        spaces_occurrence_pat = ''

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.repetition_pattern, arg):
                if not is_repeated or not is_occurrence:
                    lst = cls.add_repetition(lst, repetition=arg)
                    is_repeated = True
            elif re.match(cls.occurrence_pattern, arg):
                if not is_repeated or not is_occurrence:
                    lst = cls.add_occurrence(lst, occurrence=arg)
                    is_occurrence = True
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    repeating_space_pat = r'(?:either_)?repeat(?:s|ing)?(_[0-9_]+)_spaces?$'
                    occurring_space_pat = r'(?:either_)?((at_(least|most)_)?\d+(_occurrences?)?)_spaces?$'

                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    elif re.match(repeating_space_pat, case, flags=re.I):
                        r_case = re.sub(repeating_space_pat, r'repetition\1', case.lower())
                        spaces_occurrence_pat = cls('space(%s)' % r_case)
                        is_or_either = str.lower(case).startswith('either_')
                    elif re.match(occurring_space_pat, case, flags=re.I):
                        o_case = re.sub(occurring_space_pat, r'\1', case.lower())
                        o_case = o_case if 'occurrence' in o_case else '%s_occurrence' % o_case
                        spaces_occurrence_pat = cls('space(%s)' % o_case)
                        is_or_either = str.lower(case).startswith('either_')
                    else:
                        if case in REF:
                            if re.match('(?i)time|date(time)?', case):
                                pat = REF.get(case).get('format', f'unsupported-{case}-format')
                                pat not in lst and lst.append(pat)
                            else:
                                pat = REF.get(case).get('pattern')
                                pat not in lst and lst.append(pat)
                        else:
                            if re.match('(?i)time|date(time)?', case):
                                kw, *indices = re.split('_format', case)
                                node = REF.get(kw, None)
                                if node:
                                    if indices:
                                        for index in indices:
                                            key = f'format{index}'
                                            pat = node.get(key, f'unsupported-{kw}{key}')
                                            pat not in lst and lst.append(pat)
                                    else:
                                        pat = node.get('format', f'unsupported-{kw}format')
                                        pat not in lst and lst.append(pat)
                                else:
                                    pat = case
                                    pat not in lst and lst.append(pat)
                            else:
                                pat = case
                                pat not in lst and lst.append(pat)
                else:
                    pat = do_soft_regex_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        is_multiple = len(lst) > 1
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(
            pattern, word_bound=word_bound, added_parentheses=is_multiple
        )
        if spaces_occurrence_pat:
            fmt = '(%s)|( *%s *)' if is_or_either else '(%s)|(%s)'
            pattern = fmt % (spaces_occurrence_pat, pattern)

        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_symbol_pattern(cls, keyword, params):
        """
        Build a regex pattern for a symbol keyword with parameters.

        This method constructs a regex pattern when the keyword is `"symbol"`.
        It extracts the symbol name from the parameters, retrieves its base
        pattern from the `SYMBOL` dictionary (or escapes the name if not found),
        and applies optional modifiers such as variable naming, word boundaries,
        start/end anchors, repetition, occurrence rules, metadata options, and
        conditional cases (e.g., `or_empty`). The final pattern is assembled,
        normalized, and returned along with a success flag.

        Parameters
        ----------
        keyword : str
            The keyword that must equal `"symbol"` to trigger this builder.
        params : str
            A comma-separated string of parameters that define the symbol name
            and optional modifiers.

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): True if a symbol pattern was successfully built,
              False otherwise.
            - pattern (str): The constructed regex pattern string.

        Notes
        -----
        - The parameter `name=<symbol>` must be provided to identify the symbol.
        - Supported modifiers include:
            * `var_<name>` → defines a variable name.
            * `word_bound`, `head`, `tail` → add boundaries or anchors.
            * `repetition`, `occurrence` → apply quantifiers.
            * `meta_data_*` → attach metadata options.
            * `or_empty` → allow optional emptiness.
            * `or_<case>` → handle conditional cases such as time/date formats
              or space occurrences.
        - If the symbol name is not found in `SYMBOL`, it is safely escaped
          into a regex fragment.
        - The final pattern is normalized (e.g., replacing `__comma__` with `,`).
        """
        if keyword != 'symbol' or not params.strip():
            return False, ''

        arguments = re.split(r' *, *', params) if params else []
        symbol_name, removed_items = '', []
        for arg in arguments:
            if arg.startswith('name='):
                symbol_name = arg[5:]
                removed_items.append(arg)

        if not removed_items:
            return False, ''
        else:
            for item in removed_items:
                item in arguments and arguments.remove(item)

        val = SYMBOL.get(symbol_name, do_soft_regex_escape(symbol_name))
        lst = [val]

        name, vpat = '', r'var_(?P<name>\w+)$'
        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''
        is_repeated = False
        is_occurrence = False

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.repetition_pattern, arg):
                if not is_repeated or not is_occurrence:
                    lst = cls.add_repetition(lst, repetition=arg)
                    is_repeated = True
            elif re.match(cls.occurrence_pattern, arg):
                if not is_repeated or not is_occurrence:
                    lst = cls.add_occurrence(lst, occurrence=arg)
                    is_occurrence = True
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    else:
                        if case in REF:
                            if re.match('(?i)time|date(time)?', case):
                                pat = REF.get(case).get('format', f'unsupported-{case}-format')
                                pat not in lst and lst.append(pat)
                            else:
                                pat = REF.get(case).get('pattern')
                                pat not in lst and lst.append(pat)
                        else:
                            if re.match('(?i)time|date(time)?', case):
                                kw, *indices = re.split('_format', case)
                                node = REF.get(kw, None)
                                if node:
                                    if indices:
                                        for index in indices:
                                            key = f'format{index}'
                                            pat = node.get(key, f'unsupported-{kw}{key}')
                                            pat not in lst and lst.append(pat)
                                    else:
                                        pat = node.get('format', f'unsupported-{kw}format')
                                        pat not in lst and lst.append(pat)
                                else:
                                    pat = case
                                    pat not in lst and lst.append(pat)
                            else:
                                pat = case
                                pat not in lst and lst.append(pat)
                else:
                    pat = do_soft_regex_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        is_multiple = len(lst) > 1
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(
            pattern, word_bound=word_bound, added_parentheses=is_multiple
        )
        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_datetime_pattern(cls, keyword, params):
        """
        Build a regex pattern for datetime keywords with parameters.

        This method constructs a regex pattern when the given keyword refers
        to a datetime type defined in the reference dictionary (`REF`). It
        selects one or more datetime formats from the reference node and
        applies optional modifiers such as variable naming, word boundaries,
        start/end anchors, metadata options, and conditional cases (e.g.,
        `or_empty`). The final pattern is assembled, normalized, and returned
        along with a success flag.

        Parameters
        ----------
        keyword : str
            A custom keyword that must exist in `REF` and correspond to a
            datetime type.
        params : str
            A comma-separated string of parameters that define format
            selection and optional modifiers.

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): True if a datetime pattern was successfully built,
              False otherwise.
            - pattern (str): The constructed regex pattern string.

        Notes
        -----
        - If the keyword is not found in `REF` or has no `format` entries,
          the method returns `(False, '')`.
        - Supported parameters include:
            * `var_<name>` → defines a variable name.
            * `formatX` → selects a specific datetime format from `REF`.
            * `word_bound`, `head`, `tail` → add boundaries or anchors.
            * `meta_data_*` → attach metadata options.
            * `or_empty` → allow optional emptiness.
            * `or_<case>` → handle conditional cases such as time/date formats.
        - If no format is explicitly selected, the default `format` entry
          from the reference node is used.
        - The final pattern is normalized (e.g., replacing `__comma__` with `,`).
        """
        if keyword not in REF:
            return False, ''

        node = REF.get(keyword)
        fmt_lst = [key for key in node if key.startswith('format')]
        if not fmt_lst:
            return False, ''

        arguments = re.split(r' *, *', params) if params else []
        lst = []
        name, vpat = '', r'var_(?P<name>\w+)$'
        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif arg.startswith('format'):
                pat = node.get(arg)
                pat not in lst and lst.append(pat)
            # else:
            #     pat = arg
            #     pat not in lst and lst.append(pat)
        if not lst:
            lst.append(node.get('format'))

        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match or arg.startswith('format'):
                continue
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    else:
                        if case in REF:
                            if re.match('(?i)time|date(time)?', case):
                                pat = REF.get(case).get('format', f'unsupported-{case}-format')
                                pat not in lst and lst.append(pat)
                            else:
                                pat = REF.get(case).get('pattern')
                                pat not in lst and lst.append(pat)
                        else:
                            if re.match('(?i)time|date(time)?', case):
                                kw, *indices = re.split('_format', case)
                                node = REF.get(kw, None)
                                if node:
                                    if indices:
                                        for index in indices:
                                            key = f'format{index}'
                                            pat = node.get(key, f'unsupported-{kw}{key}')
                                            pat not in lst and lst.append(pat)
                                    else:
                                        pat = node.get('format', f'unsupported-{kw}format')
                                        pat not in lst and lst.append(pat)
                                else:
                                    pat = case
                                    pat not in lst and lst.append(pat)
                            else:
                                pat = case
                                pat not in lst and lst.append(pat)
                else:
                    pat = do_soft_regex_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(pattern, word_bound=word_bound)
        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_choice_pattern(cls, keyword, params):
        """
        Build a regex pattern for a choice keyword with parameters.

        This method constructs a regex pattern when the keyword is `"choice"`.
        It parses the provided parameters to generate a list of candidate
        sub-patterns, applies optional modifiers such as variable naming,
        word boundaries, start/end anchors, metadata options, and conditional
        cases (e.g., `or_empty`). The final pattern is assembled, normalized,
        and returned along with a success flag.

        Parameters
        ----------
        keyword : str
            The keyword that must equal `"choice"` to trigger this builder.
        params : str
            A comma-separated string of parameters that define the choice
            options and optional modifiers.

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): True if a choice pattern was successfully built,
              False otherwise.
            - pattern (str): The constructed regex pattern string.

        Notes
        -----
        - If the keyword is not `"choice"`, the method returns `(False, '')`.
        - Supported parameters include:
            * `var_<name>` → defines a variable name.
            * `word_bound`, `head`, `tail` → add boundaries or anchors.
            * `meta_data_*` → attach metadata options.
            * `or_empty` → allow optional emptiness.
            * `or_<case>` → handle conditional cases such as time/date formats
              or other reference patterns.
        - If a parameter matches a known reference in `REF`, its associated
          `pattern` or `format` entry is used.
        - Parameters that do not match special rules are safely escaped into
          regex fragments.
        - The final pattern is normalized (e.g., replacing `__comma__` with `,`).
        """
        if keyword != 'choice':
            return False, ''

        arguments = re.split(r' *, *', params) if params else []
        lst = []

        name, vpat = '', r'var_(?P<name>\w+)$'
        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    else:
                        if case in REF:
                            if re.match('(?i)time|date(time)?', case):
                                pat = REF.get(case).get('format', f'unsupported-{case}-format')
                                pat not in lst and lst.append(pat)
                            else:
                                pat = REF.get(case).get('pattern')
                                pat not in lst and lst.append(pat)
                        else:
                            if re.match('(?i)time|date(time)?', case):
                                kw, *indices = re.split('_format', case)
                                node = REF.get(kw, None)
                                if node:
                                    if indices:
                                        for index in indices:
                                            key = f'format{index}'
                                            pat = node.get(key, f'unsupported-{kw}{key}')
                                            pat not in lst and lst.append(pat)
                                    else:
                                        pat = node.get('format', f'unsupported-{kw}format')
                                        pat not in lst and lst.append(pat)
                                else:
                                    pat = case
                                    pat not in lst and lst.append(pat)
                            else:
                                pat = case
                                pat not in lst and lst.append(pat)
                else:
                    pat = do_soft_regex_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(pattern, word_bound=word_bound)
        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_data_pattern(cls, keyword, params):
        """
        Build a regex pattern for a data keyword with parameters.

        This method constructs a regex pattern when the keyword is `"data"`.
        It parses the provided parameters to generate a list of fragments,
        applies optional modifiers such as variable naming, word boundaries,
        start/end anchors, metadata options, and conditional cases (e.g.,
        `or_empty`). The final pattern is assembled, normalized, and returned
        along with a success flag.

        Parameters
        ----------
        keyword : str
            The keyword that must equal `"data"` to trigger this builder.
        params : str
            A comma-separated string of parameters that define the data
            options and optional modifiers.

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): True if a data pattern was successfully built,
              False otherwise.
            - pattern (str): The constructed regex pattern string.

        Notes
        -----
        - If the keyword is not `"data"`, the method returns `(False, '')`.
        - Supported parameters include:
            * `var_<name>` → defines a variable name.
            * `word_bound`, `head`, `tail` → add boundaries or anchors.
            * `meta_data_*` → attach metadata options.
            * `or_empty` → allow optional emptiness.
            * `or_<case>` → handle conditional cases such as time/date formats
              or other reference patterns.
        - If a parameter matches a known reference in `REF`, its associated
          `pattern` or `format` entry is used.
        - Parameters that do not match special rules are safely escaped into
          regex fragments.
        - The final pattern is normalized (e.g., replacing `__comma__` with `,`).
        """
        if keyword != 'data':
            return False, ''

        arguments = re.split(r' *, *', params) if params else []
        lst = []

        name, vpat = '', r'var_(?P<name>\w+)$'
        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    else:
                        if case in REF:
                            if re.match('(?i)time|date(time)?', case):
                                pat = REF.get(case).get('format', f'unsupported-{case}-format')
                                pat not in lst and lst.append(pat)
                            else:
                                pat = REF.get(case).get('pattern')
                                pat not in lst and lst.append(pat)
                        else:
                            if re.match('(?i)time|date(time)?', case):
                                kw, *indices = re.split('_format', case)
                                node = REF.get(kw, None)
                                if node:
                                    if indices:
                                        for index in indices:
                                            key = f'format{index}'
                                            pat = node.get(key, f'unsupported-{kw}{key}')
                                            pat not in lst and lst.append(pat)
                                    else:
                                        pat = node.get('format', f'unsupported-{kw}format')
                                        pat not in lst and lst.append(pat)
                                else:
                                    pat = case
                                    pat not in lst and lst.append(pat)
                            else:
                                pat = case
                                pat not in lst and lst.append(pat)
                else:
                    pat = do_soft_regex_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(pattern, word_bound=word_bound)
        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_start_pattern(cls, keyword, params):
        """
        Build a regex pattern for start-of-line anchors with optional whitespace.

        This method constructs a regex pattern when the keyword is `"start"`.
        It maps the provided parameter to a predefined start-of-line pattern
        that may include optional or required spaces/whitespace. If the parameter
        does not match any known option, a simple start-of-line anchor (`^`)
        is returned.

        Parameters
        ----------
        keyword : str
            The keyword that must equal `"start"` to trigger this builder.
        params : str
            A parameter string specifying the type of whitespace handling.
            Supported values include:
            - `"space"` → `^ *` (zero or more spaces)
            - `"spaces"` / `"space_plus"` → `^ +` (one or more spaces)
            - `"ws"` / `"whitespace"` → `^\\s*` (zero or more whitespace chars)
            - `"ws_plus"` / `"whitespaces"` / `"whitespace_plus"` → `^\\s+` (one or more whitespace chars)

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): True if a start pattern was successfully built,
              False otherwise.
            - pattern (str): The constructed regex pattern string.

        Notes
        -----
        - If the keyword is not `"start"`, the method returns `(False, '')`.
        - If the parameter is not recognized, the fallback pattern is `^`.
        """
        if keyword != 'start':
            return False, ''

        table = dict(space=r'^ *', spaces=r'^ +', space_plus=r'^ +',
                     ws=r'^\s*', ws_plus=r'^\s+',
                     whitespace=r'^\s*', whitespaces=r'^\s+',
                     whitespace_plus=r'^\s+')
        pat = table.get(params, r'^')
        return True, pat

    @classmethod
    def build_end_pattern(cls, keyword, params):
        """
        Build a regex pattern for end-of-line anchors with optional whitespace.

        This method constructs a regex pattern when the keyword is `"end"`.
        It maps the provided parameter to a predefined end-of-line pattern
        that may include optional or required spaces/whitespace. If the parameter
        does not match any known option, a simple end-of-line anchor (`$`)
        is returned.

        Parameters
        ----------
        keyword : str
            The keyword that must equal `"end"` to trigger this builder.
        params : str
            A parameter string specifying the type of whitespace handling.
            Supported values include:
            - `"space"` → ` *$` (zero or more spaces before end-of-line)
            - `"spaces"` / `"space_plus"` → ` +$` (one or more spaces before end-of-line)
            - `"ws"` / `"whitespace"` → `\\s*$` (zero or more whitespace chars before end-of-line)
            - `"ws_plus"` / `"whitespaces"` / `"whitespace_plus"` → `\\s+$` (one or more whitespace chars before end-of-line)

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): True if an end pattern was successfully built,
              False otherwise.
            - pattern (str): The constructed regex pattern string.

        Notes
        -----
        - If the keyword is not `"end"`, the method returns `(False, '')`.
        - If the parameter is not recognized, the fallback pattern is `$`.
        """
        if keyword != 'end':
            return False, ''

        table = dict(space=r' *$', spaces=r' +$', space_plus=r' +$',
                     ws=r'\s*$', ws_plus=r'\s+$',
                     whitespace=r'\s*$', whitespaces=r'\s+$',
                     whitespace_plus=r'\s+$')
        pat = table.get(params, r'$')
        return True, pat

    @classmethod
    def build_raw_pattern(cls, keyword, params):
        """
        Build a raw regex pattern from a keyword and parameters.

        This method constructs a regex pattern when the parameters begin
        with the prefix `"raw>>>"`. The prefix is stripped, the remaining
        text is safely escaped for regex usage, and combined with the
        keyword to form a raw pattern of the form `keyword(<escaped>)`.
        If the parameters do not start with `"raw>>>"`, the method returns
        `(False, '')`.

        Parameters
        ----------
        keyword : str
            A custom keyword used as the base of the regex pattern.
        params : str
            A parameter string that must begin with `"raw>>>"` to trigger
            raw pattern construction.

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): True if a raw pattern was successfully built,
              False otherwise.
            - pattern (str): The constructed regex pattern string, or an
              empty string if unsuccessful.

        Notes
        -----
        - The `"raw>>>"` prefix signals that the parameters should be
          treated as raw input rather than processed by other builders.
        - The remaining parameter text is passed through
          `do_soft_regex_escape` to ensure safe regex usage.
        """
        if not params.startswith('raw>>>'):
            return False, ''
        params = re.sub(r'raw>+', '', params, count=1)
        new_params = do_soft_regex_escape(params)
        pattern = r'{}\({}\)'.format(keyword, new_params)
        return True, pattern

    @classmethod
    def build_default_pattern(cls, keyword, params):
        """
        Build a default regex pattern from a keyword and parameters.

        This method constructs a fallback regex pattern when no specialized
        builder (e.g., raw, start, end, symbol, datetime, choice, or data)
        applies. The keyword and parameters are combined into the form
        `keyword(params)` and safely escaped for regex usage.

        Parameters
        ----------
        keyword : str
            A custom keyword used as the base of the regex pattern.
        params : str
            A string containing parameters associated with the keyword.

        Returns
        -------
        tuple of (bool, str)
            A tuple containing:
            - status (bool): Always True, since a default pattern is always built.
            - pattern (str): The constructed regex pattern string.

        Notes
        -----
        - This is the fallback builder used when no other specialized
          pattern builder succeeds.
        - The `do_soft_regex_escape` function is applied to ensure that
          special characters in the parameters are safely escaped.
        """
        pattern = do_soft_regex_escape('{}({})'.format(keyword, params))
        return True, pattern

    @classmethod
    def join_list(cls, lst):
        """
        Join a list of regex fragments into a single pattern string.

        This method combines multiple regex fragments into a unified pattern,
        applying grouping and alternation rules as needed. It ensures that
        whitespace-sensitive fragments are properly wrapped in parentheses,
        handles empty string cases by including optional alternation, and
        normalizes the final output for consistent regex behavior.

        Parameters
        ----------
        lst : list of str
            A list of regex pattern fragments to be joined.

        Returns
        -------
        str
            A regex pattern string constructed from the list of fragments.

        Notes
        -----
        - If the list contains more than one fragment, alternation (`|`)
          is applied between items.
        - Fragments containing whitespace or special regex constructs
          (e.g., quantifiers, brackets, parentheses, braces) are wrapped
          in parentheses to preserve grouping.
        - If the list contains an empty string, the result includes an
          optional empty match using alternation.
        - Whitespace-sensitive fragments trigger additional grouping to
          ensure correct precedence in alternation.
        """
        new_lst = []
        has_ws = False
        if len(lst) > 1:
            for item in lst:
                if ' ' in item or r'\s' in item:
                    has_ws = True
                    if item.startswith('(') and item.endswith(')'):
                        v = item
                    else:
                        if re.match(r' ([?+*]+|([{][0-9,]+[}]))$', item):
                            v = item
                        else:
                            v = '({})'.format(item)
                else:
                    if item:
                        chk1 = '\\' in item
                        chk2 = '[' in item and ']' in item
                        chk3 = '(' in item and ')' in item
                        chk4 = '{' in item and '}' in item
                        if chk1 or chk2 or chk3 or chk4:
                            v = '({})'.format(item)
                        else:
                            v = item
                    else:
                        v = item
                v not in new_lst and new_lst.append(v)
        else:
            new_lst = lst

        has_empty = bool([True for item in new_lst if item == ''])
        if has_empty:
            other_lst = [item for item in new_lst if item]
            result = '|'.join(other_lst)
            result = f"({result}|)" if len(other_lst) == 1 and not has_ws else f"(({result})|)"
            return result
        else:
            result = '|'.join(new_lst)
            result = f"({result})" if len(new_lst) > 1 and has_ws else result
            return result

        # result = '|'.join(new_lst)
        #
        # has_empty = bool([True for i in new_lst if i == ''])
        # if has_empty or len(new_lst) > 1 and has_ws:
        #     result = '({})'.format(result)
        #
        # return result

    @classmethod
    def add_var_name(cls, pattern, name=''):
        """
        Add a named capturing group to a regex pattern.

        This method wraps the given regex pattern in a named group if a
        variable name is provided. It also updates the internal variable
        state (`_variable.name` and `_variable.pattern`) to reflect the
        assigned name and associated pattern. If no name is given, the
        original pattern is returned unchanged.

        Parameters
        ----------
        pattern : str
            The regex pattern to which the variable name will be applied.
        name : str, optional
            The name of the capturing group. Default is an empty string,
            meaning no group name is added.

        Returns
        -------
        str
            A new regex pattern with the variable name applied, or the
            original pattern if no name is provided.

        Notes
        -----
        - If the pattern is enclosed in parentheses, the inner content is
          extracted and validated before applying the group name.
        - If validation fails, the original pattern is retained and an
          exception may be raised internally with `raise_exception`.
        - The method ensures that named groups follow the syntax
          `(?P<name>pattern)`.
        """
        if name:
            cls._variable.name = name
            cls._variable.pattern = pattern
            if pattern.startswith('(') and pattern.endswith(')'):
                sub_pat = pattern[1:-1]
                if pattern.endswith('|)'):
                    new_pattern = '(?P<{}>{})'.format(name, sub_pat)
                else:
                    try:
                        re.compile(sub_pat)
                        cls._variable.pattern = sub_pat
                        new_pattern = '(?P<{}>{})'.format(name, sub_pat)
                    except Exception as ex:
                        new_pattern = '(?P<{}>{})'.format(name, pattern)
                        raise_exception(ex, is_skipped=True)
            else:
                new_pattern = '(?P<{}>{})'.format(name, pattern)
            return new_pattern
        return pattern

    @classmethod
    def add_word_bound(cls, pattern, word_bound='', added_parentheses=True):
        """
        Add word boundary markers (`\\b`) to a regex pattern.

        This method conditionally wraps a regex pattern with word boundary
        anchors depending on the specified `word_bound` option. It also
        ensures that the pattern is enclosed in parentheses when required,
        particularly for whitespace-sensitive fragments or when
        `added_parentheses` is True.

        Parameters
        ----------
        pattern : str
            The regex pattern to which word boundaries will be applied.
        word_bound : str, optional
            Specifies the type of word boundary to add. Default is an empty
            string (no boundary added). Valid values are:
            - `"word_bound"` → add boundaries on both sides (`\\bpattern\\b`)
            - `"word_bound_left"` → add a boundary on the left (`\\bpattern`)
            - `"word_bound_right"` → add a boundary on the right (`pattern\\b`)
        added_parentheses : bool, optional
            If True, always enclose the pattern in parentheses unless it is
            already enclosed. Default is True.

        Returns
        -------
        str
            A new regex pattern with word boundaries applied as specified.

        Notes
        -----
        - If `word_bound` is empty, the original pattern is returned unchanged.
        - Whitespace-sensitive patterns are automatically wrapped in parentheses
          to preserve grouping.
        - Word boundaries (`\\b`) ensure that matches occur at word edges.
        """
        if not word_bound:
            return pattern

        has_ws = ' ' in pattern or r'\s' in pattern
        new_pattern = '({})'.format(pattern) if has_ws else pattern
        if added_parentheses:
            if not new_pattern.startswith('(') or not new_pattern.endswith(')'):
                new_pattern = '({})'.format(new_pattern)

        if word_bound == 'word_bound_left':
            new_pattern = r'\b{}'.format(new_pattern)
        elif word_bound == 'word_bound_right':
            new_pattern = r'{}\b'.format(new_pattern)
        else:
            new_pattern = r'\b{}\b'.format(new_pattern)
        return new_pattern

    @classmethod
    def add_head_of_string(cls, pattern, head=''):
        """
        Prepend a start-of-string anchor to a regex pattern.

        This method conditionally prepends a start-of-string marker (`^`)
        or a variant that includes optional or required whitespace depending
        on the specified `head` option. It also records the applied prefix
        in the internal `_prepended_pattern` attribute. If no `head` is
        provided, the original pattern is returned unchanged.

        Parameters
        ----------
        pattern : str
            The regex pattern to which the start-of-string anchor will be applied.
        head : str, optional
            A string specifying the type of start-of-string anchor. Default is empty.
            Supported values include:
            - `"head_ws"` → prepend `^\\s*` (zero or more whitespace)
            - `"head_ws_plus"` → prepend `^\\s+` (one or more whitespace)
            - `"head_space"` → prepend `^ *` (zero or more spaces)
            - `"head_space_plus"` / `"head_spaces"` → prepend `^ +` (one or more spaces)
            - `"head"` → prepend `^` (start of string only)
            - `"head_just_ws"` → prepend `\\s*` (zero or more whitespace, without `^`)
            - `"head_just_ws_plus"` → prepend `\\s+` (one or more whitespace, without `^`)
            - `"head_just_space"` → prepend ` *` (zero or more spaces, without `^`)
            - `"head_just_space_plus"` / `"head_just_spaces"` → prepend ` +` (one or more spaces, without `^`)
            - `"head_whitespace"` → prepend `^\\s*`
            - `"head_whitespace_plus"` / `"head_whitespaces"` → prepend `^\\s+`
            - `"head_just_whitespace"` → prepend `\\s*`
            - `"head_just_whitespace_plus"` / `"head_just_whitespaces"` → prepend `\\s+`

        Returns
        -------
        str
            A new regex pattern with the specified start-of-string anchor applied,
            or the original pattern if no valid `head` option is provided.

        Notes
        -----
        - If the pattern already begins with the specified anchor, no changes are made.
        - The applied anchor is stored in the class attribute `_prepended_pattern`
          for reference.
        """
        if head:
            case1, case2 = r'^\s*', r'^\s+'
            case3, case4 = r'^ *', r'^ +'
            case5 = r'^'

            case6, case7 = r'\s*', r'\s+'
            case8, case9 = r' *', r' +'

            case10, case11 = r'^\s*', r'^\s+'
            case12, case13 = r'\s*', r'\s+'

            if head == 'head_ws' and not pattern.startswith(case1):
                new_pattern = '{}{}'.format(case1, pattern)
                cls._prepended_pattern = case1
            elif head == 'head_ws_plus' and not pattern.startswith(case2):
                new_pattern = '{}{}'.format(case2, pattern)
                cls._prepended_pattern = case2
            elif head == 'head_space' and not pattern.startswith(case3):
                new_pattern = '{}{}'.format(case3, pattern)
                cls._prepended_pattern = case3
            elif head == 'head_space_plus' and not pattern.startswith(case4):
                new_pattern = '{}{}'.format(case4, pattern)
                cls._prepended_pattern = case4
            elif head == 'head_spaces' and not pattern.startswith(case4):
                new_pattern = '{}{}'.format(case4, pattern)
                cls._prepended_pattern = case4
            elif head == 'head' and not pattern.startswith(case5):
                new_pattern = '{}{}'.format(case5, pattern)
                cls._prepended_pattern = case5
            elif head == 'head_just_ws' and not pattern.startswith(case6):
                new_pattern = '{}{}'.format(case6, pattern)
                cls._prepended_pattern = case6
            elif head == 'head_just_ws_plus' and not pattern.startswith(case7):
                new_pattern = '{}{}'.format(case7, pattern)
                cls._prepended_pattern = case7
            elif head == 'head_just_space' and not pattern.startswith(case8):
                new_pattern = '{}{}'.format(case8, pattern)
                cls._prepended_pattern = case8
            elif head == 'head_just_space_plus' and not pattern.startswith(case9):
                new_pattern = '{}{}'.format(case9, pattern)
                cls._prepended_pattern = case9
            elif head == 'head_just_spaces' and not pattern.startswith(case9):
                new_pattern = '{}{}'.format(case9, pattern)
                cls._prepended_pattern = case9
            elif head == 'head_whitespace' and not pattern.startswith(case10):
                new_pattern = '{}{}'.format(case10, pattern)
                cls._prepended_pattern = case10
            elif head == 'head_whitespace_plus' and not pattern.startswith(case11):
                new_pattern = '{}{}'.format(case11, pattern)
                cls._prepended_pattern = case11
            elif head == 'head_whitespaces' and not pattern.startswith(case11):
                new_pattern = '{}{}'.format(case11, pattern)
                cls._prepended_pattern = case11
            elif head == 'head_just_whitespace' and not pattern.startswith(case12):
                new_pattern = '{}{}'.format(case12, pattern)
                cls._prepended_pattern = case12
            elif head == 'head_just_whitespace_plus' and not pattern.startswith(case13):
                new_pattern = '{}{}'.format(case13, pattern)
                cls._prepended_pattern = case13
            elif head == 'head_just_whitespaces' and not pattern.startswith(case13):
                new_pattern = '{}{}'.format(case13, pattern)
                cls._prepended_pattern = case13
            else:
                new_pattern = pattern
            return new_pattern
        return pattern

    @classmethod
    def add_tail_of_string(cls, pattern, tail=''):
        """
        Append an end-of-string anchor to a regex pattern.

        This method conditionally appends an end-of-string marker (`$`)
        or a variant that includes optional or required whitespace depending
        on the specified `tail` option. It also records the applied suffix
        in the internal `_appended_pattern` attribute. If no `tail` is
        provided, the original pattern is returned unchanged.

        Parameters
        ----------
        pattern : str
            The regex pattern to which the end-of-string anchor will be applied.
        tail : str, optional
            A string specifying the type of end-of-string anchor. Default is empty.
            Supported values include:
            - `"tail_ws"` → append `\\s*$` (zero or more whitespace before end-of-string)
            - `"tail_ws_plus"` → append `\\s+$` (one or more whitespace before end-of-string)
            - `"tail_space"` → append ` *$` (zero or more spaces before end-of-string)
            - `"tail_space_plus"` / `"tail_spaces"` → append ` +$` (one or
               more spaces before end-of-string)
            - `"tail"` → append `$` (end-of-string only)
            - `"tail_just_ws"` → append `\\s*` (zero or more whitespace, without `$`)
            - `"tail_just_ws_plus"` → append `\\s+` (one or more whitespace, without `$`)
            - `"tail_just_space"` → append ` *` (zero or more spaces, without `$`)
            - `"tail_just_space_plus"` / `"tail_just_spaces"` → append ` +` (one
                or more spaces, without `$`)
            - `"tail_whitespace"` → append `\\s*$`
            - `"tail_whitespace_plus"` / `"tail_whitespaces"` → append `\\s+$`
            - `"tail_just_whitespace"` → append `\\s*`
            - `"tail_just_whitespace_plus"` / `"tail_just_whitespaces"` → append `\\s+`

        Returns
        -------
        str
            A new regex pattern with the specified end-of-string anchor applied,
            or the original pattern if no valid `tail` option is provided.

        Notes
        -----
        - If the pattern already ends with the specified anchor, no changes are made.
        - The applied anchor is stored in the class attribute `_appended_pattern`
          for reference.
        """
        if tail:
            case1, case2 = r'\s*$', r'\s+$'
            case3, case4 = r' *$', r' +$'
            case5 = r'$'

            case6, case7 = r'\s*', r'\s+'
            case8, case9 = r' *', r' +'

            case10, case11 = r'\s*$', r'\s+$'
            case12, case13 = r'\s*', r'\s+'

            if tail == 'tail_ws' and not pattern.endswith(case1):
                new_pattern = '{}{}'.format(pattern, case1)
                cls._appended_pattern = case1
            elif tail == 'tail_ws_plus' and not pattern.endswith(case2):
                new_pattern = '{}{}'.format(pattern, case2)
                cls._appended_pattern = case2
            elif tail == 'tail_space' and not pattern.endswith(case3):
                new_pattern = '{}{}'.format(pattern, case3)
                cls._appended_pattern = case3
            elif tail == 'tail_space_plus' and not pattern.endswith(case4):
                new_pattern = '{}{}'.format(pattern, case4)
                cls._appended_pattern = case4
            elif tail == 'tail_spaces' and not pattern.endswith(case4):
                new_pattern = '{}{}'.format(pattern, case4)
                cls._appended_pattern = case4
            elif tail == 'tail' and not pattern.endswith(case5):
                new_pattern = '{}{}'.format(pattern, case5)
                cls._appended_pattern = case5
            elif tail == 'tail_just_ws' and not pattern.startswith(case6):
                new_pattern = '{}{}'.format(pattern, case6)
                cls._appended_pattern = case6
            elif tail == 'tail_just_ws_plus' and not pattern.startswith(case7):
                new_pattern = '{}{}'.format(pattern, case7)
                cls._appended_pattern = case7
            elif tail == 'tail_just_space' and not pattern.startswith(case8):
                new_pattern = '{}{}'.format(pattern, case8)
                cls._appended_pattern = case8
            elif tail == 'tail_just_space_plus' and not pattern.startswith(case9):
                new_pattern = '{}{}'.format(pattern, case9)
                cls._appended_pattern = case9
            elif tail == 'tail_just_spaces' and not pattern.startswith(case9):
                new_pattern = '{}{}'.format(pattern, case9)
                cls._appended_pattern = case9
            elif tail == 'tail_whitespace' and not pattern.startswith(case10):
                new_pattern = '{}{}'.format(pattern, case10)
                cls._appended_pattern = case10
            elif tail == 'tail_whitespace_plus' and not pattern.startswith(case11):
                new_pattern = '{}{}'.format(pattern, case11)
                cls._appended_pattern = case11
            elif tail == 'tail_whitespaces' and not pattern.startswith(case11):
                new_pattern = '{}{}'.format(pattern, case11)
                cls._appended_pattern = case11
            elif tail == 'tail_just_whitespace' and not pattern.startswith(case12):
                new_pattern = '{}{}'.format(pattern, case12)
                cls._appended_pattern = case12
            elif tail == 'tail_just_whitespace_plus' and not pattern.startswith(case13):
                new_pattern = '{}{}'.format(pattern, case13)
                cls._appended_pattern = case13
            elif tail == 'tail_just_whitespaces' and not pattern.startswith(case13):
                new_pattern = '{}{}'.format(pattern, case13)
                cls._appended_pattern = case13
            else:
                new_pattern = pattern
            return new_pattern
        return pattern

    @classmethod
    def add_repetition(cls, lst, repetition=''):
        """
        Apply a repetition quantifier to the first item in a list of regex fragments.

        This method modifies the first element of the provided list by appending
        a repetition quantifier based on the given `repetition` expression. If the
        item is not a singular pattern, it is wrapped in parentheses before the
        quantifier is applied. The updated list is returned.

        Parameters
        ----------
        lst : list of str
            A list of regex sub-patterns. The first item will be modified if
            repetition is specified.
        repetition : str, optional
            A repetition expression in the form of `"rep_m"` or `"rep_m_n"`,
            where:
            - `m` specifies the minimum number of repetitions.
            - `n` (optional) specifies the maximum number of repetitions.
            Default is an empty string, meaning no repetition is applied.

        Returns
        -------
        list of str
            A new list with the repetition quantifier applied to the first item,
            or the original list if no repetition is specified.

        Notes
        -----
        - If `repetition` is empty, the list is returned unchanged.
        - Non-singular patterns are wrapped in parentheses to preserve grouping
          before applying quantifiers.
        - The resulting quantifier uses the standard regex syntax `{m}` or `{m,n}`.
        """
        if not repetition:
            return lst

        new_lst = lst[:]
        item = new_lst[0]

        is_singular = ElementPattern.is_singular_pattern(item)
        item = item if is_singular else '({})'.format(item)

        _, m, *last = repetition.split('_', 2)
        if last:
            n = last[0]
            new_lst[0] = '%s{%s,%s}' % (item, m, n)
        else:
            new_lst[0] = '%s{%s}' % (item, m)
        return new_lst

    @classmethod
    def add_occurrence(cls, lst, occurrence=''):
        """
        Apply an occurrence quantifier to the first item in a list of regex fragments.

        This method modifies the first element of the provided list by appending
        an occurrence expression derived from the given `occurrence` string. The
        occurrence expression is parsed using the class-defined `occurrence_pattern`,
        which determines the quantifier type and whether the occurrence applies to
        a phrase or a single token. The updated list is returned.

        Parameters
        ----------
        lst : list of str
            A list of regex sub-patterns. The first item will be modified if
            an occurrence expression is specified.
        occurrence : str, optional
            An occurrence expression string that matches `occurrence_pattern`.
            Default is an empty string, meaning no occurrence quantifier is applied.

        Returns
        -------
        list of str
            A new list with the occurrence quantifier applied to the first item,
            or the original list if no occurrence is specified.

        Notes
        -----
        - If `occurrence` is empty, the list is returned unchanged.
        - The occurrence expression may define multiple cases (`fda/lda`, `fdb/ldb`,
          `fdc/ldc`, `fdd/ldd`), which are applied in sequence until one succeeds.
        - Phrase-based occurrences use a spacer (`' '` or `' +'`) depending on
          whether the occurrence applies to grouped tokens.
        - The method delegates case handling to `ElementPattern.add_case_occurrence`.
        """
        if not occurrence:
            return lst

        new_lst = lst[:]
        m = re.match(cls.occurrence_pattern, occurrence)
        is_phrase = bool(m.group('is_phrase'))
        spacer = ' +' if is_phrase and m.group('is_phrase') == '_group' else ' '

        fda, lda = m.group('fda') or '', m.group('lda') or ''
        fdb, ldb = m.group('fdb') or '', m.group('ldb') or ''
        fdc, ldc = m.group('fdc') or '', m.group('ldc') or ''
        fdd, ldd = m.group('fdd') or '', m.group('fdd') or ''

        func = ElementPattern.add_case_occurrence

        is_case_a = func(new_lst, fda, lda, is_phrase, spacer=spacer)
        is_case_b = is_case_a or func(new_lst, fdb, ldb, is_phrase, spacer=spacer)
        is_case_c = is_case_b or func(new_lst, fdc, ldc, is_phrase, spacer=spacer)
        is_case_c or func(new_lst, fdd, ldd, is_phrase, spacer=spacer)

        return new_lst

    @classmethod
    def add_case_occurrence(cls, lst, first, last, is_phrase, spacer=' '):
        """
        Apply an occurrence quantifier to the first item in a list of regex fragments.

        This method modifies the first element of the provided list by appending
        an occurrence quantifier based on the given `first` and `last` values.
        It supports numeric ranges, special keywords (`least`, `most`, `more`),
        and phrase-based occurrences. The updated pattern replaces the first
        item in the list, and the method returns whether the occurrence was
        successfully applied.

        Parameters
        ----------
        lst : list of str
            A list of regex sub-patterns. The first item will be modified if
            a valid occurrence case is provided.
        first : str
            The first digit or keyword defining the lower bound of the occurrence.
            Can be a number or special keyword (`least`, `most`).
        last : str
            The last digit or keyword defining the upper bound of the occurrence.
            Can be a number or special keyword (`more`).
        is_phrase : bool
            Flag indicating whether the occurrence applies to a phrase (grouped
            tokens) rather than a single pattern.
        spacer : str, optional
            The spacer string used when building phrase-based occurrences.
            Default is a single space `' '`.

        Returns
        -------
        bool
            True if an occurrence quantifier was successfully applied to the
            first item in the list, False otherwise.

        Notes
        -----
        - If both `first` and `last` are empty, no changes are made and the
          method returns False.
        - Phrase-based occurrences duplicate the item with a spacer to form
          grouped repetitions.
        - Numeric values are converted to integers when possible; otherwise,
          they are treated as keywords.
        - Supported quantifier formats include:
            * `{m}` → exact repetitions
            * `{m,n}` → bounded range
            * `*`, `+`, `?` → standard regex quantifiers
        """
        if not first and not last:
            return False

        item = lst[0]
        if is_phrase:
            # item = '{0}( {0})'.format(item)
            item = f'{item}({spacer}{item})'
        else:
            is_singular = ElementPattern.is_singular_pattern(item)
            item = item if is_singular else '({})'.format(item)

        first = int(first) if first.isdigit() else first
        last = int(last) if last.isdigit() else last

        if first == 'least' or first == 'most':
            if last == 0:
                fmt = '%s*' if first == 'least' else '%s?'
            else:
                fmt = '%%s{%s,}' if first == 'least' else '%%s{,%s}'
                fmt = fmt % last
        elif last == 'more':
            fmt = '%s*' if first == 0 else '%s+' if first == 1 else '%%s{%s,}' % first
        elif first == last:
            fmt = '%s' if first == 1 else '%%s{%s}' % first if first else '%s?'
        else:
            first, last = min(first, last), max(first, last)
            fmt = '%s?' if first == 0 and last == 1 else '%%s{%s,%s}' % (first, last)

        if fmt:
            lst[0] = fmt % item
            return True
        else:
            return False

    @classmethod
    def is_singular_pattern(cls, pattern):
        """
        Determine whether a regex pattern represents a singular unit.

        This method checks if the given pattern qualifies as a singular
        regex fragment. A pattern is considered singular if it is:
        - A single character.
        - An escaped character (e.g., `\\n`, `\\t`).
        - A character set enclosed in square brackets (e.g., `[a-z]`).

        Parameters
        ----------
        pattern : str
            The regex pattern to evaluate.

        Returns
        -------
        bool
            True if the pattern is a singular regex fragment, False otherwise.

        Notes
        -----
        - Singular patterns are treated differently when applying quantifiers
          or grouping, since they do not require additional parentheses.
        - Character sets are recognized only if they contain a single opening
          `[` and a single closing `]`.
        """
        left_bracket, right_bracket = '[', ']'
        pattern = str(pattern)
        first, last = pattern[:1], pattern[-1:]
        total = len(pattern)
        is_singular = total <= 1
        is_escape = total == 2 and first == '\\'
        is_char_set = pattern.count(first) == 1 and first == left_bracket
        is_char_set &= pattern.count(last) == 1 and last == right_bracket
        return is_singular or is_escape or is_char_set

    def remove_head_of_string(self):
        """
        Remove a start-of-string anchor from the regex pattern.

        This method strips a prepended start-of-string marker (e.g., `^`,
        `^\\s*`, `^\\s+`, `^ *`, `^ +`) from the current pattern if present.
        A new `ElementPattern` instance is returned with the modified pattern
        and updated internal state. If no start-of-string anchor is detected,
        a copy of the current instance is returned unchanged.

        Returns
        -------
        ElementPattern
            A new `ElementPattern` instance with the start-of-string anchor
            removed, or a copy of the original instance if no anchor was found.

        Notes
        -----
        - The method checks whether the pattern begins with `^` and whether
          a `prepended_pattern` is defined.
        - Internal attributes such as `variable`, `or_empty`, and
          `appended_pattern` are preserved in the new instance.
        - The `prepended_pattern` attribute is reset to an empty string in
          the returned object.
        """
        if self.prepended_pattern and self.startswith('^'):
            pattern = str(self)[len(self.prepended_pattern):]
            new_instance = ElementPattern(pattern, as_is=True)
            new_instance.as_is = False
            new_instance.variable = copy(self.variable)
            new_instance.or_empty = self.or_empty
            new_instance.prepended_pattern = ''
            new_instance.appended_pattern = self.appended_pattern
        else:
            new_instance = copy(self)

        return new_instance

    def remove_tail_of_string(self):
        """
        Remove an end-of-string anchor from the regex pattern.

        This method strips a trailing end-of-string marker (e.g., `$`,
        `\\s*$`, `\\s+$`, ` *$`, ` +$`) from the current pattern if present.
        A new `ElementPattern` instance is returned with the modified pattern
        and updated internal state. If no end-of-string anchor is detected,
        a copy of the current instance is returned unchanged.

        Returns
        -------
        ElementPattern
            A new `ElementPattern` instance with the end-of-string anchor
            removed, or a copy of the original instance if no anchor was found.

        Notes
        -----
        - The method checks whether the pattern ends with `$` and whether
          an `appended_pattern` is defined.
        - Internal attributes such as `variable`, `or_empty`, and
          `prepended_pattern` are preserved in the new instance.
        - The `appended_pattern` attribute is reset to an empty string in
          the returned object.
        """
        if self.appended_pattern and self.endswith('$'):
            pattern = str(self)[:-len(self.appended_pattern)]
            new_instance = ElementPattern(pattern, as_is=True)
            new_instance.as_is = False
            new_instance.variable = copy(self.variable)
            new_instance.or_empty = self.or_empty
            new_instance.prepended_pattern = self.prepended_pattern
            new_instance.appended_pattern = ''
        else:
            new_instance = copy(self)

        return new_instance


class LinePattern(str):
    """
    A string subclass for converting a single line of text into a regex pattern.

    The `LinePattern` class provides utilities for constructing and validating
    regex patterns from line-based text input. It supports optional whitespace
    handling at the beginning or end of the line, as well as case-insensitive
    matching.

    Raises
    ------
    LinePatternError
        Raised if the generated regex pattern is invalid.
    """
    _variables = None

    def __new__(cls, text, prepended_ws=False, appended_ws=False,
                ignore_case=False):
        """
        Create a new `LinePattern` instance from a single line of text.

        This constructor converts the given text into a validated regex
        pattern. It supports optional whitespace handling at the beginning
        or end of the line, as well as case-insensitive matching. If the
        input text is empty, a pattern that matches only whitespace is
        returned.

        Parameters
        ----------
        text : str
            The line of text to be converted into a regex pattern.
        prepended_ws : bool, optional
            If True, prepend a whitespace character at the beginning of the
            pattern. Default is False.
        appended_ws : bool, optional
            If True, append a whitespace character at the end of the pattern.
            Default is False.
        ignore_case : bool, optional
            If True, prepend `(?i)` to the pattern to enable case-insensitive
            matching. Default is False.

        Returns
        -------
        LinePattern
            A new `LinePattern` instance containing the constructed regex
            pattern.

        Raises
        ------
        LinePatternError
            If the generated regex pattern is invalid.
        """
        cls._variables = list()
        cls._items = list()
        data = str(text)
        if data:
            pattern = cls.get_pattern(
                data, prepended_ws=prepended_ws,
                appended_ws=appended_ws, ignore_case=ignore_case
            )
        else:
            pattern = r'^\s*$'
        return str.__new__(cls, pattern)

    def __init__(self, text,
                 prepended_ws=False, appended_ws=False,
                 ignore_case=False):
        self.text = text
        self.prepended_ws = prepended_ws
        self.appended_ws = appended_ws
        self.ignore_case = ignore_case

        self.variables = self._variables
        self.items = self._items

        # clear class variable after initialization
        self._variables = list()
        self._items = list()

    @property
    def statement(self):
        """
        Construct the template statement for the regex pattern.

        This property builds a string representation of the pattern by
        iterating over all items in `self.items`. If an item is an
        `ElementPattern` with a non-empty variable, its variable name
        is inserted; otherwise, the item itself is used. The resulting
        sequence of elements is concatenated into a single template
        statement.

        Returns
        -------
        str
            A template statement representing the regex pattern.
        """
        lst = []
        for item in self.items:
            if isinstance(item, ElementPattern):
                if not item.variable.is_empty:
                    lst.append(item.variable.var_name)
                else:
                    lst.append(item)
            else:
                lst.append(item)
        return ''.join(lst)

    @classmethod
    def get_pattern(cls, text,
                    prepended_ws=False, appended_ws=False,
                    ignore_case=False):
        """
        Convert a line of text into a validated regex pattern.

        This method parses the input text and constructs a regex pattern
        by identifying elements that match function-like expressions
        (e.g., `word(...)`) and wrapping them as `ElementPattern` objects.
        Other text fragments are wrapped as `TextPattern` objects. The
        resulting fragments are adjusted to ensure proper start/end anchors,
        optional whitespace handling, and case-insensitive matching if
        requested. The final pattern is validated before being returned.

        Parameters
        ----------
        text : str
            The line of text to be converted into a regex pattern.
        prepended_ws : bool, optional
            If True, prepend a whitespace character at the beginning of the
            pattern. Default is False.
        appended_ws : bool, optional
            If True, append a whitespace character at the end of the pattern.
            Default is False.
        ignore_case : bool, optional
            If True, prepend `(?i)` to the pattern to enable case-insensitive
            matching. Default is False.

        Returns
        -------
        str
            A validated regex pattern string representing the input text.

        Raises
        ------
        LinePatternError
            If the generated regex pattern is invalid.
        """
        line = str(text)

        lst = []
        start = 0
        m = None
        for m in re.finditer(r'\w+[(][^)]*[)]', line):
            pre_match = m.string[start:m.start()]
            if pre_match:
                lst.append(TextPattern(pre_match))
            elm_pat = ElementPattern(m.group())
            if not elm_pat.variable.is_empty:
                cls._variables.append(elm_pat.variable)
            lst.append(elm_pat)
            start = m.end()
        else:
            if m and start:
                after_match = m.string[start:]
                if after_match:
                    lst.append(TextPattern(after_match))

        if len(lst) == 1 and lst[0].strip() == '':
            return r'^\s*$'
        elif not lst:
            if line.strip() == '':
                return r'^\s*$'
            lst.append(TextPattern(line))

        cls.readjust_if_or_empty(lst)
        cls.ensure_start_of_line_pattern(lst)
        cls.ensure_end_of_line_pattern(lst)
        prepended_ws and cls.prepend_whitespace(lst)
        ignore_case and cls.prepend_ignorecase_flag(lst)
        appended_ws and cls.append_whitespace(lst)
        cls._items = lst
        pattern = ''.join(lst)
        validate_pattern(pattern, exception_cls=LinePatternError)
        return pattern

    @classmethod
    def readjust_if_or_empty(cls, lst):
        """
        Readjust a pattern list when an `ElementPattern` has the `or_empty` flag set.

        This method inspects a sequence of regex pattern fragments and modifies
        them when adjacent `ElementPattern` objects allow optional emptiness
        (`or_empty=True`). In such cases, preceding or following whitespace
        tokens are trimmed or replaced with a special whitespace pattern
        (`zero_or_whitespaces()`). The adjustment ensures that optional
        elements do not leave redundant or conflicting whitespace markers
        in the final regex.

        Parameters
        ----------
        lst : list
            A list of regex pattern fragments, which may include `TextPattern`,
            `ElementPattern`, or raw string segments. The list is modified
            in place.

        Returns
        -------
        None
            The input list is updated directly; no value is returned.

        Notes
        -----
        - If the list has fewer than two elements, no adjustment is performed.
        - Whitespace tokens such as `' '`, `' +'`, `r'\\s'`, and `r'\\s+'`
          may be replaced with `zero_or_whitespaces()` when adjacent to
          `ElementPattern` instances marked with `or_empty`.
        - Adjustments are applied in multiple passes to handle forward,
          backward, and mixed adjacency cases.
        """
        if len(lst) < 2:
            return

        total = len(lst)
        ws_pat = ElementPattern('zero_or_whitespaces()')
        insert_indices = []
        for index, item in enumerate(lst[1:], 1):
            prev_item = lst[index-1]
            is_prev_item_text_pat = isinstance(prev_item, (TextPattern, str))
            is_item_elm_pat = isinstance(item, ElementPattern)
            if is_prev_item_text_pat and is_item_elm_pat:
                if item.or_empty:
                    if prev_item.endswith(' '):
                        lst[index-1] = prev_item.rstrip()
                        insert_indices.insert(0, index)
                    elif prev_item.endswith(r'\s'):
                        lst[index-1] = prev_item[:-2]
                        insert_indices.insert(0, index)
                    elif index == total - 1:
                        if prev_item.endswith(' +'):
                            lst[index-1] = prev_item[:-2]
                            insert_indices.insert(0, index)
                        elif prev_item.endswith(r'\s+'):
                            lst[index-1] = prev_item[:-3]
                            insert_indices.insert(0, index)

        for index in insert_indices:
            lst.insert(index, ws_pat)

        index = len(lst) - 1
        is_stopped = False
        insert_indices = []
        while index > 0 and not is_stopped:
            prev_item, item = lst[index-1], lst[index]
            is_prev_item_text_pat = isinstance(prev_item, (TextPattern, str))
            is_item_elm_pat = isinstance(item, ElementPattern)
            if is_prev_item_text_pat and is_item_elm_pat:
                if item.or_empty:
                    if prev_item.endswith(' '):
                        lst[index - 1] = prev_item.rstrip()
                        insert_indices.insert(0, index)
                    elif prev_item.endswith(r'\s') or prev_item.endswith(' +'):
                        lst[index - 1] = prev_item[:-2]
                        insert_indices.insert(0, index)
                    elif prev_item.endswith(r'\s+'):
                        lst[index - 1] = prev_item[:-3]
                        insert_indices.insert(0, index)
            else:
                is_stopped = True
            index -= 2

        for index in insert_indices:
            lst.insert(index, ws_pat)

        index = len(lst) - 1
        is_stopped = False
        is_prev_containing_empty = False
        while index > 0 and not is_stopped:
            prev_item, item = lst[index-1], lst[index]
            is_prev_item_elm_pat = isinstance(prev_item, ElementPattern)
            is_item_text_pat = isinstance(item, (TextPattern, str))
            if is_prev_item_elm_pat and is_item_text_pat:
                if prev_item.or_empty:
                    if item in [' ', ' +', r'\s', r'\s+']:
                        lst[index] = ws_pat
                    is_prev_containing_empty = True
                else:
                    if item in [' ', ' +', r'\s', r'\s+'] and is_prev_containing_empty:
                        lst[index] = ws_pat
                    is_prev_containing_empty = False
            else:
                is_stopped = True
            index -= 2

    @classmethod
    def ensure_start_of_line_pattern(cls, lst):
        """
        Ensure that a start-of-line regex pattern does not contain redundant or invalid whitespace.

        This method inspects the beginning of a regex pattern list and removes or
        adjusts duplicate whitespace tokens that follow start-of-line anchors (`^` or `\\A`).
        It also cleans up invalid prepended patterns in `ElementPattern` objects to
        maintain a valid and concise regex structure.

        Parameters
        ----------
        lst : list
            A list of regex pattern fragments, which may include `TextPattern`,
            `ElementPattern`, or raw string segments. The list is modified in place.

        Returns
        -------
        None
            The input list is updated directly; no value is returned.

        Notes
        -----
        - If the list has fewer than two elements, no adjustment is performed.
        - Leading whitespace after `^` or `\\A` is trimmed or removed.
        - Whitespace tokens such as `' '`, `'\\s'`, `' +'`, and `'\\s+'`
          are normalized to prevent duplication.
        - `ElementPattern` instances with a `prepended_pattern` are cleaned
          using `remove_head_of_string()` to ensure proper start-of-line handling.
        """
        if len(lst) < 2:
            return

        curr, nxt = lst[0], lst[1]

        if curr == '^':
            if isinstance(nxt, TextPattern):
                if nxt == ' ':
                    lst.pop(1)
                    return
                if re.match(' [^+*]', nxt):
                    lst[1] = nxt.lstrip()
                    return

        match = re.match(r'(?P<pre_ws>( |\\s)[*+]*)', nxt)
        if re.match(r'(\^|\\A)( |\\s)[*+]*$', curr):
            if isinstance(nxt, TextPattern) and match:
                index = len(match.group('pre_ws'))
                new_val = nxt[index:]
                if new_val == '':
                    lst.pop(1)
                else:
                    lst[1] = new_val

        # clean up any invalid a start of string pattern
        for index, node in enumerate(lst[1:], 1):
            if isinstance(node, ElementPattern) and node.prepended_pattern:
                lst[index] = node.remove_head_of_string()

    @classmethod
    def ensure_end_of_line_pattern(cls, lst):
        """
        Ensure that an end-of-line regex pattern does not contain redundant or invalid whitespace.

        This method inspects the end of a regex pattern list and removes or
        adjusts duplicate whitespace tokens that precede end-of-line anchors
        (`$` or `\\Z`). It also cleans up invalid appended patterns in
        `ElementPattern` objects to maintain a valid and concise regex
        structure.

        Parameters
        ----------
        lst : list
            A list of regex pattern fragments, which may include `TextPattern`,
            `ElementPattern`, or raw string segments. The list is modified in place.

        Returns
        -------
        None
            The input list is updated directly; no value is returned.

        Notes
        -----
        - If the list has fewer than two elements, no adjustment is performed.
        - Trailing whitespace before `$` or `\\Z` is trimmed or removed.
        - Whitespace tokens such as `' '`, `'\\s'`, `' +'`, and `'\\s+'`
          are normalized to prevent duplication.
        - `ElementPattern` instances with an `appended_pattern` are cleaned
          using `remove_tail_of_string()` to ensure proper end-of-line handling.
        """
        if len(lst) < 2:
            return

        last, prev = lst[-1], lst[-2]

        if last == '$':
            if isinstance(prev, TextPattern):
                if prev == ' ':
                    lst.pop(-2)
                    return
                if not re.search(' [+*]$', prev):
                    lst[-2] = prev.rstrip()
                    return

        match = re.search(r'(?P<post_ws>( |\\s)[*+]*)$', prev)
        if re.match(r'( |\\s)[*+]?(\$|\\Z)$', last):
            if isinstance(prev, TextPattern) and match:
                index = len(match.group('post_ws'))
                new_val = prev[:-index]
                if new_val == '':
                    lst.pop(-2)
                else:
                    lst[-2] = new_val

        # clean up any invalid a start of string pattern
        for index, node in enumerate(lst[:-1]):
            if isinstance(node, ElementPattern) and node.appended_pattern:
                lst[index] = node.remove_tail_of_string()

    @classmethod
    def prepend_whitespace(cls, lst):
        """
        Prepend a whitespace pattern to the beginning of a regex pattern list.

        This method ensures that a regex pattern list starts with an optional
        whitespace matcher (`^\\s*`) when no explicit whitespace is already
        present after a start-of-line anchor (`^` or `\\A`). It modifies the
        list in place to normalize leading whitespace handling.

        Parameters
        ----------
        lst : list
            A list of regex pattern fragments, which may include `TextPattern`,
            `ElementPattern`, or raw string segments. The list is modified in place.

        Returns
        -------
        None
            The input list is updated directly; no value is returned.

        Notes
        -----
        - If the list is empty, no changes are made.
        - A leading whitespace pattern is only inserted if the first element
          does not already match the regex `(\\^|\\A)( |\\s)[*+]?`.
        - The inserted pattern is `^\\s*`, which matches zero or more whitespace
          characters at the start of the string.
        """
        if not lst:
            return

        pat = r'(\^|\\A)( |\\s)[*+]?'
        if not re.match(pat, lst[0]):
            lst.insert(0, r'^\s*')

    @classmethod
    def prepend_ignorecase_flag(cls, lst):
        """
        Prepend the case-insensitive flag `(?i)` to a regex pattern list.

        This method ensures that a regex pattern list begins with the
        case-insensitive flag `(?i)` if it is not already present.
        The flag enables case-insensitive matching for the entire
        regex expression. The list is modified in place.

        Parameters
        ----------
        lst : list
            A list of regex pattern fragments, which may include `TextPattern`,
            `ElementPattern`, or raw string segments. The list is modified in place.

        Returns
        -------
        None
            The input list is updated directly; no value is returned.

        Notes
        -----
        - If the list is empty, no changes are made.
        - The flag `(?i)` is only inserted if the first element does not
          already match the regex pattern `'[(][?]i[)]'`.
        - Adding `(?i)` affects the entire regex, making all subsequent
          matches case-insensitive.
        """
        if not lst:
            return

        pat = r'[(][?]i[)]'
        if not re.match(pat, lst[0]):
            lst.insert(0, '(?i)')

    @classmethod
    def append_whitespace(cls, lst):
        """
        Append a trailing whitespace pattern to the end of a regex pattern list.

        This method ensures that a regex pattern list ends with an optional
        whitespace matcher (`\\s*$`) when no explicit trailing whitespace is
        already present before an end-of-line anchor (`$` or `\\Z`). It modifies
        the list in place to normalize trailing whitespace handling.

        Parameters
        ----------
        lst : list
            A list of regex pattern fragments, which may include `TextPattern`,
            `ElementPattern`, or raw string segments. The list is modified in place.

        Returns
        -------
        None
            The input list is updated directly; no value is returned.

        Notes
        -----
        - If the list is empty, no changes are made.
        - A trailing whitespace pattern is only appended if the last element
          does not already match the regex `( |\\s)[*+]?(\\$|\\Z)$`.
        - The appended pattern is `\\s*$`, which matches zero or more whitespace
          characters at the end of the string.
        """
        if not lst:
            return
        pat = r'( |\\s)[*+]?(\$|\\Z)$'
        if not re.search(pat, lst[-1]):
            lst.append(r'\s*$')


class MultilinePattern(str):
    """
    A string subclass for converting multiple lines of text into a regex pattern.

    The `MultilinePattern` class processes multi-line input and generates
    a validated regex pattern. It supports optional case-insensitive
    matching by prepending the `(?i)` flag to the pattern.

    Raises
    ------
    MultilinePatternError
        Raised if the generated regex pattern is invalid.
    """
    def __new__(cls, text, ignore_case=False, is_exact=False):
        """
        Create a new `MultilinePattern` instance from multi-line text.

        This constructor processes the input text or sequence of text lines
        and converts them into a validated regex pattern. Line breaks are
        normalized and split, then passed to `get_pattern` for conversion.
        The resulting regex can optionally be case-insensitive or exact.

        Parameters
        ----------
        text : str, list of str, or tuple of str
            Input text or sequence of text lines to be converted into a regex
            pattern. Must be a string or a list/tuple of strings.
        ignore_case : bool, optional
            If True, prepend `(?i)` to the pattern to enable case-insensitive
            matching. Default is False.
        is_exact : bool, optional
            If True, generate a pattern that matches the text exactly.
            Default is False.

        Returns
        -------
        MultilinePattern
            A new `MultilinePattern` instance containing the constructed regex
            pattern.

        Raises
        ------
        MultilinePatternError
            If `text` is not a string or a list/tuple of strings, or if the
            generated regex pattern is invalid.
        """
        lines = []
        if isinstance(text, (list, tuple)):
            for line in text:
                lines.extend(re.split(r'\r\n|\r|\n', line))
        elif isinstance(text, str):
            lines = re.split(r'\r\n|\r|\n', text)
        else:
            error = f"Argument 'text' must be a string or a list of strings.\n{text}"
            raise MultilinePatternError(error)

        if lines:
            pattern = cls.get_pattern(
                lines, ignore_case=ignore_case, is_exact=is_exact
            )
        else:
            pattern = r'^\s*$'
        return str.__new__(cls, pattern)

    @classmethod
    def get_pattern(cls, lines, ignore_case=False, is_exact=False):
        """
        Construct a regex pattern from multiple lines of text.

        This method converts each line into a `LinePattern` instance and
        reformats them into a single regex pattern. The first and last lines
        are treated with special formatting rules, while intermediate lines
        are processed normally. The resulting pattern can optionally be
        case-insensitive or exact, and is validated before being returned.

        Parameters
        ----------
        lines : list of str
            A list of text lines to be converted into a regex pattern.
        ignore_case : bool, optional
            If True, prepend `(?i)` to the pattern to enable case-insensitive
            matching. Default is False.
        is_exact : bool, optional
            If True, generate a pattern that matches each line exactly.
            Default is False.

        Returns
        -------
        str
            A validated regex pattern string representing the input lines.

        Raises
        ------
        MultilinePatternError
            If the generated regex pattern is invalid.
        """
        if not lines:
            return r'^\s*$'

        line_patterns = []
        for line in lines:
            line_pat = LinePattern(line, ignore_case=ignore_case)
            line_patterns.append(line_pat)

        first, last = line_patterns[0], line_patterns[-1]
        last = line_patterns[-1]

        if len(line_patterns) == 1:
            return first

        new_line_patterns = [cls.reformat(first, is_first=True, is_exact=is_exact)]
        for line_pat in line_patterns[1:-1]:
            new_line_patterns.append(cls.reformat(line_pat, is_exact=is_exact))

        new_line_patterns.append(cls.reformat(last, is_last=True, is_exact=is_exact))

        new_pattern = ''.join(new_line_patterns)
        validate_pattern(new_pattern, exception_cls=MultilinePatternError)
        return new_pattern

    @classmethod
    def reformat(cls, pattern, is_first=False, is_last=False, is_exact=False):
        """
        Reformat a line pattern for use with `re.MULTILINE` matching.

        This method adjusts a regex line pattern to ensure proper handling
        of multi-line text. It applies different formatting rules depending
        on whether the pattern represents the first line, the last line, or
        an intermediate line. Exact matching can also be enforced.

        Parameters
        ----------
        pattern : LinePattern or str
            The line pattern to be reformatted.
        is_first : bool, optional
            If True, treat the pattern as the first line in the sequence.
            Default is False.
        is_last : bool, optional
            If True, treat the pattern as the last line in the sequence.
            Default is False.
        is_exact : bool, optional
            If True, enforce exact line matching by using stricter newline
            handling. Default is False.

        Returns
        -------
        str
            A reformatted regex pattern suitable for multi-line matching.
        """
        pat1 = r'(\r\n|\r|\n)'
        pat2 = r'[^\r\n]*[\r\n]+([^\r\n]*[\r\n]+)*'
        add_on_pat = pat1 if is_exact else pat2
        if is_first:
            return pattern[:-1] if pattern.endswith('$') else pattern
        else:
            pattern = pattern.replace('(?i)', '')
            pattern = pattern[1:] if pattern.startswith('^') else pattern
            if is_last:
                return f'{add_on_pat}{pattern}'
            else:
                pattern = pattern[:-1] if pattern.endswith('$') else pattern
                return f'{add_on_pat}{pattern}'


class PatternBuilder(str):
    """
    A string subclass for building regex patterns from a list of text.

    The `PatternBuilder` class provides utilities to convert sequences
    of text into validated regex patterns. It supports optional variable
    naming and word boundary handling to generate flexible and reusable
    regex expressions.

    Raises
    ------
    PatternBuilderError
        Raised if the generated regex pattern is invalid.
    """
    def __new__(cls, lst_of_text, var_name='', word_bound=''):
        """
        Create a new `PatternBuilder` instance from one or more text elements.

        This constructor converts the provided text or sequence of text
        elements into a validated regex pattern. Each text element is
        processed into a regex fragment, combined into a single pattern,
        optionally wrapped with word boundaries, and annotated with a
        variable name if provided.

        Parameters
        ----------
        lst_of_text : str, list, or tuple
            A single text string or a sequence of text elements to be
            converted into a regex pattern.
        var_name : str, optional
            A variable name to associate with the generated pattern.
            Default is an empty string (no variable name).
        word_bound : str, optional
            Specifies word boundary behavior. Default is an empty string.
            Valid values are:
            - "word_bound"       : apply word boundaries on both sides
            - "word_bound_left"  : apply word boundary on the left side
            - "word_bound_right" : apply word boundary on the right side

        Returns
        -------
        PatternBuilder
            A new `PatternBuilder` instance containing the constructed
            regex pattern.

        Raises
        ------
        PatternBuilderError
            If the generated regex pattern is invalid.
        """
        if not isinstance(lst_of_text, (list, tuple)):
            lst_of_text = [lst_of_text]

        lst = []
        is_empty = False
        for text in lst_of_text:
            data = str(text)
            if data:
                pattern = cls.get_pattern(data)
                pattern not in lst and lst.append(pattern)
            else:
                is_empty = True

        is_empty and lst.append('')
        pattern = ElementPattern.join_list(lst)
        pattern = ElementPattern.add_word_bound(pattern, word_bound=word_bound)
        pattern = cls.add_var_name(pattern, name=var_name)
        validate_pattern(pattern, exception_cls=PatternBuilderError)
        return str.__new__(cls, pattern)

    @classmethod
    def get_pattern(cls, text):
        """
        Convert text into a regex pattern string.

        This method processes the input text by splitting alphanumeric
        segments and non-alphanumeric delimiters. Alphanumeric segments
        are converted into regex fragments using
        `PatternBuilder.get_alnum_pattern`, while non-alphanumeric
        sequences are wrapped as `TextPattern` objects. The resulting
        fragments are concatenated into a single regex pattern, which
        is validated for correctness.

        Parameters
        ----------
        text : str
            Input text to be converted into a regex pattern.

        Returns
        -------
        str
            A regex pattern string derived from the input text.

        Raises
        ------
        PatternBuilderError
            If the generated regex pattern is invalid.
        """
        start = 0
        lst = []

        for m in re.finditer(r'[^a-zA-Z0-9]+', text):
            before_match = text[start:m.start()]
            lst.append(cls.get_alnum_pattern(before_match))
            lst.append(TextPattern(m.group()))
            start = m.end()
        else:
            if start > 0:
                after_match = text[start:]
                lst.append(cls.get_alnum_pattern(after_match))

        pattern = ''.join(lst) if lst else cls.get_alnum_pattern(text)
        validate_pattern(pattern, exception_cls=PatternBuilderError)
        return pattern

    @classmethod
    def get_alnum_pattern(cls, text):
        """
        Generate a regex pattern for alphanumeric text.

        This method inspects the input string and returns a regex
        fragment based on its composition:
        - Digits only → `[0-9]+`
        - Letters only → `[a-zA-Z]+`
        - Alphanumeric mix → `[a-zA-Z0-9]+`
        - Other characters → `.*`
        - Empty string → `''`

        Parameters
        ----------
        text : str
            Input text to be analyzed for alphanumeric composition.

        Returns
        -------
        str
            A regex pattern string corresponding to the type of input text.
        """
        if text:
            if text.isdigit():
                return '[0-9]+'
            elif text.isalpha():
                return '[a-zA-Z]+'
            elif text.isalnum():
                return '[a-zA-Z0-9]+'
            else:
                return '.*'
        else:
            return ''

    @classmethod
    def add_var_name(cls, pattern, name=''):
        """
        Add a named capturing group to a regex pattern.

        This method wraps the given regex pattern in a named group if
        a variable name is provided. If no name is given, the original
        pattern is returned unchanged.

        Parameters
        ----------
        pattern : str
            The regex pattern to which the variable name will be applied.
        name : str, optional
            The name of the capturing group. Default is an empty string,
            meaning no group name is added.

        Returns
        -------
        str
            A new regex pattern with the variable name applied, or the
            original pattern if no name is provided.
        """
        if name:
            new_pattern = '(?P<{}>{})'.format(name, pattern)
            return new_pattern
        return pattern
