"""
regexapp.application
====================

Main application module for the `regexapp` library.

This module implements the core logic and graphical user interface (GUI)
components for `regexapp`. It leverages the `tkinter` framework to provide
an interactive environment for building, customizing, and testing regular
expression patterns. Users can launch the GUI to access regex generation
tools, reference management, and dynamic test script creation.

Features
--------
- Integrates with `tkinter` to deliver a graphical interface.
- Provides the primary entry point for launching the regexapp GUI.
- Supports pattern generation, customization, and testing workflows.

Notes
-----
- If `tkinter` is not available, the module prints a descriptive error
  message and terminates execution gracefully.
- This module is intended to be executed as the main entry point for
  GUI
"""

try:
    import tkinter as tk
except ModuleNotFoundError:
    import sys
    from platform import python_version as py_version
    from genericlib.misc import sys_exit

    items = [
        "RegexBuilder application failed to start.",
        f"Python {py_version()} was detected without the tkinter module.",
        "Install tkinter to enable GUI support and retry."
    ]

    # Determine the maximum item length
    max_len = max(len(item) for item in items)
    # Build the horizontal border
    border = f"+-{'-' * max_len}-+"
    # Build the table rows
    rows = [f"| {item.ljust(max_len)} |" for item in items]
    # Combine everything into the final framed text
    txt = "\n".join([border] + rows + [border])
    sys_exit(success=False, msg=txt)
except Exception as exc:
    raise exc

from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.font import Font
from pathlib import Path
import webbrowser
from regexapp import RegexBuilder
from regexapp.collection import REF
from regexapp.collection import PatternReference
from regexapp import version
from regexapp import edition
from regexapp.core import enclose_string
from regexapp import PatternBuilder

from regexapp.config import Data

import regexapp.ui as ui
import regexapp.utils as utils

from genericlib import DotObject
from genericlib.text import dedent_and_strip

import yaml
import re
import platform

__version__ = version
__edition__ = edition


def get_relative_center_location(parent, width, height):
    """
    Calculate the coordinates to center a child window relative to its parent.

    This function determines the (x, y) position for placing a child
    window so that it is centered within the bounds of the given
    parent window.

    Parameters
    ----------
    parent : tkinter.Tk or tkinter.Toplevel
        The parent window instance whose geometry is used as reference.
    width : int
        The width of the child window.
    height : int
        The height of the child window.

    Returns
    -------
    tuple of int
        A tuple ``(x, y)`` representing the top-left coordinates at
        which the child window should be placed to appear centered
        within the parent window.

    Notes
    -----
    - The calculation uses the parent's geometry string (width x height + x + y).
    - Coordinates are returned as integers suitable for use with
      ``geometry()`` in tkinter.
    """
    pwh, px, py = parent.winfo_geometry().split('+')
    px, py = int(px), int(py)
    pw, ph = [int(i) for i in pwh.split('x')]

    x = int(px + (pw - width) / 2)
    y = int(py + (ph - height) / 2)
    return x, y


def create_msgbox(title=None, error=None, warning=None, info=None,
                  question=None, okcancel=None, retrycancel=None,
                  yesno=None, yesnocancel=None, **options):
    """
    Display a tkinter messagebox with the specified type and message.

    This function provides a unified interface for creating different
    types of message boxes (error, warning, info, question, and various
    confirmation dialogs). Only one type of message should be specified
    per call. The function delegates to the appropriate `tkinter.messagebox`
    function based on the provided keyword argument.

    Parameters
    ----------
    title : str, optional
        The title of the messagebox window. Default is None.
    error : str, optional
        An error message. Displays an error dialog. Default is None.
    warning : str, optional
        A warning message. Displays a warning dialog. Default is None.
    info : str, optional
        An informational message. Displays an info dialog. Default is None.
    question : str, optional
        A question prompt. Displays a yes/no dialog returning a string. Default is None.
    okcancel : str, optional
        A message for an OK/Cancel dialog. Returns a boolean. Default is None.
    retrycancel : str, optional
        A message for a Retry/Cancel dialog. Returns a boolean. Default is None.
    yesno : str, optional
        A message for a Yes/No dialog. Returns a boolean. Default is None.
    yesnocancel : str, optional
        A message for a Yes/No/Cancel dialog. Returns a boolean or None. Default is None.
    **options : dict
        Additional keyword arguments passed to the underlying tkinter
        messagebox function (e.g., `icon`, `default`).

    Returns
    -------
    str or bool or None
        The result of the messagebox interaction:
        - "ok" for error, warning, or info dialogs.
        - "yes"/"no" string for question dialogs.
        - Boolean for okcancel, retrycancel, yesno dialogs.
        - Boolean or None for yesnocancel dialogs.

    Notes
    -----
    - Only one message type should be provided per call. If multiple
      are specified, the first matching type in the order of evaluation
      (error → warning → info → question → okcancel → retrycancel → yesno → yesnocancel)
      will be used.
    - If no type is specified, an info dialog is shown by default.
    """
    if error:
        # a return result is an "ok" string
        result = messagebox.showerror(title=title, message=error, **options)
    elif warning:
        # a return result is an "ok" string
        result = messagebox.showwarning(title=title, message=warning, **options)
    elif info:
        # a return result is an "ok" string
        result = messagebox.showinfo(title=title, message=info, **options)
    elif question:
        # a return result is a "yes" or "no" string
        result = messagebox.askquestion(title=title, message=question,
                                        **options)
    elif okcancel:
        # a return result is boolean
        result = messagebox.askokcancel(title=title, message=okcancel,
                                        **options)
    elif retrycancel:
        # a return result is boolean
        result = messagebox.askretrycancel(title=title, message=retrycancel,
                                           **options)
    elif yesno:
        # a return result is boolean
        result = messagebox.askyesno(title=title, message=yesno, **options)
    elif yesnocancel:
        # a return result is boolean or None
        result = messagebox.askyesnocancel(title=title, message=yesnocancel,
                                           **options)
    else:
        # a return result is an "ok" string
        result = messagebox.showinfo(title=title, message=info, **options)

    return result


def set_modal_dialog(dialog):
    """
    Configure a tkinter dialog window to behave as a modal dialog.

    A modal dialog prevents interaction with other windows in the
    application until the dialog is closed. This function sets the
    dialog as transient to its parent, ensures it is visible, and
    grabs focus so that user input is restricted to the dialog.

    Parameters
    ----------
    dialog : tkinter.Toplevel or tkinter.Tk
        The dialog or window instance to configure as modal.

    Notes
    -----
    - `transient()` ties the dialog to its parent window.
    - `wait_visibility()` ensures the dialog is displayed before
      grabbing focus.
    - `grab_set()` restricts user input to the dialog only.
    - `wait_window()` blocks execution until the dialog is closed.
    """
    dialog.transient(dialog.master)
    dialog.wait_visibility()
    dialog.grab_set()
    dialog.wait_window()


