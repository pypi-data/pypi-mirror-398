"""
genericlib.utils
================

General-purpose utility classes and functions for data formatting,
validation, platform inspection, object manipulation, and structured output.

This module consolidates a variety of reusable helpers designed to simplify
common programming tasks. It includes tools for formatted printing, type
checking, shell command execution, platform metadata retrieval, safe function
invocation, object manipulation, and tabular data presentation.

Key Components
--------------
Classes
-------
- Printer:
    Provides methods for formatted printing of structured data with optional
    headers, footers, failure messages, and width constraints.

- Misc:
    Offers type-checking and validation helpers for Python’s built-in types.
    Reduces boilerplate when verifying heterogeneous data structures.

- MiscOutput:
    Executes shell commands and captures results (output, exit code, success
    status) in a structured `DotObject`.

- MiscPlatform:
    Retrieves platform and Python environment information, including kernel
    details and documentation URLs. Useful for diagnostics and logging.

- MiscFunction:
    Safely invokes callables while capturing stdout/stderr. Supports dynamic
    error handling and custom exception generation.

- MiscObject:
    Provides object manipulation helpers, including shallow/deep copying and
    cleanup of lists of dictionaries.

- Tabular:
    Formats dictionaries or lists of dictionaries into human-readable tables
    with column selection, justification, and missing-value handling.

Functions
---------
- get_data_as_tabular(data, columns=None, justify='left', missing='not_found'):
    Converts structured data into a tabular string representation.

- print_data_as_tabular(data, columns=None, justify='left', missing='not_found'):
    Prints structured data in a tabular format directly to stdout.

Use Cases
---------
- Improve readability of logs, reports, and console output.
- Validate and manipulate heterogeneous data structures safely.
- Execute shell commands with structured error handling.
- Retrieve environment metadata for debugging or reporting.
- Present structured data (e.g., query results) in tabular form.

"""

import platform
import sys
import re
import copy

import subprocess

from io import StringIO

from textwrap import wrap
from textwrap import indent
from pprint import pprint

import typing
from collections import abc

from genericlib.constant import ECODE
from genericlib.constant import STRING
from genericlib.text import Text
from genericlib.collection import DotObject

from time import time


class Printer:
    """
    A utility class for formatted printing of data.

    The `Printer` class provides methods to format and display data
    with optional headers, footers, failure messages, and width
    constraints. It is designed to improve readability of structured
    output such as lists, dictionaries, or tabular data.

    Methods
    -------
    get(data, header='', footer='', failure_msg='', width=80, width_limit=20) -> str
        Format the given data into a string with optional header and footer.
        If the data is empty or invalid, return the `failure_msg`.
        - `width` specifies the maximum line width before wrapping.
        - `width_limit` controls the maximum width of individual items.

    print(data, header='', footer='', failure_msg='', width=80, width_limit=20, print_func=None) -> None
        Print the formatted data directly to standard output (or a custom
        print function if provided). Accepts the same arguments as `get`.
    """
    @classmethod
    def get(cls, data, header='', footer='',
            width=80, width_limit=20, failure_msg=''):
        """
        Format data into a readable string with optional header and footer.

        This method converts the given `data` into a formatted string,
        applying line wrapping and width constraints for readability.
        If the data is empty or invalid, the provided `failure_msg` is
        returned instead. It is useful for preparing structured output
        (lists, dicts, tabular data) for display or logging.

        Parameters
        ----------
        data : str, list
            a text or a list of text.
        header : str
            Text to prepend before the formatted data. Default is empty.
        footer : str
            Text to append after the formatted data. Default is empty.
        failure_msg : str
            Message to return if `data` is empty or invalid. Default is empty.
        width : int
            Maximum line width before wrapping. Default is 80.
        width_limit : int
            Maximum width of individual items before truncation. Default is 20.

        Returns
        -------
        str
            A formatted string representation of the data, including
            optional header and footer. If `data` is empty, returns
            `failure_msg`.

        Notes
        -----
        - Line wrapping ensures readability for long strings or lists.
        - Width limits prevent overly long items from breaking formatting.
        - This method does not print directly; use `Printer.print` for output.
        """
        lst = []
        result = []

        if width > 0:
            right_bound = width - 4
        else:
            right_bound = 76

        headers = []
        if header:
            if Misc.is_mutable_sequence(header):
                for item in header:
                    for line in str(item).splitlines():
                        headers.extend(wrap(line, width=right_bound))
            else:
                headers.extend(wrap(str(header), width=right_bound))

        footers = []
        if footer:
            if Misc.is_mutable_sequence(footer):
                for item in footer:
                    for line in str(item).splitlines():
                        footers.extend(wrap(line, width=right_bound))
            else:
                footers.extend(wrap(str(footer), width=right_bound))

        if data:
            data = data if Misc.is_mutable_sequence(data) else [data]
        else:
            data = []

        for item in data:
            if width > 0:
                if width >= width_limit:
                    for line in str(item).splitlines():
                        lst.extend(wrap(line, width=right_bound + 4))
                else:
                    lst.extend(line.rstrip() for line in str(item).splitlines())
            else:
                lst.append(str(item))
        length = max(len(str(i)) for i in lst + headers + footers)

        if width >= width_limit:
            length = right_bound if right_bound > length else length

        result.append(Text.format('+-{}-+', '-' * length))      # noqa
        if header:
            for item in headers:
                result.append(Text.format('| {} |', item.ljust(length)))    # noqa
            result.append(Text.format('+-{}-+', '-' * length))  # noqa

        for item in lst:
            result.append(item)
        result.append(Text.format('+-{}-+', '-' * length))      # noqa

        if footer:
            for item in footers:
                result.append(Text.format('| {} |', item.ljust(length)))    # noqa
            result.append(Text.format('+-{}-+', '-' * length))  # noqa

        if failure_msg:
            result.append(failure_msg)

        txt = str.join(STRING.NEWLINE, result)
        return txt

    @classmethod
    def print(cls, data, header='', footer='',
              width=80, width_limit=20, failure_msg='', print_func=None):
        """
        Print formatted data with optional header and footer.

        This method formats the given `data` into a readable string
        (using the same logic as `Printer.get`) and prints it directly
        to standard output or a custom print function. It is useful for
        displaying structured output such as lists, dictionaries, or
        tabular data in a human-readable way.

        Parameters
        ----------
        data : str, list
            a text or a list of text.
        header : str
            Text to prepend before the formatted data. Default is empty.
        footer : str
            Text to append after the formatted data. Default is empty.
        failure_msg : str
            Message to print if `data` is empty or invalid. Default is empty.
        width : int
            Maximum line width before wrapping. Default is 80.
        width_limit : int
            Maximum width of individual items before truncation. Default is 20.
        print_func : callable
            A custom print function to use instead of the built-in `print`.
            Must accept a single string argument. Default is None.

        Returns
        -------
        None
            This method prints the formatted output and does not return a value.

        Notes
        -----
        - Internally uses `Printer.get` to format the data before printing.
        - If `print_func` is provided, the formatted string is passed to it
          instead of being printed to stdout.
        """

        txt = Printer.get(data, header=header, footer=footer,
                          failure_msg=failure_msg, width=width,
                          width_limit=width_limit)

        print_func = print_func if callable(print_func) else print
        print_func(txt)

    @classmethod
    def get_message(cls, fmt, *args, style='format', prefix=''):
        """
        Construct a formatted message string with optional prefix.

        This method formats a message using either Python's new-style
        (`str.format`) or old-style (`%`) string interpolation. It allows
        flexible message construction with positional arguments and an
        optional prefix. If no arguments are provided, the format string
        itself is returned.

        Parameters
        ----------
        fmt : str
            The format string to interpolate. Can contain placeholders
            compatible with either `.format` or `%` depending on `style`.
        *args : arguments
            Positional arguments to substitute into the format string.
        style : str, optional
            The formatting style to use:
            - ``'format'`` : use `str.format` (default).
            - ``'%'``      : use old-style `%` interpolation.
        prefix : str, optional
            A string to prepend before the formatted message. If provided,
            it is followed by a space before the message. Default is empty.

        Returns
        -------
        str
            The formatted message string, optionally prefixed.
        """

        if args:
            message = fmt.format(*args) if style == 'format' else fmt % args
        else:
            message = fmt

        message = '{} {}'.format(prefix, message) if prefix else message
        return message

    @classmethod
    def print_message(cls, fmt, *args, style='format', prefix='', print_func=None):
        """
        Format and print a message with optional prefix.

        This method constructs a message string using either Python's
        new-style (`str.format`) or old-style (`%`) string interpolation,
        then prints it directly to standard output or a custom print
        function. It is useful for producing consistent, human-readable
        messages for logging, reporting, or user-facing output.

        Parameters
        ----------
        fmt : str
            The format string to interpolate. Can contain placeholders
            compatible with either `.format` or `%` depending on `style`.
        *args : arguments
            Positional arguments to substitute into the format string.
        style : str, optional
            The formatting style to use:
            - ``'format'`` : use `str.format` (default).
            - ``'%'``      : use old-style `%` interpolation.
        prefix : str, optional
            A string to prepend before the formatted message. If provided,
            it is followed by a space before the message. Default is empty.
        print_func : callable, optional
            A custom print function to use instead of the built-in `print`.
            Must accept a single string argument. Default is None.

        Returns
        -------
        None
            This method prints the formatted message and does not return a value.
        """
        message = cls.get_message(fmt, *args, style=style, prefix=prefix)
        print_func = print_func if callable(print_func) else print
        print_func(message)


