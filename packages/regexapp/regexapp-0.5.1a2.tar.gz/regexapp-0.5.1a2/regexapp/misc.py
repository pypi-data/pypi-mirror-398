"""
regex.misc
==========

Miscellaneous helpers and utilities for the regexapp framework.

This module provides supporting functions and classes that do not fit
cleanly into other regexapp components but are useful for pattern
management, validation, and integration. It centralizes small, reusable
pieces of logic to reduce duplication and improve maintainability across
the project.
"""


import re
from argparse import ArgumentParser

from genericlib import DotObject


class MiscArgs:
    @classmethod
    def get_parsed_result_as_data_or_file(cls, *kwflags, data: str=''):
        """
        Parse input into either inline data or a file reference.

        This method uses `argparse` to interpret the first line of the
        provided `data` string. It distinguishes between file references
        (via flags such as `--file`, `--filename`, or `--file-name`) and
        inline data values. Additional custom flags can be passed through
        `kwflags`. The result is returned as a `DotObject` with attributes
        describing the parsing outcome.

        Parameters
        ----------
        *kwflags : list of flags
            Additional flag names to accept (e.g., `--config`, `--path`).
        data : str, default is empty string
            Input string to parse. Only the first line is inspected for
            flags. Defaults to an empty string.

        Returns
        -------
        DotObject
            A structured result with the following attributes:
            - `is_parsed` : bool
                Whether parsing succeeded.
            - `is_data` : bool
                True if the input was recognized as inline data.
            - `data` : str
                The parsed data content (if any).
            - `is_file` : bool
                True if the input was recognized as a file reference.
            - `filename` : str
                The parsed filename (if any).
            - `failure` : str
                Error message if parsing failed.

        Raises
        ------
        Exception
            Any exception raised during parsing is caught and stored in
            `failure`. The method itself does not propagate exceptions.

        Notes
        -----
        - File flags are matched case‑insensitively against the pattern
          `file`, `filename`, or `file-name`.
        - If neither data nor file input is found, `failure` is set to
          `"Invalid data"`.
        - The method inspects only the first line of `data` for flags.
        """
        parser = ArgumentParser(exit_on_error=False)
        parser.add_argument('val1', nargs='*')
        parser.add_argument('--file', type=str, default='')
        parser.add_argument('--filename', type=str, default='')
        parser.add_argument('--file-name', type=str, default='')
        for flag in kwflags:
            parser.add_argument(flag, type=str, default='')
        parser.add_argument('val2', nargs='*')

        data = str(data).strip()
        first_line = '\n'.join(data.splitlines()[:1])
        pattern = '(?i)file(_?name)?$'

        result = DotObject(
            is_parsed=False, is_data=False, data=data,
            is_file=False, filename='', failure=''
        )

        try:
            options = parser.parse_args(re.split(r' +', first_line))
            result.is_parsed = True
            for flag, val in vars(options).items():
                if re.match(pattern, flag) and val.strip():
                    result.is_file = True
                    result.filename = val.strip()
                else:
                    if flag != 'val1' or flag != 'val2':
                        if val.strip():
                            result.is_data = True
                            result.data = val.strip()
                            return result

            if result.val1 or result.val2:
                result.is_data = True
                return result
            else:
                result.is_parsed = False
                result.failure = 'Invalid data'
                return result

        except Exception as ex:
            result.failure = f'{type(ex).__name__}: {ex}'
            result.is_parsed = False
            return result
