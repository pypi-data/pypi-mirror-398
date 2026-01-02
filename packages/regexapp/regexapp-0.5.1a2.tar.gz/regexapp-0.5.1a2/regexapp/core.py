"""
regexapp.core
=============
Core functionality for regexapp: pattern building, reference management,
and dynamic test script generation.

This module provides the foundational classes and utilities used to
construct, manage, and validate regular expressions within regexapp.
It also supports generating test scripts across multiple frameworks
(unittest, pytest, Robot Framework, and generic Python snippets).

Contents
--------
Functions
---------
enclose_string(text: str) -> str
    Wrap a string in double quotes or triple double quotes.
create_docstring(test_framework='unittest', author='', email='', company='') -> str
    Generate a module-level docstring for a test script with optional
    metadata such as author, email, and company.
add_reference(name: str, pattern: str, **kwargs) -> None
    Add a keyword reference to the PatternReference collection for
    quick inline testing.
remove_reference(name: str) -> None
    Remove a keyword reference previously added inline.

Classes
-------
RegexBuilder
    Build regex patterns from user data and test data. Provides
    facilities for compiling patterns, generating reports, and
    validating matches.
DynamicTestScriptBuilder
    Generate test scripts dynamically for multiple frameworks using
    regex patterns and test data. Supports unittest, pytest, Robot
    Framework (planned), and generic Python snippets.
UnittestBuilder
    Create unittest scripts from dynamic test case information.
PytestBuilder
    Create pytest scripts from dynamic test case information.
PythonSnippetBuilder
    Create lightweight Python snippet test scripts, including line
    and multiline pattern validation.

Exceptions
----------
RegexBuilderError
    Raised for errors encountered during regex building.
PatternReferenceError
    Raised for invalid operations on pattern references.

Notes
-----
- The module relies on `regexapp.collection.REF` as a baseline
  reference set, which is deep-copied into `BASELINE_REF` for
  local use.
- All builders support optional metadata (author, email, company,
  filename) to embed provenance into generated test scripts.
- Community edition keyword arguments include `prepended_ws`,
  `appended_ws`, and `ignore_case`.
"""


import re
from datetime import datetime
from copy import copy, deepcopy
from collections import OrderedDict
from textwrap import indent

from regexapp import LinePattern
from regexapp import MultilinePattern
from regexapp.exceptions import RegexBuilderError
from regexapp.exceptions import PatternReferenceError

from regexapp.collection import REF
import regexapp
import regexapp.utils as utils

from genericlib.text import dedent_and_strip


BASELINE_REF = deepcopy(REF)


def enclose_string(text):
    """
    Return the given text enclosed in quotes.

    - If the text spans multiple lines, it is wrapped in triple double quotes.
    - If the text is a single line, it is wrapped in standard double quotes.
    - Any existing double quotes inside the text are escaped.

    Parameters
    ----------
    text : str
        Input text to be enclosed.

    Returns
    -------
    str
        A new string with the input text enclosed in either double quotes
        or triple double quotes, depending on its length.
    """
    text = str(text)
    fmt = '"""{}"""' if len(text.splitlines()) > 1 else '"{}"'
    enclosed_txt = fmt.format(text.replace('"', r'\"'))
    return enclosed_txt


def create_docstring(test_framework='unittest',
                     author='', email='', company=''):
    """
    Generate a standardized module-level docstring or header comment
    for a test script.

    The generated text includes metadata such as the test framework,
    author, email, company, and creation date. For Python-based
    frameworks (e.g., unittest, pytest), the output is enclosed in
    triple quotes as a proper docstring. For Robot Framework, the
    output is formatted as a comment block prefixed with `#`.

    Parameters
    ----------
    test_framework : str, optional
        Target test framework. Defaults to "unittest".
        - "unittest" or "pytest": produces a Python docstring.
        - "robotframework": produces a comment block.
    author : str, optional
        Author name. Defaults to empty string.
    email : str, optional
        Author email. Defaults to empty string.
    company : str, optional
        Company name. Defaults to empty string.

    Returns
    -------
    str
        A formatted module docstring or comment block containing
        framework information, author metadata, and creation date.

    Notes
    -----
    - If both `author` and `company` are provided, `author` takes
      precedence in the "Created by" field.
    - The `regexapp.edition` value is included to indicate which
      edition of regexapp generated the script.
    """

    lang = '' if test_framework == 'robotframework' else 'Python '
    fmt = '{}{} script is generated by Regex {} Edition'
    fmt1 = 'Created by  : {}'
    fmt2 = 'Email       : {}'
    fmt3 = 'Company     : {}'
    fmt4 = 'Created date: {:%Y-%m-%d}'

    lst = list()
    author = author or company
    lst.append(fmt.format(lang, test_framework, regexapp.edition))
    author and lst.append(fmt1.format(author))
    email and lst.append(fmt2.format(email))
    company and company != author and lst.append(fmt3.format(company))
    lst.append(fmt4.format(datetime.now()))

    if test_framework == 'robotframework':
        new_lst = [line.strip() for line in indent('\n'.join(lst), '# ').splitlines()]
        comment = '\n'.join(new_lst)
        return comment
    else:
        module_docstr = '"""{}\n"""'.format('\n'.join(lst))
        return module_docstr