class Misc:
    """
    General-purpose utility class for type checking and common data validations.

    The Misc class provides a collection of static or class methods
    that simplify working with Python’s built-in types. It is designed
    to reduce repetitive boilerplate code when verifying data structures
    or performing lightweight checks.

    Typical responsibilities include:
    - Determining whether an object is a list, dictionary, or string.
    - Providing safe type checks for dynamic or heterogeneous data.
    - Supporting other utility classes (e.g., MiscObject) by ensuring
      inputs are validated before processing.

    Methods
    -------
    is_list(obj)
        Return True if the given object is a list, False otherwise.
    is_dict(obj)
        Return True if the given object is a dictionary, False otherwise.
    is_string(obj)
        Return True if the given object is a string, False otherwise.

    Use Cases
    ---------
    - Validating inputs before performing transformations.
    - Ensuring data structures conform to expected types.
    - Supporting cleanup or copy operations in higher-level utilities.

    Notes
    -----
    This class is intended as a lightweight helper and does not
    perform deep type introspection. It focuses on common, high-level
    checks that are frequently needed in data processing workflows.
    """

    message = ''

    @classmethod
    def is_dict(cls, obj):
        """
        Check whether the given object is a dictionary.

        This method provides a safe and explicit type check to determine
        if the provided object is an instance of `dict`. It is useful for
        validating inputs before performing dictionary-specific operations
        such as key/value iteration or cleanup.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a dictionary, False otherwise.

        Examples
        --------
        >>> Misc.is_dict({"a": 1, "b": 2})
        True

        >>> Misc.is_dict([("a", 1), ("b", 2)])
        False

        >>> Misc.is_dict("not a dict")
        False
        """
        return isinstance(obj, typing.Dict)

    @classmethod
    def is_mapping(cls, obj):
        """
        Check whether the given object implements the mapping protocol.

        This method verifies if the provided object is an instance of
        `collections.abc.Mapping`, meaning it behaves like a dictionary
        or other mapping type (e.g., `dict`, `OrderedDict`, `defaultdict`).
        It is useful for validating inputs before performing operations
        that rely on key/value access.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a mapping type, False otherwise.

        Examples
        --------
        >>> from collections import OrderedDict
        >>> Misc.is_mapping({"a": 1, "b": 2})
        True

        >>> Misc.is_mapping(OrderedDict([("a", 1), ("b", 2)]))
        True

        >>> Misc.is_mapping([("a", 1), ("b", 2)])
        False

        >>> Misc.is_mapping("not a mapping")
        False
        """
        return isinstance(obj, typing.Mapping)

    @classmethod
    def is_list(cls, obj):
        """
        Check whether the given object is a list.

        This method provides a safe and explicit type check to determine
        if the provided object is an instance of `list`. It is useful for
        validating inputs before performing list-specific operations such
        as iteration, indexing, or cleanup.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a list, False otherwise.

        Examples
        --------
        >>> Misc.is_list([1, 2, 3])
        True

        >>> Misc.is_list("not a list")
        False

        >>> Misc.is_list({"a": 1, "b": 2})
        False
        """
        return isinstance(obj, typing.List)

    @classmethod
    def is_mutable_sequence(cls, obj):
        """
        Check whether the given object is a mutable sequence.

        This method verifies if the provided object is an instance of
        `collections.abc.MutableSequence`, meaning it supports sequence
        behavior (like lists) and allows modification of its contents.
        Examples of mutable sequences include `list`, `collections.deque`,
        and other custom sequence types that implement mutation methods.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a mutable sequence, False otherwise.

        Examples
        --------
        >>> Misc.is_mutable_sequence([1, 2, 3])
        True

        >>> from collections import deque
        >>> Misc.is_mutable_sequence(deque([1, 2, 3]))
        True

        >>> Misc.is_mutable_sequence((1, 2, 3))  # tuple is immutable
        False

        >>> Misc.is_mutable_sequence("abc")  # string is immutable
        False
        """
        return isinstance(obj, abc.MutableSequence)

    @classmethod
    def is_sequence(cls, obj):
        """
        Check whether the given object is a sequence.

        This method verifies if the provided object implements the
        `collections.abc.Sequence` interface, meaning it supports
        ordered element access by index and iteration. Examples of
        sequence types include `list`, `tuple`, `str`, and `range`.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a sequence type, False otherwise.

        Examples
        --------
        >>> Misc.is_sequence([1, 2, 3])
        True

        >>> Misc.is_sequence((1, 2, 3))
        True

        >>> Misc.is_sequence("abc")
        True

        >>> Misc.is_sequence({"a": 1, "b": 2})  # dict is not a sequence
        False

        >>> Misc.is_sequence(42)  # int is not a sequence
        False
        """
        return isinstance(obj, typing.Sequence)

    @classmethod
    def try_to_get_number(cls, obj, return_type=None):
        """
        Attempt to interpret the given object as a numeric value.

        This method tries to safely convert the provided object into a number.
        If the object is a string, it will be stripped and parsed as:
        - A boolean if the string is "true" or "false" (case-insensitive).
        - An integer if the string contains only digits.
        - A float if the string contains a decimal point.

        If the object is not a string, it checks whether the object is already
        a numeric type. If conversion fails, an error message is stored in
        `cls.message` and the original object is returned.

        Parameters
        ----------
        obj : Any
            The object to be converted into a number. Can be a string, int,
            float, bool, or other type.
        return_type : type, optional
            A target type to cast the result into. Must be one of {int, float, bool}.
            If not provided or not in the allowed list, the parsed result is returned
            as-is.

        Returns
        -------
        tuple
            A tuple of the form (success, value):
            - success : bool
                True if conversion succeeded, False otherwise.
            - value : int, float, bool, or Any
                The converted numeric value if successful, otherwise the original object.

        Examples
        --------
        >>> Misc.try_to_get_number("42")
        (True, 42)

        >>> Misc.try_to_get_number("3.14")
        (True, 3.14)

        >>> Misc.try_to_get_number("true")
        (True, True)

        >>> Misc.try_to_get_number("not a number")
        (False, 'not a number')

        >>> Misc.try_to_get_number(99, return_type=float)
        (True, 99.0)

        Notes
        -----
        - If conversion fails, `cls.message` will contain a descriptive error.
        - Only `int`, `float`, and `bool` are supported as explicit `return_type`.
        """
        chk_lst = [int, float, bool]

        if cls.is_string(obj):
            data = obj.strip()
            try:
                if data.lower() == 'true' or data.lower() == 'false':
                    result = True if data.lower() == 'true' else False
                else:
                    result = float(data) if '.' in data else int(data)

                num = return_type(result) if return_type in chk_lst else result
                return True, num
            except Exception as ex:     # noqa
                cls.message = Text(ex)
                return False, obj
        else:
            is_number = cls.is_number(obj)
            num = return_type(obj) if return_type in chk_lst else obj

            if not is_number:
                txt = obj if cls.is_class(obj) else type(obj)
                cls.message = Text.format('Expecting number type, but got {}', txt) # noqa
            return is_number, num

    @classmethod
    def is_integer(cls, obj):
        """
        Check whether the given object is an integer.

        This method provides a safe and explicit type check to determine
        if the provided object is an instance of `int`. It is useful for
        validating inputs before performing integer-specific operations
        such as arithmetic, indexing, or range generation.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is an integer, False otherwise.

        Examples
        --------
        >>> Misc.is_integer(42)
        True

        >>> Misc.is_integer(-7)
        True

        >>> Misc.is_integer(3.14)
        False

        >>> Misc.is_integer("100")
        False

        >>> Misc.is_integer(True)  # bool is a subclass of int
        True
        """
        if isinstance(obj, int):
            return True
        elif cls.is_string(obj):
            chk = obj.strip().isdigit()
            return chk
        else:
            return False

    @classmethod
    def is_boolean(cls, obj):
        """
        Check whether the given object is a boolean value.

        This method provides a safe and explicit type check to determine
        if the provided object is an instance of `bool`. It is useful for
        validating inputs before performing boolean-specific operations
        such as conditional logic or flag handling.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a boolean (`True` or `False`), False otherwise.

        Examples
        --------
        >>> Misc.is_boolean(True)
        True

        >>> Misc.is_boolean(False)
        True

        >>> Misc.is_boolean(1)  # int is not strictly a bool
        False

        >>> Misc.is_boolean("true")
        False
        """
        if isinstance(obj, bool):
            return True
        elif cls.is_string(obj):
            val = obj.strip().lower()
            chk = val == 'true' or val == 'false'
            return chk
        elif cls.is_integer(obj):
            chk = int(obj) == 0 or int(obj) == 1
            return chk
        elif cls.is_float(obj):
            chk = float(obj) == 0 or float(obj) == 1
            return chk
        else:
            return False

    @classmethod
    def is_float(cls, obj):
        """
        Check whether the given object is a floating-point number.

        This method provides a safe and explicit type check to determine
        if the provided object is an instance of `float`. It is useful for
        validating inputs before performing float-specific operations such
        as division, rounding, or mathematical computations requiring
        decimal precision.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a float, False otherwise.

        Examples
        --------
        >>> Misc.is_float(3.14)
        True

        >>> Misc.is_float(-0.001)
        True

        >>> Misc.is_float(42)
        False

        >>> Misc.is_float("3.14")
        False

        >>> Misc.is_float(True)  # bool is not a float
        False
        """
        if isinstance(obj, (float, int)):
            return True
        elif cls.is_string(obj):
            try:
                float(obj)
                return True
            except Exception as ex:     # noqa
                return False
        else:
            return False

    @classmethod
    def is_number(cls, obj):
        """
        Check whether the given object is a numeric type.

        This method provides a safe and explicit type check to determine
        if the provided object is an instance of a number type in Python.
        Supported numeric types include `int`, `float`, and `bool`
        (since `bool` is a subclass of `int`). It is useful for validating
        inputs before performing arithmetic or other number-specific
        operations.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a number type (int, float, or bool),
            False otherwise.

        Examples
        --------
        >>> Misc.is_number(42)
        True

        >>> Misc.is_number(3.14)
        True

        >>> Misc.is_number(True)  # bool is considered numeric
        True

        >>> Misc.is_number("100")
        False

        >>> Misc.is_number([1, 2, 3])
        False
        """
        result = cls.is_boolean(obj)
        result |= cls.is_integer(obj)
        result |= cls.is_float(obj)
        return result

    @classmethod
    def is_string(cls, obj):
        """
        Check whether the given object is a string.

        This method provides a safe and explicit type check to determine
        if the provided object is an instance of `str`. It is useful for
        validating inputs before performing string-specific operations
        such as concatenation, formatting, or text parsing.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a string, False otherwise.

        Examples
        --------
        >>> Misc.is_string("hello")
        True

        >>> Misc.is_string("")
        True

        >>> Misc.is_string(123)
        False

        >>> Misc.is_string(["a", "b", "c"])
        False

        >>> Misc.is_string(b"bytes")  # bytes is not str
        False
        """
        return isinstance(obj, typing.Text)

    @classmethod
    def is_class(cls, obj):
        """
        Check whether the given object is a class definition.

        This method determines if the provided object is a Python class
        (i.e., created using the `class` keyword) rather than an instance
        of a class or another type. It is useful for validating inputs
        before performing operations that require class objects, such as
        dynamic instantiation or reflection.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a class, False otherwise.

        Examples
        --------
        >>> class Example:
        ...     pass
        >>> Misc.is_class(Example)
        True

        >>> Misc.is_class(Example())
        False

        >>> Misc.is_class(int)
        True

        >>> Misc.is_class(42)
        False
        """
        return isinstance(obj, typing.Type)     # noqa

    @classmethod
    def is_callable(cls, obj):
        """
        Check whether the given object is callable.

        This method determines if the provided object can be called like
        a function, i.e., if it implements the `__call__` method. Callable
        objects include functions, methods, classes (which can be instantiated),
        and instances of classes that define `__call__`.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is callable, False otherwise.

        Examples
        --------
        >>> Misc.is_callable(len)  # built-in function
        True

        >>> class Example:
        ...     def __call__(self):
        ...         return "called"
        >>> Misc.is_callable(Example)
        True
        >>> Misc.is_callable(Example())
        True

        >>> Misc.is_callable(42)  # integers are not callable
        False

        >>> Misc.is_callable("hello")  # strings are not callable
        False
        """
        return isinstance(obj, typing.Callable)

    @classmethod
    def is_iterator(cls, obj):
        """
        Check whether the given object is an iterator.

        This method determines if the provided object implements the
        iterator protocol, meaning it defines both `__iter__()` and
        `__next__()` methods. Iterators produce elements one at a time
        and are consumed as they are iterated over. Unlike sequences,
        iterators do not support indexing or re-use once exhausted.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is an iterator, False otherwise.

        Examples
        --------
        >>> numbers = iter([1, 2, 3])
        >>> Misc.is_iterator(numbers)
        True

        >>> Misc.is_iterator([1, 2, 3])  # list is iterable but not an iterator
        False

        >>> Misc.is_iterator("abc")  # string is iterable but not an iterator
        False

        >>> def gen():
        ...     yield 1
        ...     yield 2
        >>> g = gen()
        >>> Misc.is_iterator(g)  # generator is an iterator
        True
        """
        return isinstance(obj, typing.Iterator)

    @classmethod
    def is_generator(cls, obj):
        """
        Check whether the given object is a generator.

        This method determines if the provided object is a generator object,
        meaning it was created by a generator function (using the `yield`
        keyword) or by calling `iter()` on a generator expression. Generators
        implement the iterator protocol and produce values lazily, one at a
        time, until exhausted.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a generator, False otherwise.

        Examples
        --------
        >>> def gen():
        ...     yield 1
        ...     yield 2
        >>> g = gen()
        >>> Misc.is_generator(g)
        True

        >>> Misc.is_generator((x for x in range(3)))  # noqa
        True

        >>> Misc.is_generator([1, 2, 3])  # list is iterable but not a generator
        False

        >>> Misc.is_generator(iter([1, 2, 3]))  # iterator but not a generator
        False
        """
        return isinstance(obj, typing.Generator)

    @classmethod
    def is_iterable(cls, obj):
        """
        Check whether the given object is iterable.

        This method determines if the provided object implements the
        iterable protocol, meaning it defines an `__iter__()` method
        or supports iteration in a `for` loop. Iterables include
        sequences (like lists, tuples, and strings), sets, dictionaries,
        generators, and custom objects that implement `__iter__`.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is iterable, False otherwise.

        Examples
        --------
        >>> Misc.is_iterable([1, 2, 3])  # list
        True

        >>> Misc.is_iterable((1, 2, 3))  # tuple
        True

        >>> Misc.is_iterable("abc")  # string
        True

        >>> Misc.is_iterable({"a": 1, "b": 2})  # dictionary
        True

        >>> def gen():
        ...     yield 1
        ...     yield 2
        >>> Misc.is_iterable(gen())  # generator
        True

        >>> Misc.is_iterable(42)  # integer is not iterable
        False
        """
        return isinstance(obj, typing.Iterable)

    @classmethod
    def is_none_type(cls, obj):
        """
        Check whether the given object is of type `None`.

        This method determines if the provided object is explicitly
        the `None` singleton in Python. It is useful for validating
        inputs before performing operations that require a non-null
        value, or for distinguishing between `None` and other falsy
        values such as `0`, `False`, or empty collections.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is `None`, False otherwise.

        Examples
        --------
        >>> Misc.is_none_type(None)
        True

        >>> Misc.is_none_type("hello")
        False

        >>> Misc.is_none_type(0)  # zero is falsy but not None
        False

        >>> Misc.is_none_type(False)  # boolean False is not None
        False

        >>> Misc.is_none_type([])  # empty list is not None
        False
        """
        return isinstance(obj, type(None))

    @classmethod
    def is_string_or_none(cls, obj):
        """
        Check whether the given object is either a string or `None`.

        This method determines if the provided object is an instance of
        `str` or explicitly the `None` singleton. It is useful for validating
        inputs that are expected to be optional strings, such as configuration
        values, user input fields, or text attributes that may be unset.

        Parameters
        ----------
        obj : Any
            The object to be tested.

        Returns
        -------
        bool
            True if the object is a string or `None`, False otherwise.

        Examples
        --------
        >>> Misc.is_string_or_none("hello")
        True

        >>> Misc.is_string_or_none(None)
        True

        >>> Misc.is_string_or_none("")
        True

        >>> Misc.is_string_or_none(123)
        False

        >>> Misc.is_string_or_none(["a", "b"])
        False
        """
        return isinstance(obj, (type(None), str))

    @classmethod
    def join_string(cls, *args, **kwargs):
        """
        Join a list of arguments into a single string.

        This method concatenates the list of arguments into a string,
        separated by the specified seperator or sep. It optionally skips `None`
        values to avoid inserting unwanted text. Non-string elements are
        converted to strings before joining.

        Parameters
        ----------
        args : list of arguments
            A collection of arguments to be joined.
        kwargs : keyword arguments
            keyword can be separator or sep
            The string used to separate items in the result. Defaults to "".

        Returns
        -------
        str
            A single string containing all items joined by the delimiter.

        Examples
        --------
        >>> Misc.join_string("apple", "banana", "cherry")       # noqa
        'applebananacherry'

        >>> Misc.join_string(1, 2, 3, separator=" - ")          # noqa
        '1 - 2 - 3'

        >>> Misc.join_string("a", None, "b", sep=", ")          # noqa
        'a, None, b'
        """
        if not args:
            return ''
        if len(args) == 1:
            return str(args[0])

        sep = kwargs.get('separator', '')
        sep = kwargs.get('sep', sep)
        return str.join(sep, [str(item) for item in args])

    @classmethod
    def indent_string(cls, *args, width=2):
        """
        Combine multiple string-like inputs and indent each line.

        This method accepts one or more arguments, converts them to strings,
        splits them into lines, and joins them into a single multi-line string.
        Each line is then indented by the specified number of spaces. If an
        argument is `None`, it is treated as an empty string.

        Parameters
        ----------
        *args : arguments
            One or more objects to be combined into a string. Each object is
            converted to a string and split into lines before joining.
        width : int, optional
            The number of spaces to prepend to each line. Negative values are
            treated as zero. Defaults to 2.

        Returns
        -------
        str
            A single string with all input lines joined and indented.

        Examples
        --------
        >>> Misc.indent_string("Hello", "World")
        '  Hello\n  World'

        >>> Misc.indent_string("Line1\\nLine2", width=4)
        '    Line1\n    Line2'

        >>> Misc.indent_string(None, "Text")
        '  Text'

        >>> Misc.indent_string("A", "B", "C", width=0)
        'A\nB\nC'
        """
        width = width if width >= 0 else 0
        lst = []
        for item in args:
            item = item or ''
            lst.extend(str(item).splitlines())

        data = str.join(STRING.NEWLINE, lst)
        result = indent(data, ' ' * width)
        return result

    @classmethod
    def indent_string_level2(cls, *args, width=2, start_pos=1, other_width=4):
        """
        Indent a multi-line string using two different indentation levels.

        This method combines one or more string-like inputs, splits them into
        lines, and applies indentation in two stages:
        - Lines before `start_pos` are indented by `width` spaces.
        - Lines from `start_pos` onward are indented by `other_width` spaces.

        If `start_pos` is 0 or `other_width` equals `width`, all lines are
        indented uniformly using `width`.

        Parameters
        ----------
        *args : arguments
            One or more objects to be combined into a string. Each object is
            converted to a string and split into lines before joining.
        width : int, optional
            The number of spaces used to indent the first block of lines.
            Defaults to 2. Negative values are treated as 0.
        start_pos : int, optional
            The line index (0-based) at which the second indentation level
            begins. Defaults to 1. Negative values are treated as 0.
        other_width : int, optional
            The number of spaces used to indent lines starting from `start_pos`.
            Must be greater than `width` to take effect; otherwise, `width`
            is applied uniformly. Defaults to 4.

        Returns
        -------
        str
            A single string with lines indented according to the specified
            two-level indentation scheme.
        """
        start_pos = start_pos if start_pos >= 0 else 0
        other_width = other_width if other_width > width else width

        if start_pos == 0 or other_width == width:
            result = cls.indent_string(*args, width=width)
            return result

        lines = cls.indent_string(*args, width=0).splitlines()

        txt1 = indent(str.join(STRING.NEWLINE, lines[:start_pos]), ' ' * width)
        txt2 = indent(str.join(STRING.NEWLINE, lines[start_pos:]), ' ' * other_width)
        result = '%s\n%s' % (txt1, txt2)
        return result

    @classmethod
    def is_string_multiline(cls, txt):
        """
        Check whether the given object is a multi-line string.

        This method first verifies that the input is a string. If so, it
        determines whether the string contains more than one line by
        splitting on line breaks. It is useful for distinguishing between
        single-line and multi-line text inputs, such as when formatting,
        validating, or processing user-provided text.

        Parameters
        ----------
        txt : Any
            The object to be tested. Must be a string to be considered.

        Returns
        -------
        bool
            True if the object is a string containing more than one line,
            False otherwise.
        """
        if not cls.is_string(txt):
            return False
        lines_count = len(txt.splitlines())
        return lines_count > 1

    @classmethod
    def skip_first_line(cls, data):
        """
        Return the input string with its first line removed.

        This method checks whether the input is a string. If so, it removes
        the first line and returns the remaining content joined with newline
        characters. If the input is not a string, it is returned unchanged.
        Useful for processing multi-line text where the first line is a header,
        title, or metadata that should be excluded.

        Parameters
        ----------
        data : Any
            The object to be processed. If not a string, it is returned as-is.

        Returns
        -------
        Any
            The input string without its first line, or the original object
            if it is not a string.
        """
        if not cls.is_string(data):
            return data
        else:
            new_data = str.join(STRING.NEWLINE, data.splitlines()[1:])
            return new_data

    @classmethod
    def is_window_os(cls):
        """
        Check whether the current operating system is Windows.

        This method inspects the runtime environment to determine if the
        underlying operating system is a Microsoft Windows platform. It is
        useful for writing cross-platform code that requires conditional
        behavior depending on the OS, such as file path handling, shell
        commands, or environment-specific configurations.

        Returns
        -------
        bool
            True if the current operating system is Windows, False otherwise.

        Examples
        --------
        >>> Misc.is_window_os()
        True   # when running on Windows

        >>> Misc.is_window_os()
        False  # when running on Linux, macOS, or other platforms
        """
        chk = platform.system().lower() == 'windows'
        return chk

    @classmethod
    def is_mac_os(cls):
        """
        Check whether the current operating system is macOS.

        This method inspects the runtime environment to determine if the
        underlying operating system is Apple macOS. It is useful for writing
        cross-platform code that requires conditional behavior depending on
        the OS, such as file path handling, shell commands, or environment-
        specific configurations.

        Returns
        -------
        bool
            True if the current operating system is macOS, False otherwise.

        Examples
        --------
        >>> Misc.is_mac_os()
        True   # when running on macOS

        >>> Misc.is_mac_os()
        False  # when running on Windows, Linux, or other platforms
        """
        chk = platform.system().lower() == 'darwin'
        return chk

    @classmethod
    def is_linux_os(cls):
        """
        Check whether the current operating system is Linux.

        This method inspects the runtime environment to determine if the
        underlying operating system is a Linux distribution. It is useful
        for writing cross-platform code that requires conditional behavior
        depending on the OS, such as file path handling, shell commands,
        or environment-specific configurations.

        Returns
        -------
        bool
            True if the current operating system is Linux, False otherwise.

        Examples
        --------
        >>> Misc.is_linux_os()
        True   # when running on Ubuntu, Fedora, Debian, etc.

        >>> Misc.is_linux_os()
        False  # when running on Windows, macOS, or other platforms
        """
        chk = platform.system().lower() == 'linux'
        return chk

    @classmethod
    def is_nix_os(cls):
        """
        Check whether the current operating system is Unix-like.

        This method inspects the runtime environment to determine if the
        underlying operating system belongs to the family of Unix-like systems,
        such as Linux or macOS. It is useful for writing cross-platform code
        that requires conditional behavior depending on whether the OS follows
        POSIX/Unix conventions (e.g., file paths, shell commands, permissions).

        Returns
        -------
        bool
            True if the current operating system is Unix-like (Linux or macOS),
            False otherwise.

        Examples
        --------
        >>> Misc.is_nix_os()
        True   # when running on Linux or macOS

        >>> Misc.is_nix_os()
        False  # when running on Windows or other non-Unix platforms
        """
        chk = cls.is_linux_os() or cls.is_mac_os()
        return chk

    @classmethod
    def escape_double_quote(cls, data):
        """
        Escape double quotes in a string.

        This method checks whether the input is a string. If so, it replaces
        all occurrences of the double quote character (`"`) with its escaped
        form (`\"`). If the input is not a string, it is returned unchanged.
        This is useful when preparing text for contexts where unescaped quotes
        would cause parsing errors, such as JSON, command-line arguments, or
        embedding strings inside other quoted text.

        Parameters
        ----------
        data : Any
            The object to process. If not a string, it is returned as-is.

        Returns
        -------
        Any
            A new string with double quotes escaped, or the original object
            if it is not a string.

        Examples
        --------
        >>> Misc.escape_double_quote('She said "Hello"')
        'She said \\\"Hello\\\"'

        >>> Misc.escape_double_quote("No quotes here")
        'No quotes here'

        >>> Misc.escape_double_quote(123)
        123  # non-string input returned unchanged

        >>> Misc.escape_double_quote(None)
        None
        """
        if not isinstance(data, str):
            return data
        new_data = data.replace('"', '\\"')
        return new_data

    @classmethod
    def escape_single_quote(cls, data):
        """
        Escape single quotes in a string.

        This method checks whether the input is a string. If so, it replaces
        all occurrences of the single quote character (`'`) with its escaped
        form (`\\'`). If the input is not a string, it is returned unchanged.
        This is useful when preparing text for contexts where unescaped single
        quotes would cause parsing errors, such as SQL queries, command-line
        arguments, or embedding strings inside other quoted text.

        Parameters
        ----------
        data : Any
            The object to process. If not a string, it is returned as-is.

        Returns
        -------
        Any
            A new string with single quotes escaped, or the original object
            if it is not a string.

        Examples
        --------
        >>> Misc.escape_single_quote("It's fine")
        'It\\'s fine'

        >>> Misc.escape_single_quote("No quotes here")
        'No quotes here'

        >>> Misc.escape_single_quote(123)
        123  # non-string input returned unchanged

        >>> Misc.escape_single_quote(None)
        None
        """
        if not isinstance(data, str):
            return data
        new_data = data.replace("'", "\\'")
        return new_data

    @classmethod
    def escape_quote(cls, data):
        """
        Escape single and double quotes in a string.

        This method checks whether the input is a string. If so, it replaces
        all occurrences of single quotes (`'`) and double quotes (`"`) with
        their escaped forms (`\\'` and `\\\"`). If the input is not a string,
        it is returned unchanged. This is useful when preparing text for
        contexts where unescaped quotes would cause parsing errors, such as
        JSON serialization, SQL queries, command-line arguments, or embedding
        strings inside other quoted text.

        Parameters
        ----------
        data : Any
            The object to process. If not a string, it is returned as-is.

        Returns
        -------
        Any
            A new string with single and double quotes escaped, or the original
            object if it is not a string.

        Examples
        --------
        >>> Misc.escape_quote("She said 'Hello' and \"Hi\"")    # noqa
        'She said \\\'Hello\\\' and \\\"Hi\\\"'

        >>> Misc.escape_quote("No quotes here")
        'No quotes here'

        >>> Misc.escape_quote(123)
        123  # non-string input returned unchanged

        >>> Misc.escape_quote(None)
        None
        """
        if not isinstance(data, str):
            return data
        new_data = re.sub('([\'"])', r'\\\1', data)
        return new_data

    @classmethod
    def get_first_char(cls, data, to_string=True, on_failure=False):
        """
        Retrieve the first character of the given input.

        This method attempts to return the first character of the provided
        data. If the input is a string, the first character is returned
        directly. If the input is not a string:

        - If `to_string=True`, the input is converted to a string and its
          first character is returned.
        - If `to_string=False` and `on_failure=True`, an exception is raised
          indicating that the input must be a string or `to_string=True`.
        - If `to_string=False` and `on_failure=False`, an empty string is
          returned.

        Parameters
        ----------
        data : Any
            The object from which to extract the first character.
        to_string : bool, optional
            Whether to convert non-string input to a string before extracting
            the first character. Defaults to True.
        on_failure : bool, optional
            Whether to raise an exception if the input is not a string and
            `to_string=False`. Defaults to False.

        Returns
        -------
        str
            The first character of the input (string or converted string),
            or an empty string if extraction is not possible.

        Raises
        ------
        Exception
            If `data` is not a string, `to_string=False`, and `on_failure=True`.

        Examples
        --------
        >>> Misc.get_first_char("Hello")
        'H'

        >>> Misc.get_first_char(123)
        '1'  # converted to string

        >>> Misc.get_first_char(123, to_string=False)
        ''   # non-string input, no conversion

        >>> Misc.get_first_char(123, to_string=False, on_failure=True)
        Traceback (most recent call last):
            ...
        Exception: Type of this data is 'int'.  Data must be string type or to_string=True

        >>> Misc.get_first_char("")
        ''   # empty string has no first character
        """
        if cls.is_string(data):
            result = data[:1]
            return result
        else:
            if to_string:
                txt = str(data)
                result = txt[:1]
                return result
            else:
                if on_failure:
                    fmt = ('Type of this data is %r.  Data must '
                           'be string type or to_string=True')
                    cls_name = data.__name__ if cls.is_class(data) else type(data).__name__
                    failure = fmt % cls_name
                    raise Exception(failure)
                else:
                    return ''

    @classmethod
    def get_last_char(cls, data, to_string=True, on_failure=False):
        """
        Retrieve the last character of the given input.

        This method attempts to return the last character of the provided
        data. If the input is a string, the last character is returned
        directly. If the input is not a string:

        - If `to_string=True`, the input is converted to a string and its
          last character is returned.
        - If `to_string=False` and `on_failure=True`, an exception is raised
          indicating that the input must be a string or `to_string=True`.
        - If `to_string=False` and `on_failure=False`, an empty string is
          returned.

        Parameters
        ----------
        data : Any
            The object from which to extract the last character.
        to_string : bool, optional
            Whether to convert non-string input to a string before extracting
            the last character. Defaults to True.
        on_failure : bool, optional
            Whether to raise an exception if the input is not a string and
            `to_string=False`. Defaults to False.

        Returns
        -------
        str
            The last character of the input (string or converted string),
            or an empty string if extraction is not possible.

        Raises
        ------
        Exception
            If `data` is not a string, `to_string=False`, and `on_failure=True`.

        Examples
        --------
        >>> Misc.get_last_char("Hello")
        'o'

        >>> Misc.get_last_char(123)
        '3'  # converted to string

        >>> Misc.get_last_char(123, to_string=False)
        ''   # non-string input, no conversion

        >>> Misc.get_last_char(123, to_string=False, on_failure=True)
        Traceback (most recent call last):
            ...
        Exception: Type of this data is 'int'.  Data must be string type or to_string=True

        >>> Misc.get_last_char("")
        ''   # empty string has no last character
        """
        if cls.is_string(data):
            result = data[-1:]
            return result
        else:
            if to_string:
                txt = str(data)
                result = txt[-1:]
                return result
            else:
                if on_failure:
                    fmt = ('Type of this data is %r.  Data must '
                           'be string type or to_string=True')
                    cls_name = data.__name__ if cls.is_class(data) else type(data).__name__
                    failure = fmt % cls_name
                    raise Exception(failure)
                else:
                    return ''

    @classmethod
    def get_clock_tick_str(cls, precision=10, dot_replaced='_',
                           prefix='', postfix=''):
        """
        Generate a string representation of the current clock tick (Unix timestamp).

        This method retrieves the current system time in seconds since the epoch
        (`time.time()`), formats it as a floating-point number with the specified
        precision, and returns it as a string. The decimal point can be replaced
        with a custom character, and optional prefix and postfix strings can be
        added to the result. This is useful for generating unique identifiers,
        filenames, or log entries based on precise timestamps.

        Parameters
        ----------
        precision : int, optional
            Number of decimal places to include in the timestamp string.
            Defaults to 10.
        dot_replaced : str, optional
            Character used to replace the decimal point in the timestamp.
            Defaults to an underscore ("_").
        prefix : str, optional
            String to prepend to the timestamp. Defaults to an empty string.
        postfix : str, optional
            String to append to the timestamp. Defaults to an empty string.

        Returns
        -------
        str
            A formatted string representing the current clock tick with
            precision, decimal replacement, and optional prefix/postfix applied.

        Examples
        --------
        >>> Misc.get_clock_tick_str()
        '1734462345_1234567890'  # example output with default settings

        >>> Misc.get_clock_tick_str(precision=5, dot_replaced='-')
        '1734462345-12345'

        >>> Misc.get_clock_tick_str(prefix='ID_', postfix='_END')
        'ID_1734462345_1234567890_END'

        >>> Misc.get_clock_tick_str(precision=3)
        '1734462345_123'
        """
        clock_tick_str = '%.*f' % (precision, time())
        clock_tick_str = clock_tick_str.replace(STRING.DOT_CHAR, dot_replaced)
        clock_tick_str = '%s%s' % (prefix, clock_tick_str) if prefix else clock_tick_str
        clock_tick_str = '%s%s' % (clock_tick_str, postfix) if postfix else clock_tick_str
        return clock_tick_str

    @classmethod
    def get_uniq_number_str(cls):
        """
        Generate a unique numeric string based on the current clock tick.

        This method calls `get_clock_tick_str()` to produce a string
        representation of the current system time (Unix timestamp with
        fractional seconds). Because system time is always increasing,
        the returned value can be used as a unique identifier for
        filenames, log entries, or other contexts where uniqueness is
        required.

        Returns
        -------
        str
            A string representation of the current clock tick, suitable
            for use as a unique identifier.

        Examples
        --------
        >>> Misc.get_uniq_number_str()
        '1734462345_1234567890'  # example output

        >>> id1 = Misc.get_uniq_number_str()
        >>> id2 = Misc.get_uniq_number_str()
        >>> id1 != id2
        True  # successive calls produce different values
        """
        uniq_str = cls.get_clock_tick_str()
        return uniq_str

    @classmethod
    def get_instance_class_name(cls, obj):
        """
        Retrieve the class name of an object's instance.

        This method inspects the given object and returns the name of its
        class as a string. It is useful for logging, debugging, or any
        situation where you need to identify the type of an object at
        runtime without directly referencing its class.

        Parameters
        ----------
        obj : Any
            The object whose class name should be retrieved.

        Returns
        -------
        str
            The name of the object's class.

        Examples
        --------
        >>> Misc.get_instance_class_name("hello")
        'str'

        >>> Misc.get_instance_class_name(123)
        'int'

        >>> class CustomClass:
        ...     pass
        >>> instance = CustomClass()
        >>> Misc.get_instance_class_name(instance)
        'CustomClass'
        """
        cls_name = obj.__class__.__name__
        return cls_name

    @classmethod
    def is_data_line(cls, line):
        """
        Check whether a line of text contains non-whitespace characters.

        This method converts the input to a string and evaluates whether it
        contains at least one non-whitespace character (letters, digits, or
        symbols). It is useful for distinguishing meaningful content from
        empty or whitespace-only lines when processing text data.

        Parameters
        ----------
        line : Any
            The input to be checked. It will be converted to a string before
            evaluation.

        Returns
        -------
        bool
            True if the line contains non-whitespace characters, False if the
            line is empty or consists only of whitespace.

        Examples
        --------
        >>> Misc.is_data_line("Hello World")
        True

        >>> Misc.is_data_line("    ")
        False  # only whitespace

        >>> Misc.is_data_line("")
        False  # empty string

        >>> Misc.is_data_line(None)
        True  # converted to "None", which contains letters

        >>> Misc.is_data_line(123)
        True  # converted to "123", which contains digits
        """
        chk = bool(re.search(r'\S+', str(line)))
        return chk

    @classmethod
    def get_list_of_lines(cls, *lines):
        """
        Convert one or more inputs into a list of text lines.

        This method takes any number of input values, converts each to a string
        (substituting an empty string if the value is None), and splits them into
        lines based on common newline delimiters (`\n`, `\r\n`, or `\r`). The
        resulting list contains all lines from all inputs. If the only result is
        a single empty string, it is normalized to an empty list.

        Parameters
        ----------
        *lines : Any
            One or more values to be processed. Each value is converted to a
            string (or treated as empty if None) before splitting into lines.

        Returns
        -------
        list of str
            A list of text lines derived from the input values. Returns an empty
            list if all inputs are None or empty.
        """
        result = []

        for line in lines:
            line = STRING.EMPTY if line is None else str(line)
            result.extend(re.split(r'\r?\n|\r', line))

        if result == [STRING.EMPTY]:
            result = []

        return result

    @classmethod
    def get_list_of_readonly_lines(cls, *lines):
        """
        Convert one or more inputs into a read-only sequence of text lines.

        This method takes any number of input values, converts each to a string
        (substituting an empty string if the value is None), and splits them into
        lines using common newline delimiters (`\n`, `\r\n`, or `\r`). The result
        is returned as a tuple, making the sequence immutable (read-only). This is
        useful when you want to ensure that the list of lines cannot be modified
        after creation, such as when passing data to functions that should not
        alter it.

        Parameters
        ----------
        *lines : Any
            One or more values to be processed. Each value is converted to a
            string (or treated as empty if None) before splitting into lines.

        Returns
        -------
        tuple of str
            An immutable sequence of text lines derived from the input values.
            Returns an empty tuple if all inputs are None or empty.
        """
        result = cls.get_list_of_lines(*lines)
        return tuple(result)

    @classmethod
    def get_leading_line(cls, line, start=None, end=None):
        """
        Extract the leading whitespace characters from a line of text.

        This method inspects the given input (converted to a string) and
        returns any leading spaces or tabs at the beginning of the specified
        substring range. Carriage returns (`\r`) and newlines (`\n`) are
        excluded from the match. If no leading whitespace is found, an empty
        string is returned.

        Parameters
        ----------
        line : Any
            The input to be checked. It will be converted to a string before
            evaluation.
        start : int, optional
            The starting index of the substring to evaluate. Defaults to None,
            meaning the beginning of the string.
        end : int, optional
            The ending index of the substring to evaluate. Defaults to None,
            meaning the end of the string.

        Returns
        -------
        str
            A string containing the leading whitespace characters (spaces or
            tabs) from the specified substring. Returns an empty string if no
            leading whitespace is present.

        Examples
        --------
        >>> Misc.get_leading_line("    indented text")
        '    '

        >>> Misc.get_leading_line("\t\tTabbed line")
        '\\t\\t'

        >>> Misc.get_leading_line("NoIndent")
        ''  # no leading whitespace

        >>> Misc.get_leading_line("   spaced text", start=1)
        ''  # substring starts at index 1, so no leading whitespace

        >>> Misc.get_leading_line(None)
        ''  # converted to "None", which has no leading whitespace
        """
        match = re.match(r'([^\S\r\n]+)?', str(line)[start:end])
        leading_spaces = match.group()
        return leading_spaces

    @classmethod
    def get_trailing_line(cls, line, start=None, end=None):
        """
        Extract the trailing whitespace characters from a line of text.

        This method converts the input to a string and inspects the specified
        substring range (defined by `start` and `end`). It returns any trailing
        spaces or tabs at the end of that substring. Carriage returns (`\r`) and
        newlines (`\n`) are excluded from the match. If no trailing whitespace
        is found, an empty string is returned.

        Parameters
        ----------
        line : Any
            The input to be checked. It will be converted to a string before
            evaluation.
        start : int, optional
            The starting index of the substring to evaluate. Defaults to None,
            meaning the beginning of the string.
        end : int, optional
            The ending index of the substring to evaluate. Defaults to None,
            meaning the end of the string.

        Returns
        -------
        str
            A string containing the trailing whitespace characters (spaces or
            tabs) from the specified substring. Returns an empty string if no
            trailing whitespace is present.

        Examples
        --------
        >>> Misc.get_trailing_line("text    ")
        '    '

        >>> Misc.get_trailing_line("Tabbed\t")
        '\\t'

        >>> Misc.get_trailing_line("NoTrailing")
        ''  # no trailing whitespace

        >>> Misc.get_trailing_line("abc   def   ", start=0, end=7)
        ''  # substring "abc   d" has no trailing whitespace

        >>> Misc.get_trailing_line(None)
        ''  # converted to "None", which has no trailing whitespace
        """
        match = re.search(r'([^\S\r\n]+)?$', str(line)[start:end])
        trailing_spaces = match.group()
        return trailing_spaces

    @classmethod
    def is_leading_line(cls, line, start=None, end=None):
        """
        Determine whether a line of text is a data line with leading whitespace.

        This method checks if the given input (converted to a string) contains
        non-whitespace characters (i.e., it is not blank) and also begins with
        leading spaces or tabs. Carriage returns (`\r`) and newlines (`\n`) are
        excluded from the leading whitespace check. If the input is not a string,
        the method returns False.

        Parameters
        ----------
        line : Any
            The input to be checked. Must be a string or convertible to a string.
        start : int, optional
            The starting index of the substring to evaluate. Defaults to None,
            meaning the beginning of the string.
        end : int, optional
            The ending index of the substring to evaluate. Defaults to None,
            meaning the end of the string.

        Returns
        -------
        bool
            True if the line contains non-whitespace characters and begins with
            leading spaces or tabs. False otherwise.

        Examples
        --------
        >>> Misc.is_leading_line("    indented text")
        True  # has leading spaces and non-whitespace content

        >>> Misc.is_leading_line("NoIndent")
        False  # no leading whitespace

        >>> Misc.is_leading_line("    ")
        False  # only whitespace, no data

        >>> Misc.is_leading_line("")
        False  # empty string

        >>> Misc.is_leading_line(None)
        False  # not a string

        >>> Misc.is_leading_line("   spaced text", start=1)
        False  # substring starts at index 1, so no leading whitespace
        """
        if not Misc.is_string(line):
            return False

        leading_spaces = cls.get_leading_line(line, start=start, end=end)
        is_leading = leading_spaces != STRING.EMPTY
        is_data_line = line.strip() != STRING.EMPTY
        chk = is_data_line and is_leading
        return chk

    @classmethod
    def is_trailing_line(cls, line, start=None, end=None):
        """
        Determine whether a line of text is a data line with trailing whitespace.

        This method checks if the given input is a string and evaluates whether
        it contains non-whitespace characters (i.e., it is not blank) and also
        ends with trailing spaces or tabs. Carriage returns (`\r`) and newlines
        (`\n`) are excluded from the trailing whitespace check. If the input is
        not a string, the method returns False.

        Parameters
        ----------
        line : Any
            The input to be checked. Must be a string or convertible to a string.
        start : int, optional
            The starting index of the substring to evaluate. Defaults to None,
            meaning the beginning of the string.
        end : int, optional
            The ending index of the substring to evaluate. Defaults to None,
            meaning the end of the string.

        Returns
        -------
        bool
            True if the line contains non-whitespace characters and ends with
            trailing spaces or tabs. False otherwise.

        Examples
        --------
        >>> Misc.is_trailing_line("text    ")
        True  # has trailing spaces and non-whitespace content

        >>> Misc.is_trailing_line("NoTrailing")
        False  # no trailing whitespace

        >>> Misc.is_trailing_line("    ")
        False  # only whitespace, no data

        >>> Misc.is_trailing_line("")
        False  # empty string

        >>> Misc.is_trailing_line(None)
        False  # not a string

        >>> Misc.is_trailing_line("abc   def   ", start=0, end=7)
        False  # substring "abc   d" has no trailing whitespace
        """
        if not Misc.is_string(line):
            return False

        trailing_spaces = cls.get_trailing_line(line, start=start, end=end)
        is_trailing = trailing_spaces != STRING.EMPTY
        is_data_line = line.strip() != STRING.EMPTY
        chk = is_data_line and is_trailing
        return chk

    @classmethod
    def is_whitespace_in_line(cls, line):
        """
        Check whether a line of text contains internal whitespace sequences.

        This method inspects the given input (if it is a string) and searches
        for sequences of whitespace characters (spaces, tabs, etc.). It then
        evaluates whether any of those sequences contain characters other than
        spaces, carriage returns (`\r`), or newlines (`\n`). If so, the method
        returns True. If the input is not a string, or no qualifying whitespace
        sequences are found, it returns False.

        Parameters
        ----------
        line : Any
            The input to be checked. Must be a string; otherwise, the method
            returns False.

        Returns
        -------
        bool
            True if the line contains at least one whitespace sequence that
            includes characters beyond simple spaces, carriage returns, or
            newlines. False otherwise.

        Examples
        --------
        >>> Misc.is_whitespace_in_line("Hello World")
        True  # contains a space between words

        >>> Misc.is_whitespace_in_line("Tabbed\tText")
        True  # contains a tab character

        >>> Misc.is_whitespace_in_line("NoWhitespaceHere")
        False  # no whitespace at all

        >>> Misc.is_whitespace_in_line("    ")
        False  # only spaces, no data

        >>> Misc.is_whitespace_in_line("")
        False  # empty string

        >>> Misc.is_whitespace_in_line(None)
        False  # not a string
        """
        if not Misc.is_string(line):
            return False

        lst_of_ws = re.findall(r'\s+', line)
        if lst_of_ws:
            chk = any(bool(re.search(r'[^ \r\n]+', ws)) for ws in lst_of_ws)
            return chk
        else:
            return False


