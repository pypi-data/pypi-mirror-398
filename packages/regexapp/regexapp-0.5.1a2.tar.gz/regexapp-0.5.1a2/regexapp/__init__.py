"""
regexapp: Top-level package initializer.

This module exposes the primary classes, builders, and utilities
that form the core functionality of regexapp. It provides access
to pattern definitions, dynamic test script generation, and
reference management utilities. End-users can leverage these
exports to build, customize, and validate regex patterns across
different contexts.

Features
--------
- Pattern support:
  * `TextPattern`, `ElementPattern`, `LinePattern`, `MultilinePattern`
    for diverse regex construction needs.
  * `PatternBuilder` for assembling complex regex patterns.
  * `PatternReference` for accessing predefined system references
    from `system_references.yaml`.
- Customization:
  * End-users can override or extend predefined patterns by editing
    `~/.geekstrident/regexapp/user_references.yaml`.
- Test script generation:
  * Dynamically generate Python snippet scripts.
  * Dynamically generate Python unittest scripts.
  * Dynamically generate Python pytest scripts.
- Utilities:
  * `RegexBuilder` and `DynamicTestScriptBuilder` for constructing
    and validating regex-based test workflows.
  * `add_reference` and `remove_reference` for managing reference
    entries programmatically.

Metadata
--------
- `version` : str
    Current package version.
- `edition` : str
    Current package edition (e.g., Community).

Notes
-----
- System references are defined in `system_references.yaml` and
  shipped with the package.
- User references are stored in the home directory under
  `.geekstrident/regexapp/`.
- This module centralizes imports and metadata for convenience,
  making regexapp easier to use directly from the top-level package.
"""

from regexapp.collection import TextPattern
from regexapp.collection import ElementPattern
from regexapp.collection import LinePattern
from regexapp.collection import PatternBuilder
from regexapp.collection import MultilinePattern
from regexapp.collection import PatternReference
from regexapp.core import RegexBuilder
from regexapp.core import DynamicTestScriptBuilder
from regexapp.core import add_reference
from regexapp.core import remove_reference

from regexapp.config import version
from regexapp.config import edition
__version__ = version
__edition__ = edition

__all__ = [
    'TextPattern',
    'ElementPattern',
    'LinePattern',
    'MultilinePattern',
    'PatternBuilder',
    'PatternReference',
    'RegexBuilder',
    'DynamicTestScriptBuilder',
    'add_reference',
    'remove_reference',
    'version',
    'edition',
]