class RegexBuilder:
    """
    Core builder for constructing and validating regular expression patterns.

    The `RegexBuilder` class provides functionality to generate regex patterns
    from user-provided data and test data. It supports customization such as
    whitespace handling, case sensitivity, and test name generation. In addition,
    it can produce test scripts for multiple frameworks (unittest, pytest,
    Robot Framework, and generic Python snippets).

    Attributes
    ----------
    user_data : str or list of str
        Input data from the user. Can be a single string or a list of strings.
    test_data : str or list of str
        Test data used to validate generated regex patterns.

    prepended_ws : bool, optional
        If True, prepend a whitespace at the beginning of each pattern.
        Default is False.
    appended_ws : bool, optional
        If True, append a whitespace at the end of each pattern.
        Default is False.
    ignore_case : bool, optional
        If True, prepend the inline flag `(?i)` to make patterns case-insensitive.
        Default is False.

    is_line : bool, optional
        Flag to enable `LinePattern` usage. Default is False.
    is_exact : bool, optional
        Flag to enforce exact matching of patterns. Default is False.
    test_name : str, optional
        Predefined test name. Defaults to empty string.
        - unittest: uses predefined name or generates one from test data.
        - pytest: uses predefined name.
        - Robot Framework: may use either predefined or generated name.
    max_words : int, optional
        Maximum number of words used when generating a test name.
        Default is 6.
    test_cls_name : str, optional
        Name of the test class for unittest/pytest scripts.
        Default is "TestDynamicGenTestScript".

    author : str, optional
        Author name. Defaults to empty string.
    email : str, optional
        Author email. Defaults to empty string.
    company : str, optional
        Company name. Defaults to empty string.

    filename : str, optional
        File name to save the generated test script.
    kwargs : dict, optional
        Additional keyword arguments. Community edition supports:
        `prepended_ws`, `appended_ws`, `ignore_case`.

    patterns : list
        List of regex patterns generated from user data.
    test_report : str
        Report summarizing test execution results.
    test_result : bool
        Boolean flag indicating overall test success or failure.
    user_data_pattern_table : OrderedDict
        Mapping of user data to generated patterns.
    pattern_user_data_table : OrderedDict
        Mapping of patterns back to user data.
    test_data_pattern_table : OrderedDict
        Mapping of test data to generated patterns.
    pattern_test_data_table : OrderedDict
        Mapping of patterns back to test data.

    Methods
    -------
    validate_data(data, name) -> bool
        Validate input data format for regex building.
    build() -> None
        Construct regex patterns from user and test data.
    test(showed=True) -> bool
        Execute tests against generated patterns and return results.
    create_unittest() -> str
        Generate a Python unittest script.
    create_pytest() -> str
        Generate a Python pytest script.
    create_rf_test() -> str
        Generate a Robot Framework test script.
    create_python_test() -> str
        Generate a generic Python test script snippet.

    Raises
    ------
    RegexBuilderError
        Raised if `user_data` or `test_data` is provided in an invalid format.
    """
    def __init__(self, user_data='', test_data='',
                 prepended_ws=False, appended_ws=False, ignore_case=False,
                 test_name='', is_line=False, is_exact=False,
                 max_words=6, test_cls_name='TestDynamicGenTestScript',
                 author='', email='', company='', filename='',
                 **kwargs
                 ):

        self.raw_user_data = user_data
        self.user_data = user_data
        self.test_data = test_data

        self.prepended_ws = prepended_ws
        self.appended_ws = appended_ws
        self.ignore_case = ignore_case

        self.test_name = test_name
        self.is_line = is_line
        self.is_exact = is_exact
        self.max_words = max_words
        self.test_cls_name = test_cls_name
        self.author = author
        self.email = email
        self.company = company
        self.filename = filename
        self.kwargs = kwargs

        self.patterns = []
        self.test_report = ''
        self.test_result = False
        self.user_data_pattern_table = OrderedDict()    # user data via pattern
        self.pattern_user_data_table = OrderedDict()    # pattern via user data
        self.test_data_pattern_table = OrderedDict()    # test data via pattern
        self.pattern_test_data_table = OrderedDict()    # pattern via test data

        BASELINE_REF.load_reference(BASELINE_REF.user_ref_loc, is_warning=False)

    @classmethod
    def validate_data(cls, **kwargs):
        """
        Validate input data for regex building.

        This method checks that each provided keyword argument value is either
        a string or a list of strings. Empty values are considered invalid.
        If any argument fails validation, a `RegexBuilderError` is raised.

        Parameters
        ----------
        **kwargs : keyword arguments
            Arbitrary keyword arguments representing named data inputs.
            Each value must be either:
            - str: a single string of data
            - list of str: a list containing only strings

        Returns
        -------
        bool
            True if all provided data is valid and non-empty,
            False otherwise.

        Raises
        ------
        RegexBuilderError
            If no keyword arguments are provided, or if any value is not
            a string or list of strings, or if a list contains non-string
            elements.
        """
        if not kwargs:
            msg = "Data validation failed: no data provided."
            raise RegexBuilderError(msg)

        is_validated = True
        for name, data in kwargs.items():
            fmt = '{} MUST be string or list of string.'
            if not isinstance(data, (list, str)):
                msg = fmt.format(name)
                raise RegexBuilderError(msg)

            if isinstance(data, list):
                for line in data:
                    if not isinstance(line, str):
                        msg = fmt.format(name)
                        raise RegexBuilderError(msg)
            is_validated &= True if data else False
        return is_validated

    def build(self):
        """
        Construct regex patterns from user-provided data.

        This method validates the `user_data` attribute and generates
        regex patterns based on its content. Patterns are created using
        either `LinePattern` (for line-based input) or `MultilinePattern`
        (for multi-line or grouped input), depending on the `is_line` flag.

        Workflow
        --------
        1. Validate `user_data` using `validate_data`.
        2. If `user_data` is empty, record a failure message in
           `self.test_report` and return early.
        3. Normalize `user_data` into a list of strings:
           - If `is_line` is True: split into lines or copy list/tuple.
           - If `is_line` is False: wrap strings in a list, or join
             nested lists/tuples into multi-line strings.
        4. For each normalized entry, build a regex pattern:
           - `LinePattern`: respects `prepended_ws`, `appended_ws`,
             and `ignore_case`.
           - `MultilinePattern`: respects `ignore_case` and `is_exact`.
        5. Append new patterns to `self.patterns` and update mapping
           tables (`user_data_pattern_table`, `pattern_user_data_table`).

        Returns
        -------
        None
            This method does not return a value. It updates internal
            attributes (`patterns`, `test_report`, mapping tables).

        Raises
        ------
        RegexBuilderError
            If `user_data` fails validation (not a string or list of strings).

        Side Effects
        ------------
        - Updates `self.patterns` with newly built regex patterns.
        - Populates mapping tables for user data ↔ pattern relationships.
        - Prints a message if `user_data` is empty.
        - Sets `self.test_report` when build fails due to empty input.
        """
        data = self.user_data
        self.__class__.validate_data(user_data=data)    # noqa

        if not data:
            self.test_report = "Regex pattern generation failed: no data provided."
            print(self.test_report)
            return

        if self.is_line:
            lst_of_user_data = data[:] if isinstance(data, (list, tuple)) else data.splitlines()
        else:
            if isinstance(data, str):
                lst_of_user_data = [data]
            else:
                lst_of_user_data = []
                for item in data:
                    if isinstance(item, (list, tuple)):
                        lst_of_user_data.append('\n'.join(map(str, item)))
                    else:
                        lst_of_user_data.append(str(item))

        for user_data in lst_of_user_data:
            if self.is_line:
                pattern = LinePattern(
                    user_data,
                    prepended_ws=self.prepended_ws,
                    appended_ws=self.appended_ws,
                    ignore_case=self.ignore_case
                )
            else:
                pattern = MultilinePattern(
                    user_data,
                    ignore_case=self.ignore_case,
                    is_exact=self.is_exact
                )

            pattern not in self.patterns and self.patterns.append(pattern)
            self.user_data_pattern_table[user_data] = pattern
            self.pattern_user_data_table[pattern] = user_data

    def test(self, showed=False):
        """
        Execute regex pattern tests against provided test data.

        This method validates the `test_data` attribute and attempts to
        match each entry against the regex patterns built by the instance.
        It records results, updates mapping tables, and optionally prints
        a formatted test report.

        Parameters
        ----------
        showed : bool, optional
            If True, print the generated test report to stdout.
            Default is False.

        Returns
        -------
        bool
            True if all test data matched at least one pattern,
            False otherwise.

        Raises
        ------
        RegexBuilderError
            If `test_data` is invalid (not a string or list of strings).

        Workflow
        --------
        1. Validate `test_data` using `validate_data`.
        2. If `test_data` is empty, record a failure message in
           `self.test_report`, optionally print it, and return False.
        3. Normalize `test_data` into a list of strings:
           - If `is_line` is True: split into lines or copy list/tuple.
           - Otherwise: wrap strings in a list, or join nested lists/tuples
             into multi-line strings.
        4. For each regex pattern in `self.patterns`:
           - Attempt to match against each test data entry.
           - Record matches, including any named groups.
           - Update mapping tables (`test_data_pattern_table`,
             `pattern_test_data_table`).
           - Append results to the report.
        5. Store overall success/failure in `self.test_result` and
           formatted report in `self.test_report`.

        Side Effects
        ------------
        - Updates `self.test_result` with overall pass/fail status.
        - Updates `self.test_report` with a detailed report string.
        - Populates mapping tables for test data ↔ pattern relationships.
        - Optionally prints the report if `showed=True`.
        """
        data = self.test_data
        self.__class__.validate_data(test_data=data)    # noqa

        if not data:
            self.test_report = "Test execution failed: no data provided."
            showed and print(self.test_report)
            return False

        if self.is_line:
            lst_of_test_data = data[:] if isinstance(data, (list, tuple)) else data.splitlines()
        else:
            if isinstance(data, str):
                lst_of_test_data = [data]
            else:
                lst_of_test_data = []
                for item in data:
                    if isinstance(item, (list, tuple)):
                        lst_of_test_data.append('\n'.join(map(str, item)))
                    else:
                        lst_of_test_data.append(str(item))

        result = ['Test Data:', '-' * 9, '\n'.join(lst_of_test_data), '']
        result += ['Matched Result:', '-' * 14]

        test_result = True
        for pat in self.patterns:
            is_matched = False
            lst = []
            for test_data in lst_of_test_data:
                match = re.search(pat, test_data)
                if match:
                    is_matched = True
                    match.groupdict() and lst.append(match.groupdict())
                    self.test_data_pattern_table[test_data] = pat
                    self.pattern_test_data_table[pat] = test_data

            test_result &= is_matched
            tr = 'NO' if not is_matched else lst if lst else 'YES'
            result.append('pattern: {}'.format(pat))
            result.append('matched: {}'.format(tr))
            result.append('-' * 10)

        self.test_result = test_result
        self.test_report = '\n'.join(result)
        showed and print(self.test_report)

        return test_result

    def create_unittest(self):
        """
        Generate a Python unittest script from the current RegexBuilder instance.

        This method delegates to `DynamicTestScriptBuilder` to construct a
        fully formatted unittest script based on the regex patterns and
        test data defined in the current builder. The generated script
        includes a test class, test methods, and metadata such as author,
        email, and company if provided.

        Returns
        -------
        str
            A string containing the complete Python unittest script.

        Notes
        -----
        - The returned script is dynamically generated and can be saved
          to a file or executed directly.
        - Metadata (author, email, company, filename) from the builder
          instance is embedded into the script if available.
        - This method does not execute the generated tests; it only
          produces the script text.
        """
        factory = DynamicTestScriptBuilder(test_info=self)
        script = factory.create_unittest()
        return script

    def create_pytest(self):
        """
        Generate a Python pytest script from the current RegexBuilder instance.

        This method delegates to `DynamicTestScriptBuilder` to construct a
        fully formatted pytest script based on the regex patterns and
        test data defined in the current builder. The generated script
        includes a test class, test functions, and optional metadata such
        as author, email, and company if provided.

        Returns
        -------
        str
            A string containing the complete Python pytest script.

        Notes
        -----
        - The returned script is dynamically generated and can be saved
          to a file or executed directly with pytest.
        - Metadata (author, email, company, filename) from the builder
          instance is embedded into the script if available.
        - This method does not execute the generated tests; it only
          produces the script text.
        """
        factory = DynamicTestScriptBuilder(test_info=self)
        script = factory.create_pytest()
        return script

    def create_rf_test(self):
        """dynamically generate Robotframework script

        Returns
        -------
        str: Robotframework test script
        """
        factory = DynamicTestScriptBuilder(test_info=self)
        script = factory.create_rf_test()
        return script

    def create_python_test(self):
        """
        Generate a Robot Framework test script from the current RegexBuilder instance.

        This method delegates to `DynamicTestScriptBuilder` to construct a
        Robot Framework test script based on the regex patterns and test
        data defined in the current builder. The generated script includes
        test cases and optional metadata such as author, email, and company
        if provided.

        Returns
        -------
        str
            A string containing the complete Robot Framework test script.

        Notes
        -----
        - The returned script is dynamically generated and can be saved
          to a file or executed directly with Robot Framework.
        - Metadata (author, email, company, filename) from the builder
          instance is embedded into the script if available.
        - This method does not execute the generated tests; it only
          produces the script text.
        - Robot Framework support may be partially implemented depending
          on the edition of regexapp.
        """
        factory = DynamicTestScriptBuilder(test_info=self)
        script = factory.create_python_test()
        return script