class MiscOutput:
    """
    Utility class for executing shell commands and capturing results.

    MiscOutput provides a structured way to run system commands from
    within Python and collect their output, exit code, and success
    status in a convenient `DotObject`. This makes it easier to
    integrate shell execution into applications without manually
    handling subprocess details.

    Methods
    -------
    execute_shell_command(cmdline)
        Run a shell command, capture its output and exit code, and
        return a `DotObject` containing:
        - output : str
            The captured stdout/stderr text from the command.
        - exit_code : int
            The numeric exit status returned by the shell.
        - is_success : bool
            True if the exit code equals `ECODE.SUCCESS`, False otherwise.

    Use Cases
    ---------
    - Automating system tasks from Python.
    - Capturing command output for logging or diagnostics.
    - Checking success/failure of shell operations in a structured way.
    """
    @classmethod
    def execute_shell_command(cls, cmdline):
        """
        Execute a shell command and capture its result.

        This method runs the specified command line string in the system shell
        using `subprocess.getstatusoutput`. It collects both the exit code and
        the command's output, then wraps them in a `DotObject` for convenient
        access. A success flag is also included for quick checks.

        Parameters
        ----------
        cmdline : str
            The shell command to execute, provided as a single string.

        Returns
        -------
        DotObject
            An object containing:
            - output : str
                The captured stdout and stderr output from the command.
            - exit_code : int
                The exit status code returned by the shell.
            - is_success : bool
                True if the exit code equals `ECODE.SUCCESS`, False otherwise.

        Examples
        --------
        >>> result = MiscOutput.execute_shell_command("echo Hello")     # noqa
        >>> result.output
        'Hello'
        >>> result.exit_code
        0
        >>> result.is_success
        True

        Notes
        -----
        - This method is useful for programmatically running shell commands
          while capturing their results in a structured way.
        - The `is_success` flag depends on the definition of `ECODE.SUCCESS`
          in your environment (commonly 0).
        """
        exit_code, output = subprocess.getstatusoutput(cmdline)
        result = DotObject(
            output=output,                          # noqa
            exit_code=exit_code,                    # noqa
            is_success=exit_code == ECODE.SUCCESS   # noqa
        )
        return result