class Application:
    """
    Main GUI class for the `regexapp` library.

    The `Application` class provides a graphical interface for building,
    customizing, and testing regular expressions. It integrates with
    `tkinter` and `ttk` to deliver a structured layout with frames,
    buttons, text areas, and interactive widgets. Users can manage
    regex patterns, generate test scripts, and view results directly
    within the GUI.

    Attributes
    ----------
    root : tkinter.Tk
        The root tkinter application window.
    panedwindow : ttk.Panedwindow
        Main layout container for organizing frames.
    text_frame : ttk.Frame
        Frame containing the test data widget.
    entry_frame : ttk.Frame
        Frame containing action buttons (open, paste, build, snippet,
        unittest, pytest, etc.).
    result_frame : ttk.Frame
        Frame containing the test result widget.
    var_name_frame : ttk.Frame
        Frame containing the variable name textbox.
    word_bound_frame : ttk.Frame
        Frame containing the word boundary combobox.
    save_as_btn : ttk.Button
        Button for saving output to a file.
    copy_text_btn : ttk.Button
        Button for copying text to the clipboard.

    snapshot : DictObject
        Stores application state for switching contexts.

    radio_line_or_multiline_btn_var : tk.StringVar
        Radio button variable; defaults to "multiline".
    builder_checkbox_var : tk.BooleanVar
        Checkbox variable for enabling the builder.
    var_name_var : tk.StringVar
        Variable bound to the var_name textbox.
    word_bound_var : tk.StringVar
        Variable bound to the word_bound combobox.
    is_confirmed : bool
        Flag to show confirmation dialogs. Defaults to True.

    prepended_ws_var : tk.BooleanVar
        Checkbox variable for prepended whitespace. Defaults to False.
    appended_ws_var : tk.BooleanVar
        Checkbox variable for appended whitespace. Defaults to False.
    ignore_case_var : tk.BooleanVar
        Checkbox variable for case-insensitive matching. Defaults to False.
    test_name_var : tk.StringVar
        Variable bound to the test name textbox. Defaults to empty string.
    test_cls_name_var : tk.StringVar
        Variable bound to the test class name textbox.
        Defaults to "TestDynamicGenTestScript".
    max_words_var : tk.IntVar
        Variable bound to the max words textbox. Defaults to 6.
    filename_var : tk.StringVar
        Variable bound to the filename textbox. Defaults to empty string.
    author_var : tk.StringVar
        Variable bound to the author textbox. Defaults to empty string.
    email_var : tk.StringVar
        Variable bound to the email textbox. Defaults to empty string.
    company_var : tk.StringVar
        Variable bound to the company textbox. Defaults to empty string.
    new_pattern_name_var : tk.StringVar
        Variable for creating new pattern references. Defaults to empty string.

    input_textarea : tk.Text
        TextArea widget for entering test data.
    result_textarea : tk.Text
        TextArea widget for displaying test results.
    line_radio_btn : tk.Radiobutton
        Radio button for enabling `LinePattern`.
    multiline_radio_btn : tk.Radiobutton
        Radio button for enabling `MultilinePattern`.

    Methods
    -------
    is_pattern_builder_app() -> bool
        Check if the application is in pattern builder mode.
    shift_to_pattern_builder_app() -> None
        Switch the interface to pattern builder mode.
    shift_to_regex_builder_app() -> None
        Switch the interface to regex builder mode.
    get_builder_args() -> dict
        Retrieve arguments for regex builder configuration.
    get_pattern_builder_args() -> dict
        Retrieve arguments for pattern builder configuration.
    set_default_setting() -> None
        Reset application settings to defaults.
    get_textarea(node) -> str
        Get text content from a specified textarea widget.
    set_textarea(node, data, title='') -> None
        Set text content in a specified textarea widget.
    set_title(widget=None, title='') -> None
        Update the window or widget title.
    callback_file_open() -> None
        Handle file open action.
    callback_help_documentation() -> None
        Display help documentation.
    callback_help_view_licenses() -> None
        Display license information.
    callback_help_about() -> None
        Display application "About" dialog.
    callback_preferences_settings() -> None
        Open preferences/settings dialog.
    callback_preferences_system_reference() -> None
        Open system reference configuration.
    callback_preferences_user_reference() -> None
        Open user reference configuration.
    build_menu() -> None
        Construct the application menu bar.
    build_frame() -> None
        Build the main application frames.
    build_textarea() -> None
        Initialize text area widgets.
    build_entry() -> None
        Initialize entry widgets and action buttons.
    build_result() -> None
        Initialize result display widgets.
    run() -> None
        Start the main application loop.
    """

    browser = webbrowser

    def __init__(self):
        # support platform: macOS, Linux, and Window
        self.is_macos = platform.system() == 'Darwin'
        self.is_linux = platform.system() == 'Linux'
        self.is_window = platform.system() == 'Windows'

        # standardize tkinter widget for macOS, Linux, and Window operating system
        self.RadioButton = tk.Radiobutton if self.is_linux else ttk.Radiobutton
        self.CheckBox = tk.Checkbutton if self.is_linux else ttk.Checkbutton
        self.Label = ttk.Label
        self.Frame = ttk.Frame
        self.LabelFrame = ttk.LabelFrame
        self.Button = ttk.Button
        self.TextBox = ttk.Entry
        self.TextArea = tk.Text
        self.PanedWindow = ttk.PanedWindow

        # tkinter root
        self._base_title = 'Regex {}'.format(edition)
        self.root = tk.Tk()
        self.root.geometry('1000x600+100+100')
        self.root.minsize(200, 200)
        self.root.option_add('*tearOff', False)

        # tkinter widgets for main layout
        self.panedwindow = None
        self.text_frame = None
        self.entry_frame = None
        self.result_frame = None

        self.input_textarea = None
        self.result_textarea = None
        self.line_radio_btn = None
        self.multiline_radio_btn = None

        self.save_as_btn = None
        self.copy_text_btn = None
        self.snippet_btn = None
        self.unittest_btn = None
        self.pytest_btn = None
        self.test_data_btn = None

        # tkinter widgets for builder app
        self.var_name_frame = None
        self.word_bound_frame = None

        # datastore
        self.snapshot = DotObject(test_data=None, test_result='')

        # variables
        # variables: radio button
        self.radio_line_or_multiline_btn_var = tk.StringVar()
        self.radio_line_or_multiline_btn_var.set('multiline')

        self.test_data_btn_var = tk.StringVar()
        self.test_data_btn_var.set('Test Data')

        # variables: for builder app
        self.builder_checkbox_var = tk.BooleanVar()
        self.var_name_var = tk.StringVar()
        self.word_bound_var = tk.StringVar()
        self.word_bound_var.set('none')
        self.is_confirmed = True

        # variables: pattern arguments
        self.prepended_ws_var = tk.BooleanVar()
        self.appended_ws_var = tk.BooleanVar()
        self.ignore_case_var = tk.BooleanVar()

        # variables: builder arguments
        self.test_name_var = tk.StringVar()
        self.test_cls_name_var = tk.StringVar()
        self.test_cls_name_var.set('TestDynamicGenTestScript')
        self.max_words_var = tk.IntVar()
        self.max_words_var.set(6)
        self.filename_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.company_var = tk.StringVar()

        # variables: preferences > user reference
        self.new_pattern_name_var = tk.StringVar()

        # method call
        self.set_title()
        self.build_menu()
        self.build_frame()
        self.build_textarea()
        self.build_entry()
        self.build_result()

    @property
    def is_pattern_builder_app(self):
        """
        Check whether the application is in pattern builder mode.

        This property evaluates the state of the builder checkbox variable
        (`builder_checkbox_var`). If the checkbox is selected, the application
        is considered to be running in pattern builder mode.

        Returns
        -------
        bool
            True if the builder checkbox is enabled (pattern builder mode),
            False otherwise.
        """
        return self.builder_checkbox_var.get() is True

    def shift_to_pattern_builder_app(self):
        """
        Switch the application interface from Regex Builder mode to Pattern Builder mode.

        This method handles the transition between the Regex Builder App and the
        Pattern Builder App. If confirmation is enabled (`is_confirmed`), a dialog
        box is displayed to prompt the user with options ("Yes", "No", "Cancel").
        Depending on the user's choice, the application state is updated and the
        interface is reconfigured accordingly.

        Workflow
        --------
        1. Prompt the user with a confirmation dialog if `is_confirmed` is True.
           - "Yes": Switch to Pattern Builder App and continue showing confirmation.
           - "No": Switch to Pattern Builder App without showing confirmation again.
           - "Cancel": Abort the switch.
        2. Save current Regex Builder data and results into the `snapshot`.
        3. Restore any previously saved Pattern Builder data and results.
        4. Update the GUI layout:
           - Remove Regex Builder-specific widgets (radio buttons, snippet/unittest/pytest buttons).
           - Display Pattern Builder-specific frames (variable name and word boundary).

        Notes
        -----
        - The `snapshot` dictionary is used to persist and restore application state
          between builder modes.
        - Confirmation behavior is controlled by the `is_confirmed` flag and updated
          based on user input.
        - This method modifies the GUI layout dynamically using `grid_remove` and `grid`.

        Returns
        -------
        None
            This method performs side effects (state updates and GUI changes) but
            does not return a value.
        """

        if self.is_confirmed:
            title = 'Switching To Pattern Builder App'
            yesnocancel = """
                You are about to leave the Regex Builder App.
    
                - Yes: Switch to the other app and show a confirmation.
                - No: Switch to the other app without showing a confirmation.
                - Cancel: Stay in the current app.
    
                Do you want to switch?
            """

            yesnocancel = dedent_and_strip(yesnocancel)
            result = create_msgbox(title=title, yesnocancel=yesnocancel)
            if result is None:
                self.builder_checkbox_var.set(not self.builder_checkbox_var.get())
            else:
                self.is_confirmed = result
        else:
            result = self.is_confirmed

        if result is not None:
            data = self.get_textarea(self.input_textarea)
            result = self.get_textarea(self.result_textarea)
            self.snapshot.update(
                regex_builder_app_data=data,
                regex_builder_app_result=result
            )
            data = self.snapshot.get('pattern_builder_app_data', '')
            result = self.snapshot.get('pattern_builder_app_result', '')

            self.set_textarea(self.input_textarea, data)
            self.set_textarea(self.result_textarea, result)

            self.line_radio_btn.grid_remove()
            self.multiline_radio_btn.grid_remove()
            self.snippet_btn.grid_remove()
            self.unittest_btn.grid_remove()
            self.pytest_btn.grid_remove()
            self.test_data_btn.grid_remove()
            self.var_name_frame.grid(row=0, column=13)
            self.word_bound_frame.grid(row=0, column=14)

    def shift_to_regex_builder_app(self):
        """
        Switch the application interface from Pattern Builder mode to Regex Builder mode.

        This method manages the transition back to the Regex Builder App. If confirmation
        is enabled (`is_confirmed`), a dialog box prompts the user with options ("Yes",
        "No", "Cancel"). Based on the user's choice, the application state is updated
        and the GUI layout is reconfigured to display Regex Builder-specific widgets.

        Workflow
        --------
        1. Prompt the user with a confirmation dialog if `is_confirmed` is True.
           - "Yes": Switch to Regex Builder App and continue showing confirmation.
           - "No": Switch to Regex Builder App without showing confirmation again.
           - "Cancel": Abort the switch.
        2. Save current Pattern Builder data and results into the `snapshot`.
        3. Restore any previously saved Regex Builder data and results.
        4. Update the GUI layout:
           - Display Regex Builder-specific widgets (radio buttons, snippet/unittest/pytest buttons).
           - Remove Pattern Builder-specific frames (variable name and word boundary).

        Notes
        -----
        - The `snapshot` dictionary is used to persist and restore application state
          between builder modes.
        - Confirmation behavior is controlled by the `is_confirmed` flag and updated
          based on user input.
        - This method modifies the GUI layout dynamically using `grid` and `grid_remove`.

        Returns
        -------
        None
            This method performs side effects (state updates and GUI changes) but
            does not return a value.
        """
        if self.is_confirmed:
            title = 'Switching To Regex Builder App'
            yesnocancel = """
                You are about to leave the Pattern Builder App.
    
                - Yes: Switch to the Regex Builder App and show a confirmation.
                - No: Switch to the Regex Builder App without showing a confirmation.
                - Cancel: Stay in the Pattern Builder App.
    
                Do you want to switch?
            """

            yesnocancel = dedent_and_strip(yesnocancel)
            result = create_msgbox(title=title, yesnocancel=yesnocancel)
            if result is None:
                self.builder_checkbox_var.set(not self.builder_checkbox_var.get())
            else:
                self.is_confirmed = result
        else:
            result = self.is_confirmed

        if result is not None:
            data = self.get_textarea(self.input_textarea)
            result = self.get_textarea(self.result_textarea)
            self.snapshot.update(
                pattern_builder_app_data=data,
                pattern_builder_app_result=result
            )
            data = self.snapshot.get('regex_builder_app_data', '')
            result = self.snapshot.get('regex_builder_app_result', '')

            self.set_textarea(self.input_textarea, data)
            self.set_textarea(self.result_textarea, result)

            self.line_radio_btn.grid(row=0, column=0, padx=(4, 0))
            self.multiline_radio_btn.grid(row=0, column=1, padx=2)
            self.snippet_btn.grid(row=0, column=8, pady=2)
            self.unittest_btn.grid(row=0, column=9, pady=2)
            self.pytest_btn.grid(row=0, column=10, pady=2)
            self.test_data_btn.grid(row=0, column=11, pady=2)
            self.var_name_frame.grid_remove()
            self.word_bound_frame.grid_remove()

    def get_regex_builder_args(self):
        """
        Collect and return configuration arguments for initializing a `RegexBuilder` instance.

        This method gathers values from the application's GUI variables and
        returns them as a dictionary. The resulting dictionary can be passed
        directly to the `RegexBuilder` class to configure regex generation
        and test script creation.

        Returns
        -------
        dict
            A dictionary of configuration arguments with the following keys:

            - ignore_case (bool): Whether to enable case-insensitive matching.
            - prepended_ws (bool): Whether to prepend a whitespace to the pattern.
            - appended_ws (bool): Whether to append a whitespace to the pattern.
            - is_line (bool): True if line-based matching is selected, False for multiline.
            - test_name (str): Name of the test case. Defaults to empty string.
            - test_cls_name (str): Name of the test class. Defaults to "TestDynamicGenTestScript".
            - max_words (int): Maximum number of words for generating test names. Defaults to 6.
            - filename (str): Output filename for saving generated test scripts.
            - author (str): Author name. Defaults to empty string.
            - email (str): Author email. Defaults to empty string.
            - company (str): Company name. Defaults to empty string.
        """
        result = dict(
            ignore_case=self.ignore_case_var.get(),
            prepended_ws=self.prepended_ws_var.get(),
            appended_ws=self.appended_ws_var.get(),
            is_line=self.radio_line_or_multiline_btn_var.get() == 'line',
            test_name=self.test_name_var.get(),
            test_cls_name=self.test_cls_name_var.get(),
            max_words=self.max_words_var.get(),
            filename=self.filename_var.get(),
            author=self.author_var.get(),
            email=self.email_var.get(),
            company=self.company_var.get()
        )
        return result

    def get_pattern_builder_args(self):
        """
        Collect and return configuration arguments for initializing a `PatternBuilder` instance.

        This method gathers values from the application's GUI variables and
        returns them as a dictionary. The resulting dictionary can be passed
        directly to the `PatternBuilder` class to configure pattern generation
        and testing.

        Returns
        -------
        dict
            A dictionary of configuration arguments with the following keys:

            - var_name (str): The variable name associated with the pattern.
            - word_bound (str): Word boundary option derived from the selected
              combobox value. Possible values include:
                * '' (none): No word boundary applied.
                * 'word_bound': Apply word boundary on both sides.
                * 'word_bound_left': Apply word boundary on the left side only.
                * 'word_bound_right': Apply word boundary on the right side only.
        """
        table = dict(none='', both='word_bound',
                     left='word_bound_left', right='word_bound_right')
        result = dict(
            var_name=self.var_name_var.get(),
            word_bound=table.get(self.word_bound_var.get(), '')
        )
        return result

    def set_default_setting(self):
        """
        Reset application configuration variables to their default values.

        This method restores the state of all regex-related configuration
        variables to their initial defaults. It ensures a consistent baseline
        when starting a new session or clearing previous settings.

        Notes
        -----
        - Whitespace options (`prepended_ws_var`, `appended_ws_var`) are reset to False.
        - Case sensitivity (`ignore_case_var`) is reset to False.
        - Test metadata is reset:
            * `test_name_var`: empty string
            * `test_cls_name_var`: "TestDynamicGenTestScript"
            * `max_words_var`: 6
            * `filename_var`: empty string
            * `author_var`: empty string
            * `email_var`: empty string
            * `company_var`: empty string

        Returns
        -------
        None
            This method performs side effects (variable resets) but does not return a value.
        """

        self.prepended_ws_var.set(False)
        self.appended_ws_var.set(False)
        self.ignore_case_var.set(False)
        self.test_name_var.set('')
        self.test_cls_name_var.set('TestDynamicGenTestScript')
        self.max_words_var.set(6)
        self.filename_var.set('')
        self.author_var.set('')
        self.email_var.set('')
        self.company_var.set('')

    @classmethod
    def get_textarea(cls, node):
        """
        Retrieve and normalize text content from a `tk.Text` widget.

        This method extracts the full text from a `tk.Text` widget starting
        at position `'1.0'` through `'end'`. It trims trailing newline or
        carriage return characters to ensure the returned string is clean
        and consistent across platforms.

        Parameters
        ----------
        node : tk.Text
            A tkinter `Text` widget from which to retrieve content.

        Returns
        -------
        str
            The normalized text string from the widget, with trailing
            newline (`\\n`), carriage return (`\\r`), or Windows-style
            line ending (`\\r\\n`) removed if present.

        Notes
        -----
        - This method ensures cross-platform consistency by stripping
          trailing line endings that tkinter may append automatically.
        - The returned string preserves all other content exactly as entered.
        """
        text = node.get('1.0', 'end')
        last_char = text[-1]
        last_two_chars = text[-2:]
        if last_char == '\r' or last_char == '\n':
            return text[:-1]
        elif last_two_chars == '\r\n':
            return text[:-2]
        else:
            return text

    def set_textarea(self, node, data, title=''):
        """
        Set text content in a `tk.Text` widget and optionally update the window title.

        This method replaces the existing content of a `tk.Text` widget with
        the provided data. If a non-empty title is supplied, it also updates
        the application window title.

        Parameters
        ----------
        node : tk.Text
            A tkinter `Text` widget where the content will be inserted.
        data : any
            The data to insert into the widget. Converted to a string before insertion.
        title : str, optional
            The title to set for the application window. Defaults to an empty string.
            If empty, the window title is not modified.

        Returns
        -------
        None
            This method performs side effects (widget updates and optional title change)
            but does not return a value.

        Notes
        -----
        - Existing content in the `Text` widget is cleared before inserting new data.
        - Both `data` and `title` are coerced to strings to ensure consistent behavior.
        """
        data, title = str(data), str(title).strip()

        title and self.set_title(title=title)
        node.delete("1.0", "end")
        node.insert(tk.INSERT, data)

    def set_title(self, widget=None, title=''):
        """
        Update the title of a tkinter widget window.

        This method sets a new title for the specified tkinter widget. If no
        widget is provided, the root application window (`self.root`) is used.
        The title is combined with the application's base title (`_base_title`)
        to ensure consistent branding across all windows.

        Parameters
        ----------
        widget : tkinter.Tk or tkinter.Toplevel, optional
            The tkinter widget whose title should be updated. Defaults to the
            root window if not provided.
        title : str, optional
            The custom title to prepend. Defaults to an empty string. If empty,
            only the base title is used.

        Returns
        -------
        None
            This method performs a side effect (updating the widget title) but
            does not return a value.

        Notes
        -----
        - If a non-empty `title` is provided, the final window title is formatted
          as: "<title> - <base_title>".
        - If `title` is empty, only `<base_title>` is applied.
        """
        widget = widget or self.root
        base_title = self._base_title
        title = f'{title} - {base_title}' if title else base_title
        widget.title(title)

    def create_custom_label(self, parent, text='', link='',
                            increased_size=0, bold=False, underline=False,
                            italic=False):
        """
        Create a customized tkinter `Label` widget.

        This method generates a `Label` widget with configurable text, font
        styling, and optional hyperlink behavior. It allows dynamic control
        over font size, weight, underline, and italic styles, making it useful
        for building visually distinct labels in the GUI.

        Parameters
        ----------
        parent : tkinter.Widget
            The parent widget that will contain the label.
        text : str, optional
            The text to display in the label. Defaults to an empty string.
        link : str, optional
            A hyperlink associated with the label. Defaults to an empty string.
            If provided, the label may be styled or bound to open the link.
        increased_size : int, optional
            Amount to increase the base font size. Defaults to 0 (no change).
        bold : bool, optional
            If True, the label text is rendered in bold. Defaults to False.
        underline : bool, optional
            If True, the label text is underlined. Defaults to False.
        italic : bool, optional
            If True, the label text is italicized. Defaults to False.

        Returns
        -------
        tkinter.Label
            A fully configured `Label` widget ready to be packed or gridded
            into the parent container.

        Notes
        -----
        - Font styling is applied by combining the provided options (`bold`,
          `underline`, `italic`, `increased_size`).
        - If `link` is provided, additional event bindings may be required
          to enable hyperlink functionality.
        """

        # Start of logic for the mouse_over inner function.
        def mouse_over(event):
            """
            Handle mouse-over event for a custom label.

            This inner function is bound to the `<Enter>` event of a label created
            by `Application.create_custom_label`. It defines the behavior when the
            mouse pointer hovers over the label, typically used to provide visual
            feedback (e.g., changing cursor style, highlighting text, or preparing
            hyperlink interaction).

            Parameters
            ----------
            event : tkinter.Event
                The event object containing metadata about the mouse-over action,
                including the widget reference and pointer coordinates.

            Returns
            -------
            None
                This function performs side effects (UI updates or event handling)
                but does not return a value.

            Notes
            -----
            - Common use cases include changing the label appearance or cursor
              when a hyperlink (`link`) is associated with the label.
            - As an inner function, it has access to the enclosing scope of
              `create_custom_label`, allowing it to reference label-specific
              attributes or configuration.
            """
            if 'underline' not in event.widget.font:
                event.widget.configure(
                    font=event.widget.font + ['underline'],
                    cursor='hand2'
                )

        # Completion of the mouse_over inner function logic.

        # Start of logic for the mouse_out inner function.
        def mouse_out(event):
            """
            Handle mouse-leave event for a custom label.

            This inner function is bound to the `<Leave>` event of a label created
            by `Application.create_custom_label`. It defines the behavior when the
            mouse pointer exits the label area, typically used to revert any visual
            feedback applied during the mouse-over event (e.g., restoring cursor
            style, removing highlight, or resetting hyperlink appearance).

            Parameters
            ----------
            event : tkinter.Event
                The event object containing metadata about the mouse-leave action,
                including the widget reference and pointer coordinates.

            Returns
            -------
            None
                This function performs side effects (UI updates or event handling)
                but does not return a value.

            Notes
            -----
            - Common use cases include restoring the label’s default appearance
              after hover effects are applied in `mouse_over`.
            - As an inner function, it has access to the enclosing scope of
              `create_custom_label`, allowing it to reference label-specific
              attributes or configuration.
            """
            event.widget.config(
                font=event.widget.font,
                cursor='arrow'
            )

        # Completion of the mouse_out inner function logic.

        # Start of logic for the mouse_press inner function.
        def mouse_press(event):
            """
            Handle mouse-click event for a custom label.

            This inner function is bound to the `<Button-1>` event of a label created
            by `Application.create_custom_label`. It defines the behavior when the
            label is clicked, typically used to trigger hyperlink navigation or
            execute a custom action associated with the label.

            Parameters
            ----------
            event : tkinter.Event
                The event object containing metadata about the mouse-click action,
                including the widget reference and pointer coordinates.

            Returns
            -------
            None
                This function performs side effects (e.g., opening a link or updating
                the UI) but does not return a value.

            Notes
            -----
            - If the label was created with a `link` argument, this handler may
              open the associated URL in a web browser.
            - As an inner function, it has access to the enclosing scope of
              `create_custom_label`, allowing it to reference label-specific
              attributes or configuration.
            """
            self.browser.open_new_tab(event.widget.link)

        # Completion of the mouse_press inner function logic.

        style = ttk.Style()
        style.configure("Blue.TLabel", foreground="blue")
        if link:
            label = self.Label(parent, text=text, style='Blue.TLabel')
            label.bind('<Enter>', mouse_over)
            label.bind('<Leave>', mouse_out)
            label.bind('<Button-1>', mouse_press)
        else:
            label = self.Label(parent, text=text)
        font = Font(name='TkDefaultFont', exists=True, root=label)
        font = [font.cget('family'), font.cget('size') + increased_size]
        bold and font.append('bold')
        underline and font.append('underline')
        italic and font.append('italic')
        label.configure(font=font)
        label.font = font
        label.link = link
        return label

    def callback_file_open(self):
        """
        Handle the "File > Open" menu action.

        This callback opens a file selection dialog, reads the chosen file,
        and loads its content into the application. If the application is in
        Regex Builder mode, the loaded content is stored as test data and the
        result area is cleared. The input text area is updated with the file
        content, and the window title is set to the filename.

        Workflow
        --------
        1. Display a file dialog restricted to text files (`.txt`) or all files.
        2. If a file is selected:
           - Read its content using UTF-8 encoding.
           - In Regex Builder mode:
             * Enable the "Test Data" button.
             * Reset the result textarea.
             * Save the content into the snapshot under `test_data`.
           - Update the input textarea with the file content.
           - Update the window title to the filename.

        Returns
        -------
        None
            This method performs side effects (file I/O, widget updates, and
            snapshot state changes) but does not return a value.

        Notes
        -----
        - The file dialog uses `tkinter.filedialog.askopenfilename`.
        - Only `.txt` files are explicitly listed, but all files can be opened.
        - Content is always read with UTF-8 encoding for consistency.
        """

        filetypes = [
            ('Text Files', '.txt', 'TEXT'),
            ('All Files', '*'),
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            content = utils.File.read(filename)
            if not self.is_pattern_builder_app:
                self.test_data_btn.config(state=tk.NORMAL)
                self.test_data_btn_var.set('Test Data')
                self.set_textarea(self.result_textarea, '')
                self.snapshot.update(test_data=content)
            self.set_textarea(self.input_textarea, content, title=filename)

    def callback_help_documentation(self):
        """
        Handle the "Help > Getting Started" menu action.

        This callback opens the application's official documentation in a new
        browser tab. It provides users with quick access to the "Getting Started"
        guide or reference materials hosted at the URL defined in
        `Data.documentation_url`.

        Workflow
        --------
        1. Retrieve the documentation URL from `Data.documentation_url`.
        2. Open the URL in a new browser tab using the application's
           `self.browser` instance.

        Returns
        -------
        None
            This method performs a side effect (launching documentation in a
            browser) but does not return a value.

        Notes
        -----
        - Relies on `self.browser.open_new_tab` for launching the documentation.
        - The documentation URL is centralized in the `Data` class for
          maintainability.
        """
        self.browser.open_new_tab(Data.documentation_url)

    def callback_help_view_licenses(self):
        """
        Handle the "Help > View Licenses" menu action.

        This callback opens the application's license information in a new
        browser tab. It provides users with direct access to the license text
        and related legal details hosted at the URL defined in
        `Data.license_url`.

        Workflow
        --------
        1. Retrieve the license URL from `Data.license_url`.
        2. Open the URL in a new browser tab using the application's
           `self.browser` instance.

        Returns
        -------
        None
            This method performs a side effect (launching the license page in
            a browser) but does not return a value.

        Notes
        -----
        - Relies on `self.browser.open_new_tab` for launching the license page.
        - The license URL is centralized in the `Data` class for maintainability.
        """
        self.browser.open_new_tab(Data.license_url)

    def callback_help_about(self):
        """
        Handle the "Help > About" menu action.

        This callback displays the application's "About" information, typically
        including the application name, version, author details, and other
        metadata. It provides users with a quick reference to the identity and
        background of the software.

        Workflow
        --------
        1. Triggered when the user selects "Help > About" from the menu.
        2. Opens an "About" dialog or page containing application details.

        Returns
        -------
        None
            This method performs a side effect (displaying an About dialog) but
            does not return a value.

        Notes
        -----
        - The exact content of the "About" dialog may include application
          metadata such as version, author, license, and company information.
        - Implementation relies on the GUI framework (`tkinter` or a browser
          instance) to render the dialog or page.
        """

        about = ui.create(tk.Toplevel, parent=self.root)
        self.set_title(widget=about, title='About')
        width, height = 460, 460
        x, y = get_relative_center_location(self.root, width, height)
        about.geometry(f'{width}x{height}+{x}+{y}')
        about.resizable(False, False)

        top_frame = ui.create(self.Frame, parent=about)
        ui.pack(top_frame, fill=tk.BOTH, expand=True)

        paned_window = ui.create(self.PanedWindow, parent=top_frame, orient=tk.VERTICAL)
        ui.pack(paned_window, fill=tk.BOTH, expand=True, padx=8, pady=12)

        # company
        frame = ui.create(self.Frame, parent=paned_window, width=450, height=20)
        paned_window.add(frame, weight=4)

        label = self.create_custom_label(
            frame, text=Data.main_app_text, increased_size=2, bold=True
        )
        ui.grid(label, row=0, column=0, columnspan=2, sticky=tk.W)

        # URL
        cell_frame = ui.create(self.Frame, parent=frame, width=450, height=5)
        ui.grid(cell_frame, row=1, column=0, sticky=tk.W, columnspan=2)

        url = Data.repo_url
        label = ui.create(self.Label, parent=cell_frame, text='URL:')
        ui.pack(label, side=tk.LEFT)

        label = self.create_custom_label(cell_frame, text=url, link=url)
        ui.pack(label, side=tk.LEFT)

        # dependencies
        label = self.create_custom_label(
            frame, text='Pypi.com Dependencies:', bold=True
        )
        ui.grid(label, row=2, column=0, sticky=tk.W)

        # PyYAML package
        label = self.create_custom_label(
            frame, text=Data.pyyaml_text, link=Data.pyyaml_link
        )
        ui.grid(label, row=3, column=0, padx=(20, 0), pady=(0, 10), sticky=tk.W)

        # genericlib package
        label = self.create_custom_label(
            frame, text=Data.gtgenlib_text, link=Data.gtgenlib_link
        )
        ui.grid(label, row=3, column=1, padx=(20, 0), pady=(0, 10), sticky=tk.W)

        # license textbox
        label_frame = ui.create(
            self.LabelFrame, parent=paned_window, height=200, width=450,
            text=Data.license_name
        )
        paned_window.add(label_frame, weight=7)

        width = 58 if self.is_macos else 51
        height = 18 if self.is_macos else 14 if self.is_linux else 15
        textbox = ui.create(self.TextArea, parent=label_frame, width=width,
                            height=height, wrap='word')
        ui.grid(textbox, row=0, column=0, padx=5, pady=5)

        scrollbar = ui.create(ttk.Scrollbar, parent=label_frame,
                              orient=tk.VERTICAL, command=textbox.yview)
        ui.grid(scrollbar, row=0, column=1, sticky='nsew')

        textbox.config(yscrollcommand=scrollbar.set)
        textbox.insert(tk.INSERT, Data.license)
        textbox.config(state=tk.DISABLED)

        # footer - copyright
        frame = ui.create(self.Frame, parent=paned_window, width=450, height=20)
        paned_window.add(frame, weight=1)

        label = ui.create(self.Label, parent=frame, text=Data.copyright_text)
        ui.pack(label, side=tk.LEFT, pady=(10, 10))

        label = self.create_custom_label(frame, text=Data.company,
                                         link=Data.company_url)
        ui.pack(label, side=tk.LEFT, pady=(10, 10))

        label = ui.create(self.Label, parent=frame, text='.  All right reserved.')
        ui.pack(label, side=tk.LEFT, pady=(10, 10))

        set_modal_dialog(about)

    def callback_preferences_settings(self):
        """
        Handle the "Preferences > Settings" menu action.

        This callback opens the application's settings interface, allowing
        users to configure preferences such as default behaviors, appearance,
        or other customizable options. It provides a centralized entry point
        for managing user-specific configurations.

        Workflow
        --------
        1. Triggered when the user selects "Preferences > Settings" from the menu.
        2. Launches the settings dialog or page.
        3. Allows the user to view and modify application preferences.

        Returns
        -------
        None
            This method performs a side effect (opening the settings interface)
            but does not return a value.

        Notes
        -----
        - The exact implementation of the settings dialog depends on the GUI
          framework and may include tabs, checkboxes, or input fields.
        - Preferences updated here typically persist across sessions or are
          stored in the application's configuration.
        """
        settings = ui.create(tk.Toplevel, parent=self.root)
        self.set_title(widget=settings, title='Settings')
        width = 544 if self.is_macos else 500 if self.is_linux else 392
        height = 320
        x, y = get_relative_center_location(self.root, width, height)
        settings.geometry(f'{width}x{height}+{x}+{y}')
        settings.resizable(False, False)

        top_frame = ui.create(self.Frame, parent=settings)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # Settings - Arguments
        label_frame_args = ui.create(self.LabelFrame, parent=top_frame,
                                     height=360, width=380, text='Arguments')
        ui.grid(label_frame_args, row=0, column=0, padx=10, pady=10, sticky=tk.W)

        # arguments checkboxes
        lst = [
            ['ignore_case', self.ignore_case_var, 0, 0],
            ['prepended_ws', self.prepended_ws_var, 0, 3],
            ['appended_ws', self.appended_ws_var, 0, 5]
        ]
        for text, variable, row, column in lst:
            checkbox = ui.create(
                self.CheckBox, parent=label_frame_args, text=text,
                variable=variable, onvalue=True, offvalue=False
            )
            ui.grid(checkbox, row=row, column=column, padx=2, pady=2, sticky=tk.W)

        pady = 0 if self.is_macos else 3

        label = ui.create(self.Label, parent=label_frame_args, text='Max Words')
        ui.grid(label, row=1, column=0, columnspan=2, padx=2, pady=(5, pady),
               sticky=tk.W)

        textbox = ui.create(
            self.TextBox, parent=label_frame_args, width=5,
            textvariable=self.max_words_var
        )
        ui.grid(textbox, row=1, column=2, padx=2, pady=(5, pady), sticky=tk.W)

        label = self.Label(label_frame_args, text='Test Name')
        ui.grid(label, row=2, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W)

        textbox = ui.create(
            self.TextBox, parent=label_frame_args, width=45,
            textvariable=self.test_name_var
        )
        ui.grid(textbox, row=2, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        label = ui.create(self.Label, parent=label_frame_args, text='Class Name')
        ui.grid(label, row=3, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W)

        textbox = ui.create(
            self.TextBox, parent=label_frame_args, width=45,
            textvariable=self.test_cls_name_var
        )
        ui.grid(textbox, row=3, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        label = ui.create(self.Label, parent=label_frame_args, text='Filename')
        ui.grid(label, row=4, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W)

        textbox = ui.create(
            self.TextBox, parent=label_frame_args, width=45,
            textvariable=self.filename_var
        )
        ui.grid(textbox, row=4, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        label = self.Label(
            label_frame_args, text='Author'
        )
        ui.grid(label, row=5, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W)

        textbox = ui.create(
            self.TextBox, parent=label_frame_args, width=45,
            textvariable=self.author_var
        )
        ui.grid(textbox, row=5, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        label = ui.create(self.Label, parent=label_frame_args, text='Email')
        ui.grid(label, row=6, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W)

        textbox = ui.create(
            self.TextBox, parent=label_frame_args, width=45,
            textvariable=self.email_var
        )
        ui.grid(textbox, row=6, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        label = ui.create(self.Label, parent=label_frame_args, text='Company')
        ui.grid(label, row=7, column=0, columnspan=2,
                padx=2, pady=(pady, 10), sticky=tk.W)

        textbox = ui.create(self.TextBox, parent=label_frame_args, width=45,
                            textvariable=self.company_var)
        ui.grid(textbox, row=7, column=2, columnspan=4, padx=2, pady=(pady, 10),
               sticky=tk.W)

        # OK and Default buttons
        frame = ui.create(self.Frame, parent=top_frame, height=20, width=380)
        ui.grid(frame, row=2, column=0, padx=10, pady=10, sticky=tk.E + tk.S)

        button = ui.create(
            self.Button, parent=frame, text='Default',
            command=lambda: self.set_default_setting(),
        )
        ui.grid(button, row=0, column=6, padx=1, pady=1, sticky=tk.E)

        button = ui.create(self.Button, parent=frame, text='OK',
                           command=lambda: settings.destroy())
        ui.grid(button, row=0, column=7, padx=1, pady=1, sticky=tk.E)

        set_modal_dialog(settings)

    def do_show_system_references_or_symbol_references(self, title='',
                                                       filename=''):
        """
        Display a dialog for viewing system or symbol references.

        This method is triggered from the "Preferences > System References"
        or "Preferences > Symbol References" menu options. It opens a dialog
        window that loads and displays reference data from the specified file,
        allowing users to review predefined keywords, patterns, or symbols.

        Parameters
        ----------
        title : str, optional
            The title of the dialog window. Defaults to an empty string.
            If provided, the dialog title is set accordingly.
        filename : str, optional
            The name of the file containing reference data to display.
            Defaults to an empty string.

        Returns
        -------
        None
            This method performs a side effect (opening a dialog and loading
            reference data) but does not return a value.

        Notes
        -----
        - The dialog may be used for inspecting either system-level references
          or symbol references depending on the menu action.
        - The `filename` argument should point to a valid reference file
          (e.g., `system_references.yaml` or `symbol_references.yaml`).
        """
        sys_ref = ui.create(tk.Toplevel, parent=self.root)
        self.set_title(widget=sys_ref, title=title)
        width, height = 600, 500
        x, y = get_relative_center_location(self.root, width, height)
        sys_ref.geometry(f'{width}x{height}+{x}+{y}')

        top_frame = ui.create(self.Frame, parent=sys_ref)
        ui.pack(top_frame, fill=tk.BOTH, expand=True)

        panedwindow = ui.create(self.PanedWindow, parent=top_frame, orient=tk.VERTICAL)
        ui.pack(panedwindow, fill=tk.BOTH, expand=True)

        text_frame = ui.create(self.Frame, parent=panedwindow,
                               width=500, height=300, relief=tk.RIDGE)
        panedwindow.add(text_frame, weight=9)

        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        textarea = ui.create(self.TextArea, parent=text_frame,
                             width=20, height=5, wrap='none')
        content = utils.File.read(filename)
        self.set_textarea(textarea, content)

        ui.grid(textarea, row=0, column=0, sticky='nswe')

        vscrollbar = ui.create(ttk.Scrollbar, parent=text_frame,
                               orient=tk.VERTICAL, command=textarea.yview)
        ui.grid(vscrollbar, row=0, column=1, sticky='ns')

        hscrollbar = ui.create(ttk.Scrollbar, parent=text_frame,
                               orient=tk.HORIZONTAL, command=textarea.xview)
        ui.grid(hscrollbar, row=1, column=0, sticky='ew')

        textarea.config(yscrollcommand=vscrollbar.set,
                        xscrollcommand=hscrollbar.set,
                        state=tk.DISABLED)

        padx, pady = (0, 0) if self.is_macos else (2, 2)

        button = ui.create(self.Button, parent=top_frame, text='OK',
                           command=lambda: sys_ref.destroy())
        ui.pack(button, side=tk.RIGHT, padx=padx, pady=pady)

        set_modal_dialog(sys_ref)

    def callback_preferences_system_reference(self):
        """
        Handle the "Preferences > System References" menu action.

        This callback opens a dialog for viewing system reference data. It
        delegates to `do_show_system_references_or_symbol_references`, passing
        the appropriate title and filename defined in `Data.system_reference_filename`.

        Workflow
        --------
        1. Triggered when the user selects "Preferences > System References"
           from the menu.
        2. Calls `do_show_system_references_or_symbol_references` with:
           - title set to "System References"
           - filename set to the system reference file path
        3. Displays a dialog containing system-level reference information.

        Returns
        -------
        None
            This method performs a side effect (opening a dialog) but does not
            return a value.

        Notes
        -----
        - The system reference file typically contains predefined keywords,
          patterns, or symbols used by the application.
        - This callback ensures consistency by centralizing the filename in
          `Data.system_reference_filename`.
        """
        self.do_show_system_references_or_symbol_references(
            title="System References",
            filename=Data.system_reference_filename
        )

    def callback_preferences_symbol_reference(self):
        """
        Handle the "Preferences > Symbol References" menu action.

        This callback opens a dialog for viewing symbol reference data. It
        delegates to `do_show_system_references_or_symbol_references`, passing
        the appropriate title and filename defined in `Data.symbol_reference_filename`.

        Workflow
        --------
        1. Triggered when the user selects "Preferences > Symbol References"
           from the menu.
        2. Calls `do_show_system_references_or_symbol_references` with:
           - title set to "Symbol References"
           - filename set to the symbol reference file path
        3. Displays a dialog containing symbol-level reference information.

        Returns
        -------
        None
            This method performs a side effect (opening a dialog) but does not
            return a value.

        Notes
        -----
        - The symbol reference file typically contains predefined symbols,
          tokens, or identifiers used by the application.
        - This callback ensures consistency by centralizing the filename in
          `Data.symbol_reference_filename`.
        """

        self.do_show_system_references_or_symbol_references(
            title="Symbol References",
            filename=Data.symbol_reference_filename
        )

    def callback_preferences_user_reference(self):
        """
        Handle the "Preferences > User References" menu action.

        This callback opens a dialog for viewing or editing user-defined
        reference data. It delegates to
        `do_show_system_references_or_symbol_references`, passing the
        appropriate title and filename defined in
        `Data.user_reference_filename`.

        Workflow
        --------
        1. Triggered when the user selects "Preferences > User References"
           from the menu.
        2. Calls `do_show_system_references_or_symbol_references` with:
           - title set to "User References"
           - filename set to the user reference file path
        3. Displays a dialog containing user-specific reference information.

        Returns
        -------
        None
            This method performs a side effect (opening a dialog) but does not
            return a value.

        Notes
        -----
        - The user reference file typically contains custom keywords, patterns,
          or symbols defined by the user.
        - This callback ensures consistency by centralizing the filename in
          `Data.user_reference_filename`.
        """

        # Start of logic for the save inner function.
        def save(node):
            """
            Save updated user reference data from a `tk.Text` widget.

            This inner function retrieves the current content of the user reference
            text area, compares it against the existing file content, and writes
            changes back to the user reference file if modifications are detected.
            It validates the new content before saving and updates the in-memory
            reference object (`REF`). If validation fails, an error message box is
            displayed.

            Parameters
            ----------
            node : tk.Text
                A tkinter `Text` widget containing the user reference data to be saved.

            Returns
            -------
            None
                This function performs side effects (file I/O, validation, and UI
                updates) but does not return a value.

            Workflow
            --------
            1. Read the original content from `Data.user_reference_filename`.
            2. Retrieve the new content from the `tk.Text` widget.
            3. If the new content matches the original (ignoring whitespace), do nothing.
            4. Otherwise:
               - Validate the new content using `REF.test`.
               - Write the new content back to the user reference file.
               - Parse the content as YAML and update `REF` with the new data.
               - If validation or parsing fails, display an error message box.

            Notes
            -----
            - Content is validated before being persisted to ensure correct format.
            - YAML parsing uses `yaml.SafeLoader` for security.
            - Errors are caught and reported via a message box with the exception type
              and message.
            """
            fn_ = Data.user_reference_filename
            origin_content = open(fn_).read()
            new_content = node.get('1.0', 'end')
            if new_content.strip() == origin_content.strip():
                return
            else:
                try:
                    REF.test(new_content)
                    open(fn_, 'w').write(new_content)

                    yaml_obj = yaml.load(new_content, Loader=yaml.SafeLoader)
                    REF.update(yaml_obj)

                except Exception as ex:
                    error = '{}: {}'.format(type(ex).__name__, ex)
                    create_msgbox(title='Invalid Format', error=error)

        # Completion of the insert inner function logic.
        # Start of logic for the insert inner function.
        def insert(var, node):
            """
            Insert a new user-defined pattern into the reference editor.

            This inner function validates a proposed pattern name, ensures it is
            unique, and appends a corresponding pattern layout to the content of
            the user reference text area. If the name is invalid or already exists,
            an error message box is displayed instead of modifying the content.

            Parameters
            ----------
            var : tkinter.StringVar
                A `StringVar` holding the proposed pattern name entered by the user.
                The value is stripped of whitespace before validation.
            node : tkinter.Text
                A `Text` widget containing the current user reference content. The
                new pattern layout is appended to this widget if validation succeeds.

            Returns
            -------
            None
                This function performs side effects (validation, error reporting,
                and text widget updates) but does not return a value.

            Workflow
            --------
            1. Retrieve and strip the proposed pattern name from `var`.
            2. Validate the name against the regex `\w+` (alphanumeric and underscore).
               - If invalid, show an error message and exit.
            3. Check for duplication by scanning existing lines in `node`.
               - If the name already exists, show an error message and exit.
            4. Clear the `StringVar` value.
            5. Retrieve a pattern layout template from `PatternReference`.
            6. Replace the placeholder with the validated name.
            7. Append the new layout to the existing content in `node`.
            8. Refresh the `Text` widget with the updated content.

            Notes
            -----
            - Error messages are displayed using `create_msgbox`.
            - Pattern layouts are generated via `PatternReference.get_pattern_layout`.
            - The insertion point is set to `tk.INSERT` to place the new content
              at the current cursor position.
            """
            name = var.get().strip()
            if not re.match(r'\w+$', name):
                error = 'Name of pattern must be alphanumeric and/or underscore'
                create_msgbox(title='Pattern Naming', error=error)
                return

            content_ = node.get('1.0', 'end')
            is_duplicated = False

            for line in content_.splitlines():
                if line.startswith('{}:'.format(name)):
                    is_duplicated = True
                    break

            if is_duplicated:
                fmt = 'This "{}" name already exist.  Please use a different name.'
                error = fmt.format(name)
                create_msgbox(title='Pattern Naming', error=error)
                return

            var.set('')
            pattern_layout = PatternReference.get_pattern_layout(name)
            pattern_layout = pattern_layout.replace('name_placeholder', name)
            new_content_ = '{}\n\n{}\n'.format(content_.strip(),
                                               pattern_layout).lstrip()
            node.delete("1.0", "end")
            node.insert(tk.INSERT, new_content_)

        # Completion of the insert inner function logic.

        fn = Data.user_reference_filename
        file_obj = Path(fn)
        if not file_obj.exists():
            question = f'{repr(fn)} file does not exist.\nWould you like to create it?'
            result = create_msgbox(question=question)
            if result == 'yes':
                parent = file_obj.parent
                if not parent.exists():
                    parent.mkdir(parents=True, exist_ok=True)
                file_obj.touch()
            else:
                return

        user_ref = ui.create(tk.Toplevel, parent=self.root)
        # user_ref.bind("<FocusOut>", lambda event: user_ref.destroy())
        self.set_title(widget=user_ref, title='User References ({})'.format(fn))
        width, height = 600, 500
        x, y = get_relative_center_location(self.root, width, height)
        user_ref.geometry(f'{width}x{height}+{x}+{y}')

        top_frame = ui.create(self.Frame, parent=user_ref)
        ui.pack(top_frame, fill=tk.BOTH, expand=True)

        panedwindow = ui.create(self.PanedWindow, parent=top_frame, orient=tk.VERTICAL)
        ui.pack(panedwindow, fill=tk.BOTH, expand=True)

        text_frame = ui.create(self.Frame, parent=panedwindow,
                               width=500, height=300, relief=tk.RIDGE)
        panedwindow.add(text_frame, weight=9)

        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        textarea = ui.create(self.TextArea, text_frame, width=20, height=5, wrap='none')
        content = utils.File.read(Data.user_reference_filename)
        self.set_textarea(textarea, content)

        ui.grid(textarea, row=0, column=0, sticky='nswe')

        vscrollbar = ui.create(ttk.Scrollbar, parent=text_frame,
                               orient=tk.VERTICAL, command=textarea.yview)
        ui.grid(vscrollbar, row=0, column=1, sticky='ns')

        hscrollbar = ui.create(ttk.Scrollbar, parent=text_frame,
                               orient=tk.HORIZONTAL, command=textarea.xview)
        ui.grid(hscrollbar, row=1, column=0, sticky='ew')

        textarea.config(
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set,
        )

        padx, pady = (0, 0) if self.is_macos else (2, 2)

        button = ui.create(self.Button, parent=top_frame, text='Save',
                           command=lambda: save(textarea))
        ui.pack(button, side=tk.RIGHT, padx=padx, pady=pady)

        button = ui.create(self.Button, parent=top_frame, text='Close',
                           command=lambda: user_ref.destroy())
        ui.pack(button, side=tk.RIGHT, padx=padx, pady=pady)

        label = ui.create(self.Label, parent=top_frame, text='Name:')
        ui.pack(label, side=tk.LEFT, padx=padx, pady=pady)

        textbox = ui.create(
            self.TextBox, parent=top_frame, width=25,
            textvariable=self.new_pattern_name_var
        )
        ui.pack(textbox, side=tk.LEFT, padx=padx, pady=pady)

        button = ui.create(
            self.Button, parent=top_frame, text='Insert',
            command=lambda: insert(self.new_pattern_name_var, textarea),
        )
        ui.pack(button, side=tk.LEFT, padx=padx, pady=pady)

        set_modal_dialog(user_ref)

    def build_menu(self):
        """
        Construct the main menubar for the Regex GUI application.

        This method initializes and attaches a menubar to the root window,
        organizing commands under **File**, **Preferences**, and **Help**
        categories. Each menu provides access to core functionality such as
        file operations, application preferences, and help resources.

        Workflow
        --------
        1. Create a `tk.Menu` instance and attach it to the root window.
        2. Define submenus:
           - **File**
             * Open: Launches a file dialog to load text data.
             * Quit: Exits the application.
           - **Preferences**
             * Settings: Opens the settings dialog.
             * System References: Displays system reference data.
             * Symbol References: Displays symbol reference data.
             * User References: Displays user-defined reference data.
           - **Help**
             * Documentation: Opens the "Getting Started" guide in a browser.
             * View Licenses: Opens the license information page.
             * About: Displays application metadata.
        3. Add separators between logical groups of commands for clarity.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching the
            menubar) but does not return a value.

        Notes
        -----
        - The menubar is attached to `self.root` via `self.root.config(menu=...)`.
        - Each command delegates to a corresponding callback method for handling
          user actions.
        - Separators are used to visually group related commands.
        """
        menu_bar = ui.create(tk.Menu, parent=self.root)
        self.root.config(menu=menu_bar)
        file = ui.create(tk.Menu, parent=menu_bar)
        preferences = ui.create(tk.Menu, parent=menu_bar)
        help_ = ui.create(tk.Menu, parent=menu_bar)

        menu_bar.add_cascade(menu=file, label='File')
        menu_bar.add_cascade(menu=preferences, label='Preferences')
        menu_bar.add_cascade(menu=help_, label='Help')

        file.add_command(label='Open',
                         command=lambda: self.callback_file_open())
        file.add_separator()
        file.add_command(label='Quit', command=lambda: self.root.quit())

        preferences.add_command(
            label='Settings',
            command=lambda: self.callback_preferences_settings()
        )
        preferences.add_separator()
        preferences.add_command(
            label='System References',
            command=lambda: self.callback_preferences_system_reference()
        )
        preferences.add_command(
            label='Symbol References',
            command=lambda: self.callback_preferences_symbol_reference()
        )
        preferences.add_separator()
        preferences.add_command(
            label='User References',
            command=lambda: self.callback_preferences_user_reference()
        )

        help_.add_command(label='Documentation',
                          command=lambda: self.callback_help_documentation())
        help_.add_command(label='View Licenses',
                          command=lambda: self.callback_help_view_licenses())
        help_.add_separator()
        help_.add_command(label='About',
                          command=lambda: self.callback_help_about())

    def build_frame(self):
        """
        Construct the main frame layout for the Regex GUI.

        This method builds the vertical layout of the application using a
        `PanedWindow` container. It organizes three primary frames:
        - **Text Frame**: Holds the input text area for test data.
        - **Entry Frame**: Contains action buttons and controls.
        - **Result Frame**: Displays the output or test results.

        Workflow
        --------
        1. Create a vertical `PanedWindow` and attach it to the root window.
        2. Define three frames with fixed dimensions and ridge borders:
           - `text_frame` (600×300)
           - `entry_frame` (600×40)
           - `result_frame` (600×350)
        3. Add the frames to the `PanedWindow` with relative weights to control
           resizing behavior:
           - `text_frame` → weight=4
           - `entry_frame` → default weight
           - `result_frame` → weight=5

        Returns
        -------
        None
            This method performs side effects (constructing and attaching frames)
            but does not return a value.

        Notes
        -----
        - The `PanedWindow` is packed to fill both dimensions and expand with
          padding for spacing.
        - Frame weights determine how much space each section receives when
          resizing the window.
        """
        self.panedwindow = ui.create(self.PanedWindow, parent=self.root,
                                     orient=tk.VERTICAL)
        ui.pack(self.panedwindow, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.text_frame = ui.create(self.Frame, parent=self.panedwindow,
                                    width=600, height=300, relief=tk.RIDGE)

        self.entry_frame = ui.create(self.Frame, parent=self.panedwindow,
                                     width=600, height=40, relief=tk.RIDGE)

        self.result_frame = ui.create(self.Frame, parent=self.panedwindow,
                                      width=600, height=350, relief=tk.RIDGE)

        self.panedwindow.add(self.text_frame, weight=4)
        self.panedwindow.add(self.entry_frame)
        self.panedwindow.add(self.result_frame, weight=5)

    def build_textarea(self):
        """
        Construct the input text area for the Regex GUI.

        This method creates a scrollable `TextArea` widget inside the
        `text_frame`. The widget serves as the primary input field for
        entering or editing text data used in regex testing. Both vertical
        and horizontal scrollbars are attached to support navigation of
        large or unwrapped text content.

        Workflow
        --------
        1. Configure the `text_frame` grid to allow resizing:
           - Row 0 and column 0 are given weight for expansion.
        2. Create a `TextArea` widget with fixed dimensions and no wrapping.
        3. Place the `TextArea` in the grid at row 0, column 0, expanding
           in all directions (`nswe`).
        4. Add a vertical scrollbar linked to the `yview` of the text area.
        5. Add a horizontal scrollbar linked to the `xview` of the text area.
        6. Configure the text area to update scrollbar positions during
           scrolling.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching
            widgets) but does not return a value.

        Notes
        -----
        - The `wrap='none'` option ensures text does not automatically wrap,
          making horizontal scrolling necessary for long lines.
        - Scrollbars are synchronized with the text area via `yscrollcommand`
          and `xscrollcommand`.
        """
        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.input_textarea = ui.create(self.TextArea, parent=self.text_frame,
                                        width=20, height=5, wrap='none')
        ui.grid(self.input_textarea, row=0, column=0, sticky='nswe')

        vscrollbar = ui.create(ttk.Scrollbar, parent=self.text_frame,
                               orient=tk.VERTICAL, command=self.input_textarea.yview)
        ui.grid(vscrollbar, row=0, column=1, sticky='ns')

        hscrollbar = ui.create(ttk.Scrollbar, parent=self.text_frame,
                               orient=tk.HORIZONTAL, command=self.input_textarea.xview)
        hscrollbar.grid(row=1, column=0, sticky='ew')

        self.input_textarea.config(
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set
        )

    def build_entry(self):
        """
        Construct the entry controls section for the Regex GUI.

        This method builds the `entry_frame` portion of the interface, which
        contains interactive widgets such as buttons, text fields, and other
        controls used to trigger actions (e.g., opening files, running regex
        tests, saving results, or switching modes). It provides the user with
        the primary means of interacting with the application beyond text input.

        Workflow
        --------
        1. Initialize the `entry_frame` container.
        2. Populate the frame with action-oriented widgets (buttons, textboxes,
           comboboxes, etc.).
        3. Configure layout and grid options to ensure controls are aligned
           and responsive to resizing.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching
            widgets) but does not return a value.

        Notes
        -----
        - The `entry_frame` is positioned between the text input area and
          the result display frame.
        - Widgets added here typically connect to callback methods such as
          `callback_file_open`, `callback_preferences_*`, or regex execution
          functions.
        - Acts as the control hub for user actions in the GUI.
        """

        # Start of logic for the callback_build_btn inner function.
        def callback_build_btn():
            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error = "Regex pattern cannot be built: no input data provided."
                )
                return

            if self.is_pattern_builder_app:
                try:
                    kwargs = self.get_pattern_builder_args()
                    pattern = PatternBuilder(user_data, **kwargs)
                    result = 'pattern = r{}'.format(enclose_string(pattern))
                    self.set_textarea(self.result_textarea, result)
                    self.snapshot.update(test_result=result)
                except Exception as ex:
                    error = '{}: {}'.format(type(ex).__name__, ex)
                    create_msgbox(title='PatternBuilder Error', error=error)
            else:
                try:
                    kwargs = self.get_regex_builder_args()
                    factory = RegexBuilder(user_data=user_data, **kwargs)
                    factory.build()

                    patterns = factory.patterns
                    total = len(patterns)
                    if total >= 1:
                        if total == 1:
                            result = 'pattern = r{}'.format(
                                enclose_string(patterns[0]))
                        else:
                            lst = []
                            fmt = 'pattern{} = r{}'
                            for index, pattern in enumerate(patterns, 1):
                                lst.append(
                                    fmt.format(index, enclose_string(pattern)))
                            result = '\n'.join(lst)
                        self.test_data_btn_var.set('Test Data')
                        self.set_textarea(self.result_textarea, result)
                        self.save_as_btn.config(state=tk.NORMAL)
                        self.copy_text_btn.config(state=tk.NORMAL)
                    else:
                        error = "An error occurred in RegexBuilder. Please report this bug."
                        create_msgbox(title='RegexBuilder Error', error=error)
                except Exception as ex:
                    error = '{}: {}'.format(type(ex).__name__, ex)
                    create_msgbox(title='RegexBuilder Error', error=error)

        # Completion of the callback_build_btn inner function logic.

        # Start of logic for the callback_save_as_btn inner function.
        def callback_save_as_btn():
            filename = filedialog.asksaveasfilename()
            content = Application.get_textarea(self.result_textarea)
            utils.File.write(filename, content)

        # Completion of the callback_save_as_btn inner function logic.

        # Start of logic for the callback_clear_text_btn inner function.
        def callback_clear_text_btn():
            self.input_textarea.delete("1.0", "end")
            self.result_textarea.delete("1.0", "end")
            self.save_as_btn.config(state=tk.DISABLED)
            self.copy_text_btn.config(state=tk.DISABLED)
            self.test_data_btn.config(state=tk.DISABLED)
            self.snapshot.update(test_data=None)
            self.snapshot.update(test_result='')
            self.test_data_btn_var.set('Test Data')
            # self.root.clipboard_clear()
            self.set_title()
        # Completion of the callback_clear_text_btn inner function logic.

        # Start of logic for the callback_copy_text_btn inner function.
        def callback_copy_text_btn():
            content = Application.get_textarea(self.result_textarea)
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()

        # Completion of the callback_copy_text_btn inner function logic.

        # Start of logic for the callback_paste_text_btn inner function.
        def callback_paste_text_btn():
            try:
                data = self.root.clipboard_get()
                if not data:
                    return

                if not self.is_pattern_builder_app:
                    self.test_data_btn.config(state=tk.NORMAL)
                    self.test_data_btn_var.set('Test Data')
                    self.set_textarea(self.result_textarea, '')
                    self.snapshot.update(test_data=data)

                title = '<<PASTE - Clipboard>>'
                self.set_textarea(self.input_textarea, data, title=title)
            except Exception as ex:
                print(ex)
                create_msgbox(
                    title='Empty Clipboard',
                    info='CAN NOT paste because there is no data in pasteboard.'
                )

        # Completion of the callback_paste_text_btn inner function logic.

        # Start of logic for the callback_snippet_btn inner function.
        def callback_snippet_btn():
            if self.snapshot.test_data is None:
                create_msgbox(
                    title='No Test Data',
                    error=(
                        "Cannot build Python test script without test data.\n"
                        "Please use the Open or Paste button to load test data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error = "Python test script generation failed: no input data provided."
                )
                return

            try:
                kwargs = self.get_regex_builder_args()
                factory = RegexBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,
                    **kwargs
                )

                script = factory.create_python_test()
                self.set_textarea(self.result_textarea, script)
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(test_result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexBuilder Error', error=error)

        # Completion of the callback_snippet_btn inner function logic.

        # Start of logic for the callback_unittest_btn inner function.
        def callback_unittest_btn():
            if self.snapshot.test_data is None:
                create_msgbox(
                    title='No Test Data',
                    error=(
                        "Cannot build Python unittest script without test data.\n"
                        "Please use the Open or Paste button to load test data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error = "Unittest script generation failed: no input data provided."
                )
                return

            try:
                kwargs = self.get_regex_builder_args()
                factory = RegexBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,
                    **kwargs
                )

                script = factory.create_unittest()
                self.set_textarea(self.result_textarea, script)
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(test_result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexBuilder Error', error=error)

        # Completion of the callback_unittest_btn inner function logic.

        # Start of logic for the callback_pytest_btn inner function.
        def callback_pytest_btn():
            if self.snapshot.test_data is None:
                create_msgbox(
                    title='No Test Data',
                    error=(
                        "Cannot build Python pytest script without test data.\n"
                        "Please use the Open or Paste button to load test data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error = "Pytest script generation failed: no input data provided."
                )
                return

            try:
                kwargs = self.get_regex_builder_args()
                factory = RegexBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,
                    **kwargs
                )

                script = factory.create_pytest()
                self.set_textarea(self.result_textarea, script)
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(test_result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexBuilder Error', error=error)

        # Completion of the callback_pytest_btn inner function logic.

        # Start of logic for the callback_test_data_btn inner function.
        def callback_test_data_btn():
            if self.snapshot.test_data is None:
                create_msgbox(
                    title='No Test Data',
                    error = "Test data is required. Use the Open or Paste button to load it."
                )
                return

            name = self.test_data_btn_var.get()
            if name == 'Test Data':
                self.test_data_btn_var.set('Hide')
                self.set_textarea(
                    self.result_textarea,
                    self.snapshot.test_data
                )
            else:
                self.test_data_btn_var.set('Test Data')
                self.set_textarea(
                    self.result_textarea,
                    self.snapshot.test_result
                )

        # Completion of the callback_test_data_btn inner function logic.

        # Start of logic for the callback_builder_checkbox inner function.
        def callback_builder_checkbox():
            if self.is_pattern_builder_app:
                self.shift_to_pattern_builder_app()
            else:
                self.shift_to_regex_builder_app()

        # Completion of the callback_builder_checkbox inner function logic.

        # Start of logic for the callback_rf_btn inner function.
        # def callback_rf_btn():
        #     create_msgbox(
        #         title='Robotframework feature',
        #         info="The Robotframework button will be available starting with the 1.x release."
        #     )

        # Completion of the callback_rf_btn inner function logic.

        # radio buttons
        self.line_radio_btn = ui.create(
            self.RadioButton, parent=self.entry_frame, text='line',
            variable=self.radio_line_or_multiline_btn_var, value='line'
        )
        ui.grid(self.line_radio_btn, row=0, column=0, padx=(4, 0))

        self.multiline_radio_btn = ui.create(
            self.RadioButton, parent=self.entry_frame, text='multiline',
            variable=self.radio_line_or_multiline_btn_var, value='multiline'
        )
        ui.grid(self.multiline_radio_btn, row=0, column=1, padx=2)

        btn_width = 5.5 if self.is_macos else 8
        # open button
        open_file_btn = ui.create(
            self.Button, parent=self.entry_frame, text='Open',
            command=self.callback_file_open, width=btn_width
        )
        ui.grid(open_file_btn, row=0, column=2, pady=2)

        # Save As button
        self.save_as_btn = ui.create(
            self.Button, parent=self.entry_frame, text='Save As',
            command=callback_save_as_btn, width=btn_width
        )
        ui.grid(self.save_as_btn, row=0, column=3)
        self.save_as_btn.config(state=tk.DISABLED)

        # copy button
        self.copy_text_btn = ui.create(
            self.Button, parent=self.entry_frame, text='Copy',
            command=callback_copy_text_btn, width=btn_width
        )
        ui.grid(self.copy_text_btn, row=0, column=4)
        self.copy_text_btn.config(state=tk.DISABLED)

        # paste button
        paste_text_btn = ui.create(
            ttk.Button, parent=self.entry_frame, text='Paste',
            command=callback_paste_text_btn, width=btn_width
        )
        ui.grid(paste_text_btn, row=0, column=5)

        # clear button
        clear_text_btn = ui.create(
            self.Button, parent=self.entry_frame, text='Clear',
            command=callback_clear_text_btn, width=btn_width
        )
        ui.grid(clear_text_btn, row=0, column=6)

        # build button
        build_btn = ui.create(
            self.Button, parent=self.entry_frame, text='Build',
            command=callback_build_btn, width=btn_width
        )
        ui.grid(build_btn, row=0, column=7)

        # snippet button
        self.snippet_btn = ui.create(
            self.Button, parent=self.entry_frame, text='Snippet',
            command=callback_snippet_btn, width=btn_width
        )
        ui.grid(self.snippet_btn, row=0, column=8)

        # unittest button
        self.unittest_btn = self.Button(self.entry_frame, text='Unittest',
                                        command=callback_unittest_btn,
                                        width=btn_width)
        self.unittest_btn.grid(row=0, column=9)

        # pytest button
        self.pytest_btn = ui.create(
            self.Button, parent=self.entry_frame, text='Pytest',
            command=callback_pytest_btn, width=btn_width
        )
        ui.grid(self.pytest_btn, row=0, column=10)

        # test_data button
        self.test_data_btn = ui.create(
            self.Button, parent=self.entry_frame,
            command=callback_test_data_btn,
            textvariable=self.test_data_btn_var,
            width=btn_width
        )
        ui.grid(self.test_data_btn, row=0, column=11)
        self.test_data_btn.config(state=tk.DISABLED)

        # builder checkbox
        builder_checkbox = ui.create(
            self.CheckBox, parent=self.entry_frame, text='Builder',
            variable=self.builder_checkbox_var, onvalue=True, offvalue=False,
            command=callback_builder_checkbox
        )
        ui.grid(builder_checkbox, row=0, column=12)

        self.var_name_frame = self.Frame(self.entry_frame)

        label = ui.create(self.Label, parent=self.var_name_frame, text='var_name')
        ui.pack(label, padx=(10, 4), side=tk.LEFT)

        textbox = ui.create(
            self.TextBox, parent=self.var_name_frame, width=12,
            textvariable=self.var_name_var
        )
        ui.pack(textbox, side=tk.LEFT)

        self.word_bound_frame = ui.create(self.Frame, parent=self.entry_frame)

        label = ui.create(self.Label, parent=self.word_bound_frame, text='word_bound')
        ui.pack(label, padx=(10, 4), side=tk.LEFT)

        combobox = ui.create(
            ttk.Combobox, parent=self.word_bound_frame, state='readonly',
            values=['both', 'left', 'right', 'none'],
            textvariable=self.word_bound_var,
            width=6
        )
        ui.pack(combobox, side=tk.LEFT)

        # Robotframework button
        # rf_btn = self.Button(self.entry_frame, text='RF',
        #                     command=callback_rf_btn, width=4)
        # rf_btn.grid(row=0, column=11)

    def build_result(self):
        """
        Construct the result display area for the Regex GUI.

        This method creates a scrollable `TextArea` widget inside the
        `result_frame`. The widget serves as the output field for displaying
        regex matches, test results, or other feedback generated by the
        application. Both vertical and horizontal scrollbars are attached to
        support navigation of large or unwrapped result content.

        Workflow
        --------
        1. Configure the `result_frame` grid to allow resizing:
           - Row 0 and column 0 are given weight for expansion.
        2. Create a `TextArea` widget with fixed dimensions and no wrapping.
        3. Place the `TextArea` in the grid at row 0, column 0, expanding
           in all directions (`nswe`).
        4. Add a vertical scrollbar linked to the `yview` of the result area.
        5. Add a horizontal scrollbar linked to the `xview` of the result area.
        6. Configure the result area to update scrollbar positions during
           scrolling.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching
            widgets) but does not return a value.

        Notes
        -----
        - The `wrap='none'` option ensures text does not automatically wrap,
          making horizontal scrolling necessary for long lines of output.
        - Scrollbars are synchronized with the result area via `yscrollcommand`
          and `xscrollcommand`.
        """
        self.result_frame.rowconfigure(0, weight=1)
        self.result_frame.columnconfigure(0, weight=1)
        self.result_textarea = ui.create(
            self.TextArea, parent=self.result_frame,
            width=20, height=5, wrap='none'
        )
        ui.grid(self.result_textarea, row=0, column=0, sticky='nswe')

        vscrollbar = ui.create(
            ttk.Scrollbar, parent=self.result_frame, orient=tk.VERTICAL,
            command=self.result_textarea.yview
        )
        ui.grid(vscrollbar, row=0, column=1, sticky='ns')

        hscrollbar = ui.create(
            ttk.Scrollbar, parent=self.result_frame, orient=tk.HORIZONTAL,
            command=self.result_textarea.xview
        )
        ui.grid(hscrollbar, row=1, column=0, sticky='ew')

        self.result_textarea.config(
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set
        )

    def run(self):
        """
        Start the Regex GUI application.

        This method launches the Tkinter main event loop, keeping the
        application window responsive to user interactions such as menu
        selections, text input, and dialog actions. It serves as the
        primary entry point for running the GUI once the application
        has been initialized.

        Workflow
        --------
        1. Initialize the Tkinter event loop via `self.root.mainloop()`.
        2. Keep the GUI active until the user closes the window or
           explicitly terminates the application.

        Returns
        -------
        None
            This method performs a side effect (starting the event loop)
            but does not return a value.

        Notes
        -----
        - Must be called after the application layout and menus are built.
        - Blocks further code execution until the GUI window is closed.
        - Typically invoked by the `execute()` function or directly after
          instantiating `Application`.
        """
        self.root.mainloop()


def execute():
    """
    Launch the Regex GUI application.

    This function serves as the entry point for starting the graphical
    interface of the `regexapp` library. It instantiates the `Application`
    class and invokes its `run` method, initializing the main event loop
    and displaying the GUI to the user.

    Workflow
    --------
    1. Create an instance of `Application`.
    2. Call `Application.run()` to start the Tkinter event loop.
    3. Display the Regex GUI for interactive use.

    Returns
    -------
    None
        This function performs side effects (launching the GUI) but does
        not return a value.

    Notes
    -----
    - Intended to be used as the main entry point when launching the
      application programmatically.
    - Typically invoked from `__main__` or a command-line interface
      wrapper.
    """
    app = Application()
    app.run()