def add_reference(name='', pattern='', **kwargs):
    """
    Add a keyword reference to the PatternReference collection.

    This function registers a new keyword-to-pattern mapping for quick
    inline testing. If the keyword already exists in the baseline
    references (`system_references.yaml` or `user_references.yaml`),
    a `PatternReferenceError` is raised. Special handling is provided
    for the keyword `"datetime"`, allowing additional format options
    to be passed via keyword arguments.

    Parameters
    ----------
    name : str, optional
        The keyword to associate with the regex pattern.
        Must be non-empty.
    pattern : str, optional
        The regex pattern string to register.
    **kwargs : dict, optional
        Additional keyword arguments for special cases.
        For `"datetime"`, keys matching `formatN` (e.g., `format1`,
        `format2`) can be used to define custom datetime formats.

    Returns
    -------
    None
        This function does not return a value. It updates the
        `REF` collection in place.

    Raises
    ------
    PatternReferenceError
        If `name` is empty, or if the keyword already exists in
        `system_references.yaml` or `user_references.yaml`.

    Notes
    -----
    - Inline references are intended for quick testing and do not
      persist beyond the current runtime unless explicitly saved.
    - For `"datetime"`, additional formats are merged into the
      existing reference entry.
    """
    if not name:
        fmt = '{} keyword can not be empty name.'
        PatternReferenceError(fmt.format(name))

    obj = dict(pattern=pattern,
               description='inline_{}_{}'.format(name, pattern))
    if name not in REF:
        REF[name] = obj
    else:
        if name == 'datetime':
            for key, value in kwargs.items():
                if re.match(r'format\d+$', key):
                    REF['datetime'][key] = value
        else:
            if name not in BASELINE_REF:
                REF[name] = obj
            else:
                fmt = ('{} already exists in system_references.yaml '
                       'or user_references.yaml')
                raise PatternReferenceError(fmt.format(name))