class MiscPlatform:
    """
    Utility class for retrieving platform and Python environment information.

    MiscPlatform provides helper methods to query details about the
    underlying operating system kernel, the current Python runtime,
    and the official documentation URL for the active Python version.
    These methods are useful for logging, diagnostics, or displaying
    environment metadata in applications.

    Methods
    -------
    get_kernel_info()
        Return a string containing the operating system name and kernel
        release version (e.g., "Linux 5.15.0").
    get_python_info()
        Return a string with the current Python interpreter version
        (e.g., "Python 3.11.6").
    get_python_docs_url()
        Return the URL to the official Python documentation site for
        the current major and minor version (e.g.,
        "https://docs.python.org/3.11/").
    """
    @classmethod
    def get_kernel_info(cls):
        """
        Retrieve basic operating system kernel information.

        This method queries the underlying platform using
        `platform.uname()` and returns a string containing the
        system name and kernel release version. It is useful for
        logging, diagnostics, or displaying environment metadata.

        Returns
        -------
        str
            A string in the format "<system> <release>", where:
            - <system> is the operating system name (e.g., "Linux",
              "Windows", "Darwin").
            - <release> is the kernel or OS release version
              (e.g., "5.15.0", "10.0.22621").

        Examples
        --------
        >>> MiscPlatform.get_kernel_info()
        'Linux 5.15.0'

        >>> MiscPlatform.get_kernel_info()
        'Windows 10.0.22621'
        """
        result = '{0.system} {0.release}'.format(platform.uname())
        return result

    @classmethod
    def get_python_info(cls):
        """
        Retrieve the current Python interpreter version.

        This method queries the runtime environment using
        `platform.python_version()` and returns a string that
        identifies the active Python version. It is useful for
        logging, diagnostics, or displaying environment metadata
        in applications.

        Returns
        -------
        str
            A string in the format "Python <version>", where
            <version> is the full version number (e.g., "3.11.6").

        Examples
        --------
        >>> MiscPlatform.get_python_info()
        'Python 3.11.6'
        """
        result = 'Python {}'.format(platform.python_version())
        return result

    @classmethod
    def get_python_docs_url(cls):
        """
        Retrieve the official Python documentation URL for the current runtime version.

        This method constructs a URL pointing to the Python documentation site
        that matches the major and minor version of the interpreter currently
        in use. It ensures that developers are directed to the correct set of
        docs for their environment.

        Returns
        -------
        str
            A URL string in the format:
            "https://docs.python.org/<major>.<minor>/"
            where <major> and <minor> correspond to the active Python version.

        Examples
        --------
        >>> MiscPlatform.get_python_docs_url()
        'https://docs.python.org/3.11/'

        Notes
        -----
        - The patch version (e.g., 3.11.6) is not included in the URL.
        - Useful for linking users directly to the correct documentation
          for their Python environment.
        """
        fmt = 'https://docs.python.org/{0.major}.{0.minor}/'
        result = fmt.format(sys.version_info)
        return result


