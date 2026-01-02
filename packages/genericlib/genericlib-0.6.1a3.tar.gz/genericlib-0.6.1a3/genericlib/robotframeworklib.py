"""
genericlib.robotframeworklib
============================

Integration utilities for Robot Framework.

This module provides helpers to adapt Python functions and classes from
`genericlib` into Robot Framework–compatible libraries. It focuses on
transforming Python docstrings into Robot Framework documentation style
and dynamically attaching functions to Robot Framework library classes.

Key Components
--------------
- to_robotframework_doc_str:
    Converts a Python function or method docstring into Robot Framework
    documentation style (pipe-prefixed lines). Updates the target Robot
    Framework function with the transformed docstring.

- update_robot_framework_lib:
    Scans a Python class or module for functions matching a given regex
    pattern (default: `"rf_?generic_?lib_?"`). Wraps their docstrings
    into Robot Framework style and attaches them to the specified Robot
    Framework library class.

- RFFile:
    A Robot Framework library class that exposes file-related operations
    from `genericlib.File`. Methods are dynamically attached using
    `update_robot_framework_lib`.

Design Notes
------------
- Docstrings are reformatted to align with Robot Framework's table-style
  documentation, improving readability in Robot Framework test suites.
- Functions are dynamically bound to Robot Framework library classes,
  allowing seamless reuse of `genericlib` utilities in Robot Framework
  environments.
- The default regex pattern ensures only functions intended for Robot
  Framework integration are included.

"""


from genericlib import File
from genericlib.text import dedent_and_strip
import re
import types


def to_robotframework_doc_str(py_func, rf_func=None):
    """
    Get doc_str of py_func, wrap python doc_str to robot framework
    documentation style, and then update to robot framework function.
    Parameters
    ----------
    py_func (FunctionType, MethodType): function or method
    rf_func (FunctionType, Method): function or method.  Default is None.
    """
    if hasattr(py_func, '__func__'):
        doc_str = dedent_and_strip(py_func.__func__.__doc__ or '')
    elif hasattr(py_func, '__doc__'):
        doc_str = dedent_and_strip(py_func.__doc__ or '')
    else:
        return

    if doc_str:
        lst = []
        for line in doc_str.splitlines():
            if line.strip():
                prefix = '' if line.startswith('|') else '| '
                lst.append('%s%s' % (prefix, line))
        if lst:
            rf_func = rf_func or py_func
            new_doc_str = str.join('\n', lst)
            if hasattr(rf_func, '__func__'):
                rf_func.__func__.__doc__ = new_doc_str
            elif hasattr(py_func, '__doc__'):
                rf_func.__doc__ = new_doc_str


def update_robot_framework_lib(rf_cls, py_cls_or_module, pattern='rf_?generic_?lib_?'):
    """
    Find method or function in py_cls_or_module, wrap to doc_str to
    robot framework documentation style, and set to robot framework class.
    Parameters
    ----------
    rf_cls (type): class for robot framework library
    py_cls_or_module (type): python class or module
    pattern (str): regex pattern.  Default is "rf_?generic_?lib_?"
    """
    for attr in dir(py_cls_or_module):
        py_func = getattr(py_cls_or_module, attr)
        if callable(py_func) and re.match(pattern, attr, re.I):
            if isinstance(py_cls_or_module, types.ModuleType):
                setattr(rf_cls, attr, staticmethod(py_func))
            else:
                setattr(rf_cls, attr, py_func)
            to_robotframework_doc_str(py_func)


class RFFile:
    pass


update_robot_framework_lib(RFFile, File)