def remove_reference(name=''):
    """
    Remove a keyword reference from the PatternReference collection.

    This function deletes an inline keyword-to-pattern mapping previously
    added via `add_reference`. Baseline references defined in
    `system_references.yaml` or `user_references.yaml` cannot be removed,
    except for the special case `"datetime"`, which is reset to its
    baseline definition.

    Parameters
    ----------
    name : str, optional
        The keyword to remove. Must be non-empty.

    Returns
    -------
    None
        This function does not return a value. It updates the `REF`
        collection in place.

    Raises
    ------
    PatternReferenceError
        - If `name` is empty.
        - If the keyword exists only in baseline references and cannot
          be removed (other than `"datetime"`).
        - If the keyword does not exist in the current references.

    Notes
    -----
    - Inline references are intended for quick testing and can be
      removed with this function.
    - For `"datetime"`, the reference is restored to its baseline
      configuration rather than being deleted outright.
    """
    if not name:
        error = f"Keyword '{name}' must have a non-empty name."
        raise PatternReferenceError(error)

    if name in REF:
        if name not in BASELINE_REF:
            REF.pop(name)
        else:
            if name == 'datetime':
                REF['datetime'] = deepcopy(BASELINE_REF['datetime'])
            else:
                error = (f"Keyword {repr(name)} cannot be removed from "
                         f"system_references.yaml or user_references.yaml.")
                raise PatternReferenceError(error)
    else:
        error = f"Keyword {repr(name)} cannot be removed because it does not exist."
        raise PatternReferenceError(error)