class MiscFunction:
    """
    Utility class for function invocation and dynamic error handling.

    MiscFunction provides helper methods for safely invoking callables
    while capturing their output, as well as for creating and raising
    custom runtime errors. It is designed to simplify scenarios where
    you need to:
    - Execute a function without polluting the console with stdout/stderr.
    - Capture and optionally persist the output and error streams.
    - Dynamically generate exception classes tied to specific objects.

    Methods
    -------
    do_silent_invoke(callable_obj, *args, filename='', **kwargs)
        Invoke a callable while suppressing stdout/stderr, capture its
        output and error streams, and return a DotObject containing
        the result and captured text. Optionally write combined output
        and error to a file.
    create_runtime_error(obj=None, msg='')
        Dynamically create a custom Exception subclass based on the
        provided object and return an instance with the given message.
    raise_runtime_error(obj=None, msg='')
        Raise a dynamically created runtime error with the specified
        message, using `create_runtime_error` internally.
    """
    @classmethod
    def do_silent_invoke(cls, callable_obj, *args, filename='', **kwargs):
        """
        Invoke a callable while capturing and suppressing its stdout/stderr output.

        This method executes the given callable object with the provided arguments,
        redirecting `sys.stdout` and `sys.stderr` to in-memory buffers so that any
        printed output or error messages are captured instead of displayed. The
        captured streams, along with the callable's return value, are packaged into
        a `DotObject` for convenient access.

        Optionally, the combined output and error text can be written to a file.

        Parameters
        ----------
        callable_obj : Callable
            The function or callable object to be invoked.
        *args : arguments
            Positional arguments to pass to the callable.
        filename : str, optional
            Path to a file where the combined stdout and stderr output will be
            written. Defaults to an empty string (no file written).
        **kwargs : keyword arguments
            Keyword arguments to pass to the callable.

        Returns
        -------
        DotObject
            An object containing:
            - result : The return value of the callable.
            - output : Captured stdout text.
            - error : Captured stderr text.
            - output_and_error : Combined stdout and stderr text.

        Notes
        -----
        - Standard output and error streams are restored to their original state
          after invocation.
        - If `filename` is provided, the combined output and error are written
          to that file.
        - This method is useful for safely invoking functions that produce
          console output, allowing you to capture and inspect their output
          programmatically.
        """
        stdout_bak = sys.stdout
        stderr_bak = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        ret_result = callable_obj(*args, **kwargs)

        sys.stdout.seek(0)
        sys.stderr.seek(0)

        stdout_result = sys.stdout.read()
        stderr_result = sys.stderr.read()

        if stderr_result:
            output_and_error = '%s\n%s' % (stdout_result, stderr_result)
        else:
            output_and_error = stdout_result

        result = DotObject(
            result=ret_result,
            output=stdout_result,               # noqa
            error=stderr_result,                # noqa
            output_and_error=output_and_error   # noqa
        )

        if filename:
            with open(filename, 'w') as stream:
                stream.write(result.output_and_error)

        sys.stdout = stdout_bak
        sys.stderr = stderr_bak

        return result

    @classmethod
    def create_runtime_error(cls, obj=None, msg=''):
        """
        Dynamically create a custom runtime exception instance.

        This method generates a new Exception subclass at runtime,
        naming it based on the provided object. If `obj` is a string,
        that string is used directly as the exception class name.
        Otherwise, the class name of `obj` is suffixed with "RTError"
        to form the new exception type. An instance of this dynamically
        created exception is then returned with the specified message.

        Parameters
        ----------
        obj : Any, optional
            The object or string used to derive the exception class name.
            - If a string, it is used directly as the exception class name.
            - If another object, its class name is suffixed with "RTError".
            Defaults to None.
        msg : str, optional
            The error message to associate with the exception instance.
            Defaults to an empty string.

        Returns
        -------
        Exception
            An instance of the dynamically created exception class,
            initialized with the provided message.

        Examples
        --------
        >>> exc = MiscFunction.create_runtime_error("CustomError", "Something went wrong")
        >>> raise exc
        Traceback (most recent call last):
            ...
        CustomError: Something went wrong
        """
        cls_name = obj.__class__.__name__
        exc_cls_name = obj if cls_name == 'str' else '%sRTError' % cls_name
        exc_cls = type(exc_cls_name, (Exception,), {})
        exc_obj = exc_cls(msg)
        return exc_obj

    @classmethod
    def raise_runtime_error(cls, obj=None, msg=''):
        """
        Raise a dynamically created runtime exception.

        This method builds on `create_runtime_error` by generating a
        custom Exception subclass at runtime and immediately raising
        an instance of it. The exception class name is derived from
        the provided object:
        - If `obj` is a string, that string is used directly as the
          exception class name.
        - If `obj` is another object, its class name is suffixed with
          "RTError" to form the new exception type.

        Parameters
        ----------
        obj : Any, optional
            The object or string used to derive the exception class name.
            Defaults to None.
        msg : str, optional
            The error message to associate with the raised exception.
            Defaults to an empty string.

        Raises
        ------
        Exception
            A dynamically created exception instance with the specified
            message.

        Examples
        --------
        >>> MiscFunction.raise_runtime_error("CustomError", "Something went wrong")
        Traceback (most recent call last):
            ...
        CustomError: Something went wrong
        """
        exc_obj = cls.create_runtime_error(obj=obj, msg=msg)
        raise exc_obj


