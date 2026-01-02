"""'
regexapp.__main__
=================
Entry point module for regexapp.

This module provides the command-line interface (CLI) entry point
for regexapp. When executed as a script (e.g., via
``python -m regexapp``), it initializes the CLI application and
invokes its main runtime loop.

Features
--------
- Imports the `Cli` class from `regexapp.main`.
- Instantiates a `Cli` object (`console`).
- Executes the CLI by calling `console.run()`.

Usage
-----
Run regexapp directly from the command line:

    python -m regexapp

This will launch the CLI interface, allowing users to interact
with regexapp features such as pattern building, test script
generation, and reference management.

Notes
-----
- This module is intended to be executed, not imported.
- The CLI behavior is defined in `regexapp.main.Cli`.
- Provides a convenient way to access regexapp functionality
  without writing additional Python code.
"""

from regexapp.main import Cli

console = Cli()
console.run()