class DynamicTestScriptBuilder:
    """
    Builder for dynamically generating test scripts across multiple frameworks.

    The `DynamicTestScriptBuilder` constructs test scripts for unittest,
    pytest, Robot Framework, or generic Python snippets based on regex
    patterns and test data. It supports both direct use of a `RegexBuilder`
    instance and a simplified list format containing `[user_data, test_data]`.
    The builder automates test name generation, pattern compilation, and
    script creation, embedding optional metadata such as author, email,
    company, and filename.

    Attributes
    ----------
    test_info : RegexBuilder or list
        Either a `RegexBuilder` instance or a two-element list containing
        [user_data, test_data].
    test_name : str
        Predefined test name. Defaults to empty string.
        - unittest: uses predefined name or generates one from test data.
        - pytest: uses predefined name.
        - Robot Framework: may use either predefined or generated name.
    is_line : bool
        Flag to enable `LinePattern`. Defaults to False.
    max_words : int
        Maximum number of words used when generating a test name.
        Default is 6.
    test_cls_name : str
        Name of the test class for unittest/pytest scripts.
        Default is "TestDynamicGenTestScript".
    author : str
        Author name. Defaults to empty string.
    email : str
        Author email. Defaults to empty string.
    company : str
        Company name. Defaults to empty string.
    filename : str
        File name to save the generated test script.
    kwargs : dict
        Optional keyword arguments. Community edition supports:
        `prepended_ws`, `appended_ws`, `ignore_case`.
    prepended_ws : bool
        If True, prepend a whitespace at the beginning of each pattern.
        Default is False.
    appended_ws : bool
        If True, append a whitespace at the end of each pattern.
        Default is False.
    ignore_case : bool
        If True, prepend the inline flag `(?i)` to make patterns case-insensitive.
        Default is False.
    lst_of_tests : list
        Compiled list of test cases, each containing test name, test data,
        prepared data, and pattern.
    test_data : str or None
        Test data string used for validation. Initialized as None.
    patterns : list or None
        List of regex patterns generated from user data. Initialized as None.

    Methods
    -------
    compile_test_info() -> None
        Prepare a list of test cases from `test_info`.
    generate_test_name(test_data: str = '') -> str
        Generate a valid test name from provided test data.
    create_unittest() -> str
        Generate a Python unittest script.
    create_pytest() -> str
        Generate a Python pytest script.
    create_rf_test() -> str
        Generate a Robot Framework test script (may be partially implemented).
    create_python_test() -> str
        Generate a generic Python test script snippet.

    Notes
    -----
    - Metadata (author, email, company, filename) is embedded into generated
      scripts if provided.
    - Inline keyword arguments (`prepended_ws`, `appended_ws`, `ignore_case`)
      are consumed during initialization and removed from `kwargs`.
    - This class does not execute generated tests; it only produces script text.
    """
    def __init__(self, test_info=None, test_name='', is_line=False,
                 max_words=6, test_cls_name='TestDynamicGenTestScript',
                 author='', email='', company='', filename='',
                 **kwargs):

        self.test_info = test_info
        if isinstance(test_info, RegexBuilder):
            self.test_name = test_info.test_name
            self.is_line = is_line or test_info.is_line
            self.max_words = test_info.max_words
            self.test_cls_name = test_info.test_cls_name

            self.author = author or test_info.author
            self.email = email or test_info.email
            self.company = company or test_info.company
            self.filename = filename or test_info.filename

            self.prepended_ws = test_info.prepended_ws
            self.appended_ws = test_info.appended_ws
            self.ignore_case = test_info.ignore_case
            self.kwargs = test_info.kwargs
        else:
            self.test_name = test_name
            self.is_line = is_line
            self.max_words = max_words
            self.test_cls_name = test_cls_name

            self.author = author
            self.email = email
            self.company = company
            self.filename = filename

            self.prepended_ws = kwargs.get('prepended_ws', False)
            self.appended_ws = kwargs.get('appended_ws', False)
            self.ignore_case = kwargs.get('ignore_case', False)
            self.kwargs = kwargs

        'prepended_ws' in self.kwargs and self.kwargs.pop('prepended_ws')
        'appended_ws' in self.kwargs and self.kwargs.pop('appended_ws')
        'ignore_case' in self.kwargs and self.kwargs.pop('ignore_case')

        self.lst_of_tests = []
        self.test_data = None
        self.patterns = None
        self.compile_test_info()

    def compile_test_info(self):
        """
        Compile test cases from the provided test information.

        This method processes `test_info` (either a `RegexBuilder` instance
        or a two-element list of `[user_data, test_data]`) to generate a
        structured list of test cases. Each test case includes a generated
        test name, the test data, the prepared user data, and the associated
        regex pattern. The compiled test cases are stored in
        `self.lst_of_tests`.

        Workflow
        --------
        1. Reset `self.lst_of_tests` to an empty list.
        2. Determine the source of `test_info`:
           - If a `RegexBuilder` instance: copy it and extract `test_data`.
           - If a list: validate format, extract `user_data` and `test_data`,
             and construct a new `RegexBuilder` instance.
        3. Build regex patterns and run tests using the `RegexBuilder`.
        4. Extract generated patterns and mapping tables.
        5. Validate that prepared data exists; raise `RegexBuilderError` if not.
        6. For each test data entry:
           - Generate a test name via `generate_test_name`.
           - Retrieve prepared user data from mapping tables.
           - Append `[test_name, test_data, prepared_data, pattern]` to
             `self.lst_of_tests`.

        Returns
        -------
        None
            This method does not return a value. It updates internal
            attributes (`lst_of_tests`, `test_data`, `patterns`).

        Raises
        ------
        RegexBuilderError
            - If `test_info` is not a valid `RegexBuilder` or two-element list.
            - If no prepared data is available to build test cases.

        Side Effects
        ------------
        - Updates `self.lst_of_tests` with compiled test cases.
        - Updates `self.test_data` with extracted test data.
        - Updates `self.patterns` with regex patterns generated by `RegexBuilder`.
        """
        self.lst_of_tests = []
        test_info = self.test_info
        if isinstance(test_info, RegexBuilder):
            # testable = deepcopy(test_info)
            testable = copy(test_info)
            self.test_data = testable.test_data
        else:
            chk = isinstance(test_info, list) and len(test_info) == 2
            if not chk:
                raise RegexBuilderError('Invalid test_info format')

            user_data, test_data = self.test_info
            self.test_data = test_data

            testable = RegexBuilder(
                user_data=user_data, test_data=test_data,
                is_line=self.is_line,
                prepended_ws=self.prepended_ws,
                appended_ws=self.appended_ws,
                ignore_case=self.ignore_case
            )
        testable.build()
        testable.test()

        self.patterns = testable.patterns

        user_data_pattern_table = testable.user_data_pattern_table
        pattern_user_data_table = testable.pattern_user_data_table
        test_data_pattern_table = testable.test_data_pattern_table

        if not test_data_pattern_table and not user_data_pattern_table:
            error = "Test script generation failed: no prepared data provided."
            raise RegexBuilderError(error)

        for test_data, pattern in test_data_pattern_table.items():
            test_name = self.generate_test_name(test_data=test_data)
            prepared_data = pattern_user_data_table.get(pattern)
            self.lst_of_tests.append([test_name, test_data, prepared_data, pattern])

    def generate_test_name(self, test_data=''):
        """
        Generate a sanitized test function name from provided test data.

        This method normalizes the input string, extracts up to `max_words`
        words, and converts them into a safe identifier suitable for use
        as a Python test function name. If a predefined `self.test_name`
        exists, it takes precedence over the generated name. The final
        name is guaranteed to start with the prefix ``test_``.

        Parameters
        ----------
        test_data : str, optional
            Raw test data string used to derive the test name.
            Defaults to an empty string.

        Returns
        -------
        str
            A valid test function name string that:
            - Contains only lowercase alphanumeric characters and underscores.
            - Is truncated to at most `max_words` words.
            - Always begins with ``test_``.

        Notes
        -----
        - Non-alphanumeric characters are replaced with underscores.
        - Leading and trailing underscores are stripped.
        - If `test_data` is empty and no predefined `self.test_name` exists,
          the result will be ``test_`` followed by an empty suffix.
        - This ensures compatibility with Python naming conventions for
          test discovery in frameworks such as unittest and pytest.
        """
        pat = r'[^0-9a-zA-Z]*\s+[^0-9a-zA-Z]*'
        test_data = str(test_data).lower().strip()
        test_data = ' '.join(re.split(pat, test_data)[:self.max_words])
        test_name = self.test_name or test_data
        test_name = re.sub(r'[^0-9a-z]+', '_', test_name)
        test_name = test_name.strip('_')
        if not test_name.startswith('test_'):
            test_name = 'test_{}'.format(test_name)
        return test_name

    def create_unittest(self):
        """
        Generate and optionally save a Python unittest script.

        This method delegates to `UnittestBuilder` to construct a complete
        unittest script based on the test cases and configuration stored
        in the current `DynamicTestScriptBuilder` instance. The generated
        script includes a test class, test methods, and optional metadata
        such as author, email, company, and filename. If `self.filename`
        is set, the script is also written to disk.

        Returns
        -------
        str
            A string containing the full Python unittest script.

        Raises
        ------
        OSError
            If writing the generated script to disk fails.

        Notes
        -----
        - The returned script is dynamically generated and can be executed
          directly with Python’s unittest framework.
        - Metadata (author, email, company, filename) is embedded into the
          script if available.
        - Saving to disk is performed via `utils.File.write`; if `self.filename`
          is empty, the script is returned but not saved.
        - This method does not execute the generated tests; it only produces
          the script text.
        """
        factory = UnittestBuilder(self)
        test_script = factory.create()
        if self.filename:
            utils.File.write(self.filename, test_script)
        return test_script

    def create_pytest(self):
        """
        Generate and optionally save a Python pytest script.

        This method delegates to `PytestBuilder` to construct a complete
        pytest script based on the test cases and configuration stored
        in the current `DynamicTestScriptBuilder` instance. The generated
        script includes a test class, test functions, and optional metadata
        such as author, email, company, and filename. If `self.filename`
        is set, the script is also written to disk.

        Returns
        -------
        str
            A string containing the full Python pytest script.

        Raises
        ------
        OSError
            If writing the generated script to disk fails.

        Notes
        -----
        - The returned script is dynamically generated and can be executed
          directly with pytest.
        - Metadata (author, email, company, filename) is embedded into the
          script if available.
        - Saving to disk is performed via `utils.File.write`; if `self.filename`
          is empty, the script is returned but not saved.
        - This method does not execute the generated tests; it only produces
          the script text.
        """
        factory = PytestBuilder(self)
        test_script = factory.create()
        if self.filename:
            utils.File.write(self.filename, test_script)
        return test_script

    def create_rf_test(self):     # noqa
        """
        Generate a Robot Framework test script.

        This method is intended to construct a Robot Framework test script
        based on the current builder state (test cases, configuration, and
        patterns). At present, the implementation is not available and will
        raise a ``NotImplementedError``.

        Returns
        -------
        str
            A Robot Framework test script string once implemented.

        Raises
        ------
        NotImplementedError
            Always raised until Robot Framework test generation is
            implemented.
        """
        msg = "Robotframework test script generation is not implemented yet."
        raise NotImplementedError(msg)

    def create_python_test(self):
        """
        Generate and optionally save a generic Python test script.

        This method delegates to `PythonSnippetBuilder` to construct a
        lightweight Python test script based on the test cases and
        configuration stored in the current `DynamicTestScriptBuilder`
        instance. The generated script is returned as a string and, if
        `self.filename` is set, also written to disk.

        Returns
        -------
        str
            A string containing the complete Python test script.

        Raises
        ------
        OSError
            If writing the generated script to disk fails.

        Notes
        -----
        - The returned script is dynamically generated and can be executed
          directly with Python.
        - Metadata (author, email, company, filename) is embedded into the
          script if available.
        - Saving to disk is performed via `utils.File.write`; if `self.filename`
          is empty, the script is returned but not saved.
        - This method does not execute the generated tests; it only produces
          the script text.
        """
        factory = PythonSnippetBuilder(self)
        test_script = factory.create()
        if self.filename:
            utils.File.write(self.filename, test_script)
        return test_script