class MiscObject:
    """
    Utility class for object manipulation and data cleanup.

    The MiscObject class provides helper methods for working with
    generic Python objects and collections. It focuses on two main
    tasks:
    - Copying objects with support for both shallow and deep copies.
    - Cleaning up lists of dictionaries by stripping string values
      and safely copying non-string values.

    These methods are designed to simplify common operations when
    handling heterogeneous data structures, ensuring consistency
    and reducing repetitive boilerplate code.

    Methods
    -------
    copy(instance, is_deep_copy=True)
        Create a shallow or deep copy of the given object.
    cleanup_list_of_dict(lst_of_dict, chars=None)
        Clean up a list of dictionaries by stripping strings and
        copying non-string values.
    """
    @classmethod
    def copy(cls, instance, is_deep_copy=True):
        """
        Create a copy of the given object.

        This method provides a convenient wrapper around Python's
        `copy.copy` and `copy.deepcopy` functions. It allows you to
        choose whether to perform a shallow or deep copy of the
        provided instance.

        Parameters
        ----------
        instance : Any
            The object to be copied.
        is_deep_copy : bool, optional
            If True (default), a deep copy of the object is created.
            If False, a shallow copy is created.

        Returns
        -------
        Any
            A new object that is either a shallow or deep copy of
            the original instance, depending on the `is_deep_copy`
            flag.
        """
        if is_deep_copy:
            new_instance = copy.deepcopy(instance)
        else:
            new_instance = copy.copy(instance)
        return new_instance

    @classmethod
    def cleanup_list_of_dict(cls, lst_of_dict, chars=None):
        """
        Clean up a list of dictionaries by stripping strings and copying values.

        This method iterates through a list of dictionaries (or other
        objects) and performs the following:
        - If an element is a dictionary, each string value is stripped
          of leading/trailing characters (default: whitespace, or
          characters specified in `chars`).
        - Non-string values are copied (deeply by default).
        - If an element is not a dictionary, it is copied directly.

        Parameters
        ----------
        lst_of_dict : list
            A list containing dictionaries or other objects to be cleaned.
        chars : str, optional
            A string specifying the set of characters to strip from
            string values. Defaults to None, which strips whitespace.

        Returns
        -------
        list
            A new list with cleaned dictionaries and copied elements.
            If `lst_of_dict` is not a list, the input is returned unchanged.
        """
        if not Misc.is_list(lst_of_dict):
            return lst_of_dict
        lst = []
        for node in lst_of_dict:
            if Misc.is_dict(node):
                new_node = dict()
                for key, val in node.items():
                    if Misc.is_string(val):
                        new_node[key] = str.strip(val, chars)
                    else:
                        new_node[key] = cls.copy(val)
                lst.append(new_node)
            else:
                lst.append(cls.copy(node))
        return lst


