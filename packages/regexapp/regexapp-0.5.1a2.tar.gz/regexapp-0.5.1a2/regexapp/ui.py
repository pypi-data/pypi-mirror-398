"""
regexapp.ui
===========

Utility functions for constructing and managing Tkinter UI components
in the Regex GUI application. These helpers provide safe wrappers
around common geometry managers (`grid`, `pack`) and a generic factory
for creating widgets. They are designed to simplify layout code and
avoid runtime errors when working with varying widget types.

Functions
---------
- create : Instantiate a Tkinter widget of a given type.
- grid   : Safely apply the `grid` geometry manager to a widget.
- pack   : Safely apply the `pack` geometry manager to a widget.

Notes
-----
These helpers are defensive: if a widget does not support the requested
geometry manager, the call is silently ignored rather than raising an
exception. This makes them useful in generic layout code where widget
types may vary.
"""


def create(ui_type, parent=None, **kwargs):
    """
    Create a UI component of the given type.

    Parameters
    ----------
    ui_type : callable
        The widget class to instantiate (e.g., `tk.Label`, `tk.Button`).
    parent : instance of tkinter.Frame, ...
        The parent widget to attach the component to.
    **kwargs : keyword arguments
        Additional keyword arguments passed to the widget constructor.

    Returns
    -------
    tk.Widget
        The instantiated widget.
    """
    if parent:
        return ui_type(parent, **kwargs)
    return ui_type(**kwargs)


def grid(node, **kwargs):
    """
    Safely apply the Tkinter `grid` geometry manager to a widget.

    This utility function checks whether the given `node` object
    supports the `grid` method (as Tkinter widgets do). If so, it
    calls `node.grid(**kwargs)` with the provided keyword arguments.
    If the object does not support `grid`, the function silently
    does nothing.

    Parameters
    ----------
    node : Tkinter widget
        A Tkinter widget (e.g., `tk.Label`, `tk.Entry`, `tk.Frame`)
        or any object that implements a `grid` method.
    **kwargs : keyword arguments
        Keyword arguments passed directly to `node.grid()`. Common
        options include `row`, `column`, `sticky`, `padx`, and `pady`.

    Returns
    -------
    None
        This function performs a side effect (configuring widget
        layout) but does not return a value.

    Notes
    -----
    - This function is defensive: it avoids raising an `AttributeError`
      if `node` does not implement `grid`.
    - Useful for generic layout helpers where the widget type may vary.
    """
    if getattr(node, 'grid', None) is not None:
        node.grid(**kwargs)


def pack(node, **kwargs):
    """
    Safely apply the Tkinter `pack` geometry manager to a widget.

    This utility function checks whether the given `node` object
    supports the `pack` method (as Tkinter widgets do). If so, it
    calls `node.pack(**kwargs)` with the provided keyword arguments.
    If the object does not support `pack`, the function silently
    does nothing.

    Parameters
    ----------
    node : Tkinter widget
        A Tkinter widget (e.g., `tk.Label`, `tk.Button`, `tk.Frame`)
        or any object that implements a `pack` method.
    **kwargs : keyword arguments
        Keyword arguments passed directly to `node.pack()`. Common
        options include `side`, `fill`, `expand`, `padx`, and `pady`.

    Returns
    -------
    None
        This function performs a side effect (configuring widget
        layout) but does not return a value.

    Notes
    -----
    - This function is defensive: it avoids raising an `AttributeError`
      if `node` does not implement `pack`.
    - Useful for generic layout helpers where the widget type may vary.
    """
    if getattr(node, 'pack', None) is not None:
        node.pack(**kwargs)