class UnittestBuilder:
    """
    Builder for dynamically generating Python unittest scripts.

    The `UnittestBuilder` constructs a complete unittest script based on
    the test cases and configuration provided by a `DynamicGenTestScript`
    instance. It automates the creation of test classes, test methods,
    and loader functions, embedding optional metadata such as author,
    email, and company into the module-level docstring.

    Attributes
    ----------
    tc_gen : DynamicGenTestScript
        A `DynamicGenTestScript` instance containing test cases,
        patterns, and configuration details used to generate the
        unittest script.
    module_docstring : str
        A module-level docstring snippet generated via `create_docstring`,
        including metadata such as author, email, and company.

    Methods
    -------
    create_testcase_class() -> str
        Generate the Python code for the unittest test class definition.
    create_testcase_method() -> str
        Generate Python code for individual unittest test methods
        based on compiled test cases.
    create_testcase_load() -> str
        Generate Python code for loading and running the unittest suite.
    create() -> str
        Assemble the complete unittest script, including the module
        docstring, test class, test methods, and loader function.

    Notes
    -----
    - The generated script is returned as a string and can be saved
      to a file or executed directly with Python’s unittest framework.
    - Metadata (author, email, company) is embedded into the script
      if provided by the `DynamicGenTestScript` instance.
    - This class does not execute the generated tests; it only produces
      the script text.
    """
    def __init__(self, tc_gen):
        self.tc_gen = tc_gen
        self.module_docstring = create_docstring(
            test_framework='unittest',
            author=tc_gen.author,
            email=tc_gen.email,
            company=tc_gen.company,
        )

    def create_testcase_class(self):
        """
        Generate the partial definition of a unittest test class.

        This method constructs the initial portion of a Python unittest
        class, including the module-level docstring, required imports,
        and the class header with its constructor. The generated snippet
        serves as the foundation for building a complete unittest script,
        to which test methods and loader functions can later be appended.

        Returns
        -------
        str
            A string containing the partial unittest class definition,
            including:
            - The module docstring with metadata (author, email, company).
            - Imports for `unittest` and `re`.
            - A test class definition derived from `self.tc_gen.test_cls_name`.
            - An `__init__` method that initializes `test_name`, `test_data`,
              and `pattern`.

        Notes
        -----
        - The returned script is incomplete by design; it provides only
          the class skeleton and constructor.
        - Additional methods (e.g., test cases, loader functions) must be
          appended separately to form a runnable unittest script.
        - Metadata is embedded via `self.module_docstring`, generated
          during initialization of the builder.
        """
        tmpl = dedent_and_strip("""
          {module_docstring}

          import unittest
          import re

          class {test_cls_name}(unittest.TestCase):
              def __init__(self, test_name='', test_data=None, pattern=None):
                  super().__init__(test_name)
                  self.test_data = test_data
                  self.pattern = pattern
        """)

        tc_gen = self.tc_gen
        partial_script = tmpl.format(
            module_docstring=self.module_docstring,
            test_cls_name=tc_gen.test_cls_name
        )

        return partial_script

    def create_testcase_method(self):
        """
        Generate partial unittest method definitions for compiled test cases.

        This method constructs Python unittest test methods based on the
        list of test cases stored in `self.tc_gen.lst_of_tests`. Each
        generated method attempts to match `self.test_data` against
        `self.pattern` using `re.search`, and asserts that a match is
        found. The resulting code snippet can be appended to the test
        class definition created by `create_testcase_class`.

        Workflow
        --------
        1. Define a template for a unittest method that:
           - Performs a regex search using `self.pattern` and `self.test_data`.
           - Asserts that the result is not None.
        2. Iterate over all test cases in `self.tc_gen.lst_of_tests`.
        3. For each test case:
           - Format the template with the generated test name.
           - Indent the method definition for proper placement inside a class.
           - Avoid duplicates by checking against previously added methods.
        4. Concatenate all method definitions into a single string.

        Returns
        -------
        str
            A string containing one or more unittest method definitions,
            each corresponding to a compiled test case.

        Notes
        -----
        - The returned script is partial; it provides only the test methods
          and must be combined with the class definition and loader to form
          a complete unittest script.
        - Each generated method name is derived from `generate_test_name`
          and guaranteed to be a valid Python identifier.
        - Duplicate method definitions are skipped to prevent redundancy.
        """
        tmpl = dedent_and_strip("""
            def {test_name}(self):
                result = re.search(self.pattern, self.test_data)
                self.assertIsNotNone(result)
        """)

        tc_gen = self.tc_gen
        lst = []

        for test in tc_gen.lst_of_tests:
            test_name = test[0]
            method_def = tmpl.format(test_name=test_name)
            method_def = indent(method_def, ' ' * 4)
            if method_def not in lst:
                lst.append(method_def)
                lst.append('')

        partial_script = '\n'.join(lst)
        return partial_script

    def create_testcase_load(self):
        """
        Generate the partial definition of a unittest `load_tests` function.

        This method constructs a `load_tests` function that dynamically
        assembles a `unittest.TestSuite` from the compiled test cases in
        `self.tc_gen.lst_of_tests`. Each test case is inserted into the
        suite by instantiating the generated test class with its name,
        data, and associated regex pattern. The returned snippet can be
        appended to the test class and method definitions to form a
        complete unittest script.

        Workflow
        --------
        1. Define a template for the `load_tests` function that:
           - Initializes a `unittest.TestSuite`.
           - Iterates over prepared arguments (test name, test data, pattern).
           - Instantiates the test class (`self.tc_gen.test_cls_name`) for
             each argument.
           - Adds each test case to the suite.
           - Returns the assembled suite.
        2. Build argument entries for each test case in `self.tc_gen.lst_of_tests`:
           - Format test name, test data, and pattern.
           - Insert descriptive comments for readability.
           - Ensure proper indentation for valid Python code.
        3. Insert the generated argument list into the template.
        4. Return the completed `load_tests` function definition as a string.

        Returns
        -------
        str
            A string containing the partial definition of a unittest
            `load_tests` function, including:
            - Initialization of an empty test suite.
            - Argument insertion for each compiled test case.
            - Loop to instantiate and add test cases to the suite.

        Notes
        -----
        - The returned script is partial; it provides only the loader
          function and must be combined with the class and method
          definitions to form a runnable unittest script.
        - Each test case entry includes inline comments for clarity,
          showing the test name, test data, and pattern.
        - The generated loader ensures that all compiled test cases are
          discoverable and executable by the unittest framework.
        """

        tmpl = dedent_and_strip("""
            def load_tests(loader, tests, pattern):
                test_cases = unittest.TestSuite()
                
                {data_insertion}
                
                for arg in arguments:
                    test_name, test_data, pattern = arg
                    testcase = {test_cls_name}(
                        test_name=test_name,
                        test_data=test_data,
                        pattern=pattern
                    )
                    test_cases.addTest(testcase)
                return test_cases
        """)

        tmpl_data = dedent_and_strip("""
            arguments.append(
                (
                    {test_name},    # test name
                    {test_data},    # test data
                    r{pattern}   # pattern
                )
            )
        """)

        tc_gen = self.tc_gen
        lst = ['arguments = list()']

        test_desc_fmt = '    # test case #{:0{}} - {}'
        spacers = len(str(len(tc_gen.lst_of_tests)))
        for index, test in enumerate(tc_gen.lst_of_tests, 1):
            test_name, test_data, _, pattern = test
            test_data = enclose_string(test_data)
            data = tmpl_data.format(
                test_name=enclose_string(test_name),
                test_data='__test_data_placeholder__',
                pattern=enclose_string(pattern))
            lst.append('')
            lst.append(test_desc_fmt.format(index, spacers, test_name))
            new_data = indent(data, ' ' * 4)
            new_data = new_data.replace('__test_data_placeholder__', test_data)
            lst.append(new_data)

        data_insertion = '\n'.join(lst)
        sub_script = tmpl.format(
            data_insertion=data_insertion,
            test_cls_name=tc_gen.test_cls_name
        )
        return sub_script

    def create(self):
        """return Python unittest script"""
        tc_class = self.create_testcase_class()
        tc_method = self.create_testcase_method()
        tc_load = self.create_testcase_load()

        test_script = '{}\n\n{}\n\n{}'.format(tc_class, tc_method, tc_load)
        return test_script