class Tabular:
    """
    A utility class for constructing and displaying tabular data.

    The `Tabular` class formats dictionaries (or lists of dictionaries)
    into a human-readable table. It supports column selection, text
    justification, and handling of missing values. This is useful for
    presenting structured data such as query results, reports, or logs
    in a clear tabular format.

    Attributes
    ----------
    data : list of dict
        The input data to format. Can be a list of dictionaries or a
        single dictionary (which will be wrapped in a list).
    columns : list of str, optional
        A list of column headers to include in the table. If None,
        all keys from the dictionaries are used. Default is None.
    justify : str, optional
        Text alignment for columns. Must be one of:
        - ``'left'``   : left-align text (default).
        - ``'right'``  : right-align text.
        - ``'center'`` : center-align text.
    missing : str, optional
        Placeholder text for missing values when a column is not found
        in the data. Default is ``'not_found'``.

    Methods
    -------
    validate_argument_list_of_dict() -> None
        Validate that the input data is a list of dictionaries.
    build_width_table(columns) -> dict
        Compute the maximum width for each column based on the data.
    align_string(value, width) -> str
        Align a string within a given width according to `justify`.
    build_headers_string(columns, width_tbl) -> str
        Construct the header row as a formatted string.
    build_tabular_string(columns, width_tbl) -> str
        Construct the table body as a formatted string.
    process() -> None
        Process the input data and prepare the tabular representation.
    get() -> str or list
        Return the formatted table as a string, or raw data if not processed.
    print() -> None
        Print the formatted table directly to standard output.
    """
    def __init__(self, data, columns=None, justify='left', missing='not_found'):
        self.result = ''
        if isinstance(data, dict):
            self.data = [data]
        else:
            self.data = data
        self.columns = columns
        self.justify = str(justify).lower()
        self.missing = missing
        self.is_ready = True
        self.is_tabular = False
        self.failure = ''
        self.validate_argument_list_of_dict()
        self.process()

    def validate_argument_list_of_dict(self):
        """
        Validate that the input data is a list of dictionaries.

        This method ensures that the `data` attribute of the `Tabular`
        instance is properly structured as either:
        - A list of dictionaries, or
        - A single dictionary (which is automatically wrapped in a list
          during initialization).

        If the validation fails, the method sets internal flags to mark
        the tabular object as invalid and records an error message.

        Returns
        -------
        None
            This method does not return a value. It updates internal
            state (`is_ready`, `failure`) to reflect validation results.

        Raises
        ------
        TypeError
            If `data` is not a dictionary or a list of dictionaries.

        Notes
        -----
        - This method is called automatically during initialization.
        - Ensures that subsequent tabular processing methods can safely
          assume the input is valid.
        """
        if not isinstance(self.data, (list, tuple)):
            self.is_ready = False
            self.failure = 'data MUST be a list.'
            return

        if not self.data:
            self.is_ready = False
            self.failure = 'data MUST be NOT an empty list.'
            return

        chk_keys = list()
        for a_dict in self.data:
            if isinstance(a_dict, dict):
                if not a_dict:
                    self.is_ready = False
                    self.failure = 'all dict elements MUST be NOT empty.'
                    return

                keys = list(a_dict.keys())
                if not chk_keys:
                    chk_keys = keys
                else:
                    if keys != chk_keys:
                        self.is_ready = False
                        self.failure = 'dict element MUST have same keys.'
                        return
            else:
                self.is_ready = False
                self.failure = 'all elements of list MUST be dictionary.'
                return

    def build_width_table(self, columns):
        """
        Compute the maximum width for each column in the tabular data.

        This method analyzes the provided `columns` and the instance's `data`
        to determine the maximum string length required for each column. The
        result is a mapping of column names to their respective widths, which
        can be used to align and format tabular output consistently.

        Parameters
        ----------
        columns : list of str
            A list of column headers to include in the width calculation.
            Each column name is checked against the data to determine the
            longest string value.

        Returns
        -------
        dict
            A dictionary mapping each column name to its maximum string
            length (including the header itself). For example:
            ``{"name": 5, "age": 3}``.

        Notes
        -----
        - The width of each column is the maximum of:
            * The length of the column header.
            * The length of the longest value in that column across all rows.
        - Missing values are replaced with the `missing` attribute before
          measuring length.
        """
        width_tbl = dict(zip(columns, (len(str(k)) for k in columns)))

        for a_dict in self.data:
            for col, width in width_tbl.items():
                curr_width = len(str(a_dict.get(col, self.missing)))
                new_width = max(width, curr_width)
                width_tbl[col] = new_width
        return width_tbl

    def align_string(self, value, width):
        """
        Align a string within a given width according to the justification setting.

        This method takes a value, converts it to a string, and aligns it
        within the specified width based on the `justify` attribute of the
        `Tabular` instance. Supported justifications are left, right, and
        center alignment.

        Parameters
        ----------
        value : Any
            The data to align. It will be converted to a string before alignment.
        width : int
            The target width for alignment. If the string is shorter than
            `width`, padding is added according to the justification.

        Returns
        -------
        str
            The aligned string, padded with spaces as needed to fit the
            specified width.

        Notes
        -----
        - The `justify` attribute of the `Tabular` instance determines
          alignment:
            * ``'left'``   : pad on the right.
            * ``'right'``  : pad on the left.
            * ``'center'`` : pad evenly on both sides.
        - If `value` is longer than `width`, it is returned unchanged.
        """
        value = str(value)
        if self.justify == 'center':
            return str.center(value, width)
        elif self.justify == 'right':
            return str.rjust(value, width)
        else:
            return str.ljust(value, width)

    def build_headers_string(self, columns, width_tbl):
        """
        Construct the header row of the tabular output as a formatted string.

        This method takes a list of column headers and a width mapping table,
        then aligns each header according to the `justify` setting of the
        `Tabular` instance. The result is a single string representing the
        header row of the table.

        Parameters
        ----------
        columns : list of str
            A list of column names to include in the header row.
        width_tbl : dict
            A dictionary mapping each column name to its maximum width
            (as computed by `build_width_table`). Used to align headers
            consistently with the table body.

        Returns
        -------
        str
            A formatted string containing the aligned column headers,
            separated by spaces.

        Notes
        -----
        - Each header is padded or aligned based on the width specified
          in `width_tbl`.
        - Alignment is controlled by the `justify` attribute of the
          `Tabular` instance (left, right, or center).
        - The resulting string is typically used as the first row of
          the tabular output.
        """
        lst = []
        for col in columns:
            width = width_tbl.get(col)
            new_col = self.align_string(col, width)
            lst.append(new_col)
        return '| {} |'.format(str.join(' | ', lst))

    def build_tabular_string(self, columns, width_tbl):
        """
        Construct the body of the tabular output as a formatted string.

        This method iterates over the instance's `data` and builds a
        tabular representation row by row. Each value is aligned according
        to the `justify` setting of the `Tabular` instance and padded to
        the width specified in `width_tbl`. The result is a multi-line
        string representing the table body.

        Parameters
        ----------
        columns : list of str
            A list of column headers that define the order of values in
            each row.
        width_tbl : dict
            A dictionary mapping each column name to its maximum width
            (as computed by `build_width_table`). Used to align values
            consistently across rows.

        Returns
        -------
        str
            A formatted string containing the tabular data rows, with
            values aligned and separated by spaces.

        Notes
        -----
        - Missing values are replaced with the `missing` attribute of
          the `Tabular` instance.
        - Alignment is controlled by the `justify` attribute (left,
          right, or center).
        - The resulting string does not include headers; use
          `build_headers_string` for the header row.
        """
        lst_of_str = []
        for a_dict in self.data:
            lst = []
            for col in columns:
                val = a_dict.get(col, self.missing)
                width = width_tbl.get(col)
                new_val = self.align_string(val, width)
                lst.append(new_val)
            lst_of_str.append('| {} |'.format(str.join(' | ', lst)))

        return str.join(STRING.NEWLINE, lst_of_str)

    def process(self):
        """
        Prepare the input data for tabular formatting.

        This method validates the input `data` and constructs the internal
        structures required to generate a tabular representation. It ensures
        that the data is properly normalized (list of dictionaries), computes
        column widths, and builds both the header and body strings. After
        calling `process`, the table is ready to be retrieved with `get()` or
        printed with `print()`.

        Returns
        -------
        None
            This method updates internal state and does not return a value.

        Notes
        -----
        - Calls `validate_argument_list_of_dict()` to ensure data integrity.
        - Uses `build_width_table()` to compute column widths.
        - Relies on `build_headers_string()` and `build_tabular_string()` to
          construct the formatted output.
        - Must be executed before calling `get()` or `print()` if the table
          has not yet been processed.
        """
        if not self.is_ready:
            return

        try:
            keys = list(self.data[0].keys())
            columns = self.columns or keys
            width_tbl = self.build_width_table(columns)
            deco = ['-' * width_tbl.get(c) for c in columns]
            deco_str = '+-{}-+'.format(str.join('-+-', deco))
            headers_str = self.build_headers_string(columns, width_tbl)
            tabular_data = self.build_tabular_string(columns, width_tbl)

            lst = [deco_str, headers_str, deco_str, tabular_data, deco_str]
            self.result = str.join(STRING.NEWLINE, lst)
            self.is_tabular = True
        except Exception as ex:
            self.failure = '{}: {}'.format(type(ex).__name__, ex)
            self.is_tabular = False

    def get(self):
        """
        Retrieve the processed tabular output or the raw data.

        This method returns the formatted tabular string if the instance
        has successfully processed the input data into tabular format.
        Otherwise, it falls back to returning the original `data` attribute.

        Returns
        -------
        str or Any
            - If `is_tabular` is True, returns the formatted tabular string
              stored in `result`.
            - If `is_tabular` is False, returns the original `data`.

        Notes
        -----
        - Typically called after `process()` to retrieve the final tabular
          representation.
        - Provides a safe way to access either the formatted output or the
          raw data depending on processing status.
        """
        tabular_data = self.result if self.is_tabular else self.data
        return tabular_data

    def print(self):
        """
        Print the tabular content or raw data.

        This method retrieves the current output from `get()` and prints it
        in a human-readable format. If the result is a structured object
        (e.g., dict, list, tuple, or set), it uses `pprint` for pretty-printing.
        Otherwise, it prints the string representation directly.

        Returns
        -------
        None
            This method prints the output and does not return a value.

        Notes
        -----
        - If the data has been processed into tabular format, the formatted
          string is printed.
        - If the data is still raw (e.g., a dictionary or list), it is
          pretty-printed for readability.
        - Acts as a convenience wrapper around `get()` and `pprint`.
        """
        tabular_data = self.get()
        if isinstance(tabular_data, (dict, list, tuple, set)):
            pprint(tabular_data)
        else:
            print(tabular_data)