class PytestBuilder:
    """
    Builder for dynamically generating Python pytest scripts.

    The `PytestBuilder` constructs a complete pytest script based on
    the test cases and configuration provided by a `DynamicGenTestScript`
    instance. It automates the creation of test functions and embeds
    optional metadata such as author, email, and company into the
    module-level docstring.

    Attributes
    ----------
    tc_gen : DynamicGenTestScript
        A `DynamicGenTestScript` instance containing test cases,
        patterns, and configuration details used to generate the
        pytest script.
    module_docstring : str
        A module-level docstring snippet generated via `create_docstring`,
        including metadata such as author, email, and company.

    Methods
    -------
    create() -> str
        Assemble and return the complete pytest script, including
        the module docstring and all generated test functions.

    Notes
    -----
    - The generated script is returned as a string and can be saved
      to a file or executed directly with pytest.
    - Metadata (author, email, company) is embedded into the script
      if provided by the `DynamicGenTestScript` instance.
    - This class does not execute the generated tests; it only produces
      the script text.
    """
    def __init__(self, tc_gen):
        self.tc_gen = tc_gen
        self.module_docstring = create_docstring(
            test_framework='pytest',
            author=tc_gen.author,
            email=tc_gen.email,
            company=tc_gen.company,
        )

    def create(self):
        """
        Assemble and return a complete pytest script.

        This method constructs a fully formatted pytest script based on
        the test cases stored in `self.tc_gen.lst_of_tests`. It embeds
        metadata into the module-level docstring, defines a test class,
        and generates a parameterized test function that validates regex
        patterns against provided test data.

        Workflow
        --------
        1. Define a template for the pytest script that includes:
           - The module docstring with metadata (author, email, company).
           - Imports for `pytest` and `re`.
           - A test class definition (`self.tc_gen.test_cls_name`).
           - A parameterized test function using `pytest.mark.parametrize`.
        2. Build parameterized data entries for each test case:
           - Format test data and regex pattern.
           - Insert inline comments for readability.
           - Use placeholders to safely handle string quoting.
        3. Replace placeholders with actual test data values.
        4. Ensure the test function name begins with ``test_``.
        5. Format and clean up the final script for consistent indentation.

        Returns
        -------
        str
            A string containing the complete pytest script, including
            module docstring, test class, and parameterized test function.

        Notes
        -----
        - The returned script is dynamically generated and can be saved
          to a file or executed directly with pytest.
        - Metadata (author, email, company) is embedded into the script
          if available.
        - Each test case is parameterized, allowing pytest to run them
          individually with clear reporting.
        - This method does not execute the generated tests; it only
          produces the script text.
        """

        tmpl = dedent_and_strip("""
            {module_docstring}
            
            import pytest
            import re
            
            class {test_cls_name}:
                @pytest.mark.parametrize(
                    ('test_data', 'pattern'),
                    (
                        {parametrize_data}
                    )
                )
                def {test_name}(self, test_data, pattern):
                    result = re.search(pattern, test_data)
                    assert result is not None
        """)

        tmpl_data = dedent_and_strip("""
            (
                {test_data},    # test data
                r{pattern}   # pattern
            ),
        """)

        tc_gen = self.tc_gen
        lst = []
        placeholder_table = dict()
        for index, test in enumerate(tc_gen.lst_of_tests):
            _, test_data, _, pattern = test
            test_data = enclose_string(test_data)
            key = '__test_data_placeholder_{}__'.format(index)
            placeholder_table[key] = test_data

            kw = dict(test_data=key,
                      pattern=enclose_string(pattern))
            parametrize_item = tmpl_data.format(**kw)
            parametrize_item = indent(parametrize_item, ' ' * 12)
            lst.append(parametrize_item)

        parametrize_data = '\n'.join(lst).strip()

        for key, value in placeholder_table.items():
            parametrize_data = parametrize_data.replace(key, value)

        test_name = tc_gen.test_name or 'test_generating_script'
        if not test_name.startswith('test_'):
            test_name = 'test_{}'.format(test_name)

        test_script = tmpl.format(
            module_docstring=self.module_docstring,
            test_cls_name=tc_gen.test_cls_name,
            test_name=test_name,
            parametrize_data=parametrize_data
        )
        test_script = '\n'.join(line.rstrip() for line in test_script.splitlines())
        return test_script


class PythonSnippetBuilder:
    """
    Builder for dynamically generating lightweight Python test scripts.

    The `PythonSnippetBuilder` constructs simple Python test snippets
    based on the test cases and configuration provided by a
    `DynamicGenTestScript` instance. Unlike full framework builders
    (e.g., unittest or pytest), this builder produces minimal scripts
    that demonstrate regex validation logic in a straightforward,
    executable form. Metadata such as author, email, and company is
    embedded into the module-level docstring.

    Attributes
    ----------
    tc_gen : DynamicGenTestScript
        A `DynamicGenTestScript` instance containing test cases,
        patterns, and configuration details used to generate the
        Python snippet script.
    module_docstring : str
        A module-level docstring snippet generated via `create_docstring`,
        including metadata such as author, email, and company.

    Methods
    -------
    create() -> str
        Assemble and return the complete Python test script, including
        the module docstring and generated test functions.
    create_line_via_pattern_script(test_data: str, pattern: str) -> str
        Generate a script snippet that tests a single line of input
        against a single regex pattern.
    create_line_via_patterns_script(test_data: str, patterns: list[str]) -> str
        Generate a script snippet that tests a single line of input
        against multiple regex patterns.
    create_multiline_via_pattern_script(test_data: str, pattern: str) -> str
        Generate a script snippet that tests multi-line input against
        a single regex pattern.

    Notes
    -----
    - The generated scripts are returned as strings and can be saved
      to a file or executed directly with Python.
    - Metadata (author, email, company) is embedded into the script
      if provided by the `DynamicGenTestScript` instance.
    - This class does not execute the generated tests; it only produces
      the script text.
    """
    def __init__(self, tc_gen):
        self.tc_gen = tc_gen
        self.module_docstring = create_docstring(
            test_framework='test',
            author=tc_gen.author,
            email=tc_gen.email,
            company=tc_gen.company,
        )

    def create_line_via_pattern_script(self, test_data, pattern):
        """
        Generate a Python test script that validates a regex pattern against line-based input.

        This method constructs a standalone Python script snippet that tests
        each line of the provided `test_data` against the given regex `pattern`.
        The generated script prints the pattern being tested, iterates through
        each line of the input, and reports whether matches are found. If no
        matches occur, the script outputs "Result: No match".

        Parameters
        ----------
        test_data : str
            A string containing one or more lines of test data to validate.
        pattern : str
            A regex pattern string to apply against each line of the test data.

        Returns
        -------
        str
            A complete Python script as a string, including:
            - The module-level docstring with metadata (author, email, company).
            - Imports for `re`.
            - Inline comments describing test data and regex pattern.
            - A `test_regex` function that performs line-by-line regex matching.
            - A function call to execute the test.

        Notes
        -----
        - Matches are reported with either the full match or captured groups
          if the regex defines named groups.
        - The script is dynamically generated and can be saved to a file or
          executed directly with Python.
        - This method does not execute the test itself; it only produces
          the script text.
        """

        tmpl = dedent_and_strip('''
            {module_docstring}

            import re

            # test data
            test_data = {test_data}

            # regex pattern
            pattern = r{pattern}

            def test_regex(test_data, pattern):
                """test regular expression

                Parameters
                ----------
                test_data (str): a test data
                pattern (str): a regular expression pattern
                """
                print("Pattern: {{}}".format(pattern))
                is_matched = False
                for index, line in enumerate(test_data.splitlines(), 1):
                    match = re.search(pattern, line)
                    if match:
                        is_matched = True
                        if match.groupdict():
                            print("Result{{}}: {{}}".format(index, match.groupdict()))
                        else:
                            print("Result{{}}: {{}}".format(index, match.group()))
                else:
                    if not is_matched:
                        print("Result: No match")

            # function call
            test_regex(test_data, pattern)
        ''')

        test_script = tmpl.format(
            module_docstring=self.module_docstring,
            test_data=test_data,
            pattern=pattern
        )
        return test_script

    def create_line_via_patterns_script(self, test_data, patterns):
        """return python snippet script - line via patterns

        Parameters
        ----------
        test_data (str): a test data.
        patterns (list): a list of patterns.

        Returns
        -------
        str: a python test script
        """
        tmpl = dedent_and_strip('''
            {module_docstring}
            
            import re
            
            # test data
            test_data = {test_data}
            
            # list of regex pattern
            patterns = [
                {patterns}
            ]
            
            def test_regex(test_data, patterns):
                """test regular expression
            
                Parameters
                ----------
                test_data (str): a test data
                patterns (list): a list of regular expression pattern
                """
            
                for pattern in patterns:
                    is_matched = False
                    for line in test_data.splitlines():
                        match = re.search(pattern, line)
                        if match:
                            is_matched = True
                            print("Pattern: {{}}".format(pattern))
                            if match.groupdict():
                                print("Result: {{}}".format(match.groupdict()))
                            else:
                                print("Result: {{}}".format(match.group()))
                            print("-" * 10)
                    else:
                        if not is_matched:
                            print("Result: No match")
            
            # function call
            test_regex(test_data, patterns)
        ''')

        lst = []
        for pattern in patterns:
            lst.append('r{}'.format(enclose_string(pattern)))
        patterns = indent(',\n'.join(lst), '    ').strip()
        test_script = tmpl.format(
            module_docstring=self.module_docstring,
            test_data=test_data, patterns=patterns
        )
        return test_script

    def create_multiline_via_pattern_script(self, test_data, pattern):
        """return python test script - multiline via pattern

        Parameters
        ----------
        test_data (str): a test data.
        pattern (str): a regex pattern.

        Returns
        -------
        str: a python test script
        """
        tmpl = dedent_and_strip('''
            {module_docstring}
            
            import re
            
            # test data
            test_data = {test_data}
            
            # regex pattern
            pattern = r{pattern}
            
            def test_regex(test_data, pattern):
                """test regular expression
            
                Parameters
                ----------
                test_data (str): a test data
                pattern (str): a regular expression pattern
                """
            
                print("Pattern: {{}}".format(pattern))
                match = re.search(pattern, test_data)
                if match:
                    if match.groupdict():
                        print("Result: {{}}".format(match.groupdict()))
                    else:
                        print("Result: {{}}".format(match.group()))
                else:
                    print("Result: No match")
            
            # function call
            test_regex(test_data, pattern)
        ''')
        test_script = tmpl.format(
            module_docstring=self.module_docstring,
            test_data=test_data, pattern=pattern
        )
        return test_script

    def create(self):
        """
        Assemble and return a Python test script snippet.

        This method generates a complete Python test script based on the
        current builder state (`self.tc_gen`). Depending on whether the
        builder is configured for line-based or multiline testing, it
        delegates to one of the specialized snippet creation methods:
        - `create_line_via_pattern_script` for a single regex pattern
          tested line-by-line.
        - `create_line_via_patterns_script` for multiple regex patterns
          tested line-by-line.
        - `create_multiline_via_pattern_script` for a single regex pattern
          tested against multiline input.

        Workflow
        --------
        1. Inspect `self.tc_gen.is_line` to determine line-based vs.
           multiline testing.
        2. Normalize `test_data`:
           - If provided as a list/tuple, join or select appropriate
             elements.
           - Otherwise, use the raw string.
        3. Select the appropriate snippet builder method based on the
           number of patterns and test mode.
        4. Return the generated Python script as a string.

        Returns
        -------
        str
            A dynamically generated Python test script, including:
            - The module-level docstring with metadata (author, email, company).
            - Regex pattern(s) and test data.
            - A test function that validates regex matches and prints results.

        Notes
        -----
        - Line-based mode (`is_line=True`) tests each line of input against
          one or more regex patterns.
        - Multiline mode (`is_line=False`) tests the entire input string
          against a single regex pattern.
        - The script is returned as text and can be saved to a file or
          executed directly with Python.
        - This method does not execute the test itself; it only produces
          the script text.
        """
        tc_gen = self.tc_gen
        if self.tc_gen.is_line:
            if isinstance(tc_gen.test_data, (list, tuple)):
                test_data = enclose_string('\n'.join(tc_gen.test_data))
            else:
                test_data = enclose_string(tc_gen.test_data)

            if len(tc_gen.patterns) == 1:
                pattern = enclose_string(tc_gen.patterns[0])
                test_script = self.create_line_via_pattern_script(
                    test_data, pattern
                )
            else:
                test_script = self.create_line_via_patterns_script(
                    test_data, tc_gen.patterns
                )
        else:
            if isinstance(tc_gen.test_data, (list, tuple)):
                test_data = enclose_string(tc_gen.test_data[0])
            else:
                test_data = enclose_string(tc_gen.test_data)

            pattern = enclose_string(tc_gen.patterns[0])
            test_script = self.create_multiline_via_pattern_script(
                test_data, pattern
            )

        return test_script