def get_data_as_tabular(data, columns=None, justify='left', missing='not_found'):
    """
    Convert structured data into a tabular string representation.

    This function wraps the `Tabular` class to provide a simple interface
    for translating dictionaries or lists of dictionaries into a formatted
    table. It supports optional column selection, text justification, and
    handling of missing values.

    Parameters
    ----------
    data : list of dict or dict
        The input data to format. Can be:
        - A list of dictionaries (multiple rows).
        - A single dictionary (treated as one row).
    columns : list of str, optional
        A list of column headers to include in the table. If None, all keys
        from the dictionaries are used. Default is None.
    justify : str, optional
        Text alignment for columns. Must be one of:
        - ``'left'``   : left-align text (default).
        - ``'right'``  : right-align text.
        - ``'center'`` : center-align text.
    missing : str, optional
        Placeholder text for missing values when a column is not found in
        the data. Default is ``'not_found'``.

    Returns
    -------
    str
        A formatted string representing the tabular data.

    Notes
    -----
    - Internally creates a `Tabular` instance and calls its `get()` method.
    - Useful for quickly converting structured data into a human-readable
      table without manually instantiating `Tabular`.
    """
    node = Tabular(data, columns=columns, justify=justify, missing=missing)
    result = node.get()
    return result


def print_data_as_tabular(data, columns=None, justify='left', missing='not_found'):
    """
    Print structured data in a tabular format.

    This function wraps the `Tabular` class to provide a simple interface
    for displaying dictionaries or lists of dictionaries as a formatted
    table. It supports optional column selection, text justification, and
    handling of missing values. The formatted table is printed directly
    to standard output.

    Parameters
    ----------
    data : list of dict or dict
        The input data to format. Can be:
        - A list of dictionaries (multiple rows).
        - A single dictionary (treated as one row).
    columns : list of str, optional
        A list of column headers to include in the table. If None, all keys
        from the dictionaries are used. Default is None.
    justify : str, optional
        Text alignment for columns. Must be one of:
        - ``'left'``   : left-align text (default).
        - ``'right'``  : right-align text.
        - ``'center'`` : center-align text.
    missing : str, optional
        Placeholder text for missing values when a column is not found in
        the data. Default is ``'not_found'``.

    Returns
    -------
    None
        This function prints the formatted table and does not return a value.

    Notes
    -----
    - Internally creates a `Tabular` instance and calls its `print()` method.
    - Useful for quickly displaying structured data without manually
      instantiating `Tabular`.
    """
    node = Tabular(data, columns=columns, justify=justify, missing=missing)
    node.print()
