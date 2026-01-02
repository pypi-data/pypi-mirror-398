"""
genericlib.file
===============

File and directory utilities for the `genericlib` package.

This module provides decorators and a utility class for handling common
filesystem operations with built-in error management. It centralizes tasks
such as file creation, deletion, copying, path manipulation, and content
loading (text, JSON, YAML, CSV), while offering consistent error-handling
strategies through decorators.

Key Components
--------------
- try_to_call:
    A decorator that wraps methods in a try/except block. On failure, it
    returns `False` unless `on_failure=True` is passed, in which case the
    exception is re-raised. It also updates the calling object's `message`
    and `on_failure` attributes when exceptions are suppressed.

- try_to_other_call:
    Similar to `try_to_call`, but returns an empty string (`""`) instead of
    `False` when exceptions are suppressed. Useful for methods expected to
    return string values.

- File:
    A utility class that consolidates common file and directory operations.
    It includes methods for checking existence, copying, creating, deleting,
    and loading files in multiple formats. It also provides helpers for
    building paths, extracting extensions, and performing quick lookups.

Error Handling
--------------
- Methods decorated with `@try_to_call` or `@try_to_other_call` provide
  flexible error management controlled by the `on_failure` flag.
- When exceptions are suppressed, the `File` class updates its `message`
  and `on_failure` attributes to reflect the error state.

Use Cases
---------
- Safely perform file operations without breaking application flow.
- Load structured data (JSON, YAML, CSV) with consistent error handling.
- Simplify directory creation, file copying, and path manipulation.
- Integrate with Robot Framework for automated testing and reporting.

"""

import csv
import re
import os
import filecmp
import shutil
import functools

from pathlib import Path
from pathlib import PurePath
from pathlib import WindowsPath
from datetime import datetime

import yaml
import json

from genericlib import Text
from genericlib import DotObject
from genericlib import substitute_variable

from genericlib.exceptions import raise_exception

from genericlib.constant import STRING


def try_to_call(func):
    """
    Wrap the classmethod and return False if on_failure is false.
    ==========

    Decorator to wrap a callable and handle exceptions gracefully.

    This function wraps the given callable (typically a classmethod) in a
    try/except block. If the wrapped function raises an exception, the
    behavior depends on the `on_failure` keyword argument:

    - If `on_failure=True`, the exception is re-raised.
    - If `on_failure=False` (default), the exception is suppressed and
      `False` is returned. Additionally, if the first positional argument
      is an object, its `message` attribute is set to the exception text
      and its `on_failure` attribute is set to `False`.

    Parameters
    ----------
    func : callable
        The function or method to wrap.

    Returns
    -------
    callable
        A wrapped function that executes `func` and handles exceptions
        according to the `on_failure` flag.

    Notes
    -----
    - The wrapper preserves the original function's metadata via
      `functools.wraps`.
    - The first positional argument is assumed to be an object with
      `message` and `on_failure` attributes if exception handling is
      triggered.

    Examples
    --------
    >>> @try_to_call
    ... def risky_method(self, x, on_failure=False):
    ...     if x < 0:
    ...         raise ValueError("Negative not allowed")
    ...     return x * 2

    >>> class Obj:
    ...     def __init__(self):
    ...         self.message = None
    ...         self.on_failure = True
    ...
    ...     risky = risky_method

    >>> o = Obj()
    >>> o.risky(5)
    10

    >>> o.risky(-1)
    False
    >>> o.message
    Text(ValueError('Negative not allowed'))
    >>> o.on_failure
    False
    """
    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
        """A Wrapper Function"""
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as ex:
            if kwargs.get('on_failure', False):
                raise_exception(ex)
            else:
                if len(args) >= 1:
                    args[0].message = Text(ex)
                    args[0].on_failure = False
                    return False
                else:
                    raise_exception(ex)
    return wrapper_func


def try_to_other_call(func):
    """
    Wrap the classmethod and return empty string if on_failure is false.
    ==========

    Decorator to wrap a callable and handle exceptions gracefully.

    This function wraps the given callable (typically a classmethod) in a
    try/except block. If the wrapped function raises an exception, the
    behavior depends on the `on_failure` keyword argument:

    - If `on_failure=True`, the exception is re-raised.
    - If `on_failure=False` (default), the exception is suppressed and
      an empty string (`""`) is returned. Additionally, if the first
      positional argument is an object, its `message` attribute is set
      to the exception text and its `on_failure` attribute is set to
      `False`.

    Parameters
    ----------
    func : callable
        The function or method to wrap.

    Returns
    -------
    callable
        A wrapped function that executes `func` and handles exceptions
        according to the `on_failure` flag.

    Notes
    -----
    - The wrapper preserves the original function's metadata via
      `functools.wraps`.
    - The first positional argument is assumed to be an object with
      `message` and `on_failure` attributes if exception handling is
      triggered.
    - This decorator differs from `try_to_call` in that it returns
      an empty string (`""`) instead of `False` when suppressing
      exceptions.

    Examples
    --------
    >>> @try_to_other_call
    ... def risky_method(self, x, on_failure=False):
    ...     if x < 0:
    ...         raise ValueError("Negative not allowed")
    ...     return str(x * 2)

    >>> class Obj:
    ...     def __init__(self):
    ...         self.message = None
    ...         self.on_failure = True
    ...
    ...     risky = risky_method

    >>> o = Obj()
    >>> o.risky(5)
    '10'

    >>> o.risky(-1)
    ''
    >>> o.message
    Text(ValueError('Negative not allowed'))
    >>> o.on_failure
    False
    """
    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
        """A Wrapper Function"""
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as ex:
            if kwargs.get('on_failure', False):
                raise_exception(ex)
            else:
                if len(args) >= 1:
                    args[0].message = Text(ex)
                    args[0].on_failure = False
                    return ''
                else:
                    raise_exception(ex)
    return wrapper_func


class File:
    """
    Utility class for common file and directory operations.

    The `File` class centralizes frequently used filesystem tasks such as
    checking existence, copying, creating, deleting, and loading files in
    various formats (text, JSON, YAML, CSV). It also provides helpers for
    building file paths, extracting extensions, and performing quick lookups.

    Error Handling
    --------------
    - Methods decorated with `@try_to_call` return `False` on failure unless
      `on_failure=True` is passed, in which case the exception is re-raised.
    - Methods decorated with `@try_to_other_call` return an empty string (`""`)
      on failure unless `on_failure=True` is passed.
    - When exceptions are suppressed, the class-level attributes `message`
      and `on_failure` are updated to reflect the error state.

    Attributes
    ----------
    message : str
        Stores the last error message when an operation fails.
    on_failure : bool
        Indicates whether the last operation failed (`False`) or succeeded (`True`).

    Common Operations
    -----------------
    - File checks: `is_file`, `is_dir`, `is_exist`
    - Copying: `copy_file`, `copy_files`
    - Directory creation: `make_directory`, `make_dir`
    - File creation and saving: `create`, `save`
    - Deletion: `delete`
    - Path utilities: `get_path`, `get_dir`, `get_new_filename`,
      `get_extension`, `get_filepath_timestamp_format1`
    - Content loading: `load_text`, `load_json`, `load_yaml`, `load_csv`
    - Content retrieval: `get_content`, `get_result_from_yaml_file`
    - Miscellaneous: `quicklook`, `is_duplicate_file`,
      `get_list_of_filenames`, `change_home_dir_to_generic`

    Notes
    -----
    - Many methods support an `on_failure` flag to control whether exceptions
      are raised or suppressed.
    - Methods are implemented as classmethods, so they can be called directly
      on the class without instantiation.
    - Designed to integrate with Robot Framework, with usage examples provided
      in several method docstrings.
    """
    message = ''
    on_failure = False

    @classmethod
    def clean(cls):
        """
        Reset the error state of the File class.

        This method clears the `message` attribute, effectively removing
        any stored error information from previous operations. It does not
        affect files on disk; it only resets the internal state used for
        error reporting.

        Returns
        -------
        None
            The method performs an in-place reset of the class-level
            `message` attribute.

        Notes
        -----
        - Use this method before starting a new sequence of file operations
          if you want to ensure that no residual error messages remain.
        - The `on_failure` flag is not modified by this method.

        Examples
        --------
        >>> File.message
        'File not found'
        >>> File.clean()
        >>> File.message
        ''
        """
        cls.message = ''

    @classmethod
    @try_to_call
    def is_file(cls, filename, on_failure=False):
        """
        Check whether the given path refers to an existing file.

        This method verifies if the specified `filename` corresponds to a
        valid file on the filesystem. It is decorated with `@try_to_call`,
        meaning exceptions can be suppressed or re-raised depending on the
        `on_failure` flag.

        Parameters
        ----------
        filename : str
            The path or name of the file to check.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns False.

        Returns
        -------
        bool
            True if the path exists and is a file, otherwise False.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - This method does not check directories; use `File.is_dir`
          for that purpose.

        Examples
        --------
        >>> File.is_file("example.txt")
        True

        >>> File.is_file("nonexistent.txt")
        False

        >>> File.is_file("example.txt", on_failure=True)
        True
        """
        cls.clean()
        cls.on_failure = on_failure
        file_obj = Path(filename)
        return file_obj.is_file()

    @classmethod
    @try_to_call
    def is_dir(cls, file_path, on_failure=False):
        """
        Check whether the given path refers to an existing directory.

        This method verifies if the specified `file_path` corresponds to a
        valid directory on the filesystem. It is decorated with `@try_to_call`,
        meaning exceptions can be suppressed or re-raised depending on the
        `on_failure` flag.

        Parameters
        ----------
        file_path : str
            The path to check.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns False.

        Returns
        -------
        bool
            True if the path exists and is a directory, otherwise False.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - This method does not check files; use `File.is_file` for that purpose.

        Examples
        --------
        >>> File.is_dir("/usr/local")
        True

        >>> File.is_dir("example.txt")
        False

        >>> File.is_dir("/nonexistent/path", on_failure=True)
        Traceback (most recent call last):
            ...
        FileNotFoundError: ...
        """
        cls.clean()
        cls.on_failure = on_failure
        file_obj = Path(file_path)
        return file_obj.is_dir()

    @classmethod
    @try_to_call
    def is_exist(cls, filename, on_failure=False):
        """
        Check whether the given path exists in the filesystem.

        This method verifies if the specified `filename` corresponds to
        an existing file or directory. It is decorated with `@try_to_call`,
        meaning exceptions can be suppressed or re-raised depending on the
        `on_failure` flag.

        Parameters
        ----------
        filename : str
            The path or name of the file or directory to check.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns False.

        Returns
        -------
        bool
            True if the path exists (file or directory), otherwise False.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - Use `File.is_file` or `File.is_dir` if you need to distinguish
          between files and directories.

        Examples
        --------
        >>> File.is_exist("example.txt")
        True

        >>> File.is_exist("/nonexistent/path")
        False

        >>> File.is_exist("example.txt", on_failure=True)
        True
        """
        cls.clean()
        cls.on_failure = on_failure
        file_obj = Path(filename)
        return file_obj.exists()

    @classmethod
    @try_to_other_call
    def copy_file(cls, src, dst, on_failure=False):
        """
        Copy a single file from source to destination.

        This method copies the file located at `src` to the specified
        destination `dst`. The destination may be either a file path or
        a directory. It is decorated with `@try_to_other_call`, meaning
        exceptions can be suppressed or re-raised depending on the
        `on_failure` flag.

        Parameters
        ----------
        src : str
            The path to the source file to copy.
        dst : str
            The destination file path or directory.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns an empty string.

        Returns
        -------
        str
            The path of the copied file if the operation succeeds.
            If the copy fails and `on_failure=False`, an empty string
            is returned.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - Use `File.copy_files` if you need to copy multiple files at once.

        Examples
        --------
        >>> File.copy_file("source.txt", "dest.txt")
        'dest.txt'

        >>> File.copy_file("source.txt", "/nonexistent/path")
        ''

        >>> File.copy_file("source.txt", "dest.txt", on_failure=True)
        'dest.txt'
        """
        cls.clean()
        cls.on_failure = on_failure
        copied_file = shutil.copy2(src, dst)
        return copied_file

    @classmethod
    def copy_files(cls, src, dst, on_failure=False):
        """
        Copy one or more files to a destination directory.

        This method copies either a single file or a list of files from
        `src` into the specified destination directory `dst`. Unlike
        `File.copy_file`, which handles only one file, this method supports
        batch copying. If any copy operation fails, behavior depends on the
        `on_failure` flag.

        Parameters
        ----------
        src : str or list
            The source file path or a list of file paths to copy.
        dst : str
            The destination directory where the files will be copied.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns an empty list.

        Returns
        -------
        list
            A list of copied file paths if the operation succeeds.
            If the copy fails and `on_failure=False`, an empty list is returned.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - Use `File.copy_file` for single-file copy operations.
        - The destination must be a directory; copying to a file path
          is not supported by this method.

        Examples
        --------
        >>> File.copy_files("source.txt", "backup_dir")
        ['backup_dir/source.txt']

        >>> File.copy_files(["a.txt", "b.txt"], "backup_dir")
        ['backup_dir/a.txt', 'backup_dir/b.txt']

        >>> File.copy_files("missing.txt", "backup_dir")
        []

        >>> File.copy_files("missing.txt", "backup_dir", on_failure=True)
        Traceback (most recent call last):
            ...
        FileNotFoundError: ...
        """
        cls.clean()
        cls.make_directory(dst, showed=False)

        empty_list = []
        if isinstance(src, list):
            copied_files = empty_list
            for file in src:
                copied_file = cls.copy_file(file, dst, on_failure=on_failure)
                if cls.message:
                    return copied_files
                copied_files.append(copied_file)
            return copied_files
        else:
            copied_file = cls.copy_file(src, dst)
            if cls.message:
                return empty_list
            else:
                return [copied_file]

    @classmethod
    @try_to_call
    def make_directory(cls, file_path, showed=True, on_failure=False):
        """
        Create a new directory at the specified path.

        This method attempts to create a directory at the given `file_path`.
        It is decorated with `@try_to_call`, meaning exceptions can be
        suppressed or re-raised depending on the `on_failure` flag. If
        `showed=True`, a message may be displayed to indicate that the
        directory was created.

        Parameters
        ----------
        file_path : str
            The path where the new directory should be created.
        showed : bool, optional
            Whether to display a message when the directory is created.
            Defaults to True.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns False.

        Returns
        -------
        bool
            True if the directory was successfully created, otherwise False.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - Use `File.make_dir` as an alias for this method if preferred.

        Examples
        --------
        >>> File.make_directory("new_folder")
        True

        >>> File.make_directory("/restricted/path")
        False

        >>> File.make_directory("new_folder", on_failure=True)
        True
        """
        cls.clean()
        cls.on_failure = on_failure

        if cls.is_exist(file_path):
            if cls.is_dir(file_path):
                cls.message = Text.format('%r directory is already existed.', file_path)    # noqa
                return True
            else:
                cls.message = Text.format('Existing %r IS NOT a directory.', file_path)     # noqa
                return False

        file_obj = Path(file_path)
        file_obj.mkdir(parents=True, exist_ok=True)
        fmt = '{:%Y-%m-%d %H:%M:%S.%f} - {} folder is created.'
        showed and print(fmt.format(datetime.now(), file_path))
        cls.message = Text.format('{} folder is created.', file_path)       # noqa
        return True

    @classmethod
    def make_dir(cls, file_path, showed=True, on_failure=False):
        """
        Create a new directory at the specified path (alias of `make_directory`).

        This method attempts to create a directory at the given `file_path`.
        It behaves the same as `File.make_directory`, providing an alternative
        name for convenience. If `showed=True`, a message may be displayed to
        indicate that the directory was created.

        Parameters
        ----------
        file_path : str
            The path where the new directory should be created.
        showed : bool, optional
            Whether to display a message when the directory is created.
            Defaults to True.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns False.

        Returns
        -------
        bool
            True if the directory was successfully created, otherwise False.

        Notes
        -----
        - This method is functionally identical to `File.make_directory`.
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.

        Examples
        --------
        >>> File.make_dir("new_folder")
        True

        >>> File.make_dir("/restricted/path")
        False

        >>> File.make_dir("new_folder", on_failure=True)
        True
        """
        result = cls.make_directory(file_path, showed=showed, on_failure=on_failure)
        return result

    @classmethod
    @try_to_call
    def create(cls, filename, showed=True, on_failure=False):
        """
        Create a new empty file at the specified path.

        This method attempts to create a file with the given `filename`.
        If the file already exists, behavior may depend on the underlying
        implementation (typically overwriting or leaving unchanged). It is
        decorated with `@try_to_call`, meaning exceptions can be suppressed
        or re-raised depending on the `on_failure` flag. If `showed=True`,
        a message may be displayed to indicate that the file was created.

        Parameters
        ----------
        filename : str
            The path or name of the file to create.
        showed : bool, optional
            Whether to display a message when the file is created.
            Defaults to True.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns False.

        Returns
        -------
        bool
            True if the file was successfully created, otherwise False.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - Use `File.save` if you want to create a file and immediately
          write content into it.

        Examples
        --------
        >>> File.create("new_file.txt")
        True

        >>> File.create("/restricted/path/file.txt")
        False

        >>> File.create("new_file.txt", on_failure=True)
        True
        """
        cls.clean()
        cls.on_failure = on_failure

        filename = cls.get_path(str(filename).strip())  # noqa
        if cls.is_exist(filename):
            cls.message = 'File is already existed.'
            return True

        file_obj = Path(filename)
        if not file_obj.parent.exists():
            file_obj.parent.mkdir(parents=True, exist_ok=True)
        file_obj.touch()
        fmt = '{:%Y-%m-%d %H:%M:%S.%f} - {} file is created.'
        showed and print(fmt.format(datetime.now(), filename))
        cls.message = Text.format('{} file is created.', filename)      # noqa
        return True

    @classmethod
    def get_path(cls, *args, is_home=False):
        """
        Construct a filesystem path from one or more components.

        This method joins the given path components into a single
        filesystem path string. If `is_home=True`, the user's home
        directory is prepended to the constructed path.

        Parameters
        ----------
        *args : arguments
            One or more strings representing path components (e.g.,
            directory names, filenames).
        is_home : bool, optional
            If True, the user's home directory is included at the
            beginning of the path. Defaults to False.

        Returns
        -------
        str
            A constructed filesystem path.

        Notes
        -----
        - Path components are joined using the operating system's
          native path separator.
        - Use this method to build portable paths without manually
          concatenating strings.
        """
        lst = [Path.home()] if is_home else []
        lst.extend(list(args))      # noqa
        file_path = str(Path(PurePath(*lst)).expanduser().absolute())
        return file_path

    @classmethod
    def get_dir(cls, file_path):
        """
        Extract the directory portion from a given file path.

        This method returns the directory component of the specified
        `file_path`. It is useful when you need to isolate the folder
        location from a full path that includes a filename.

        Parameters
        ----------
        file_path : str
            A full filesystem path that may include both directory
            and filename components.

        Returns
        -------
        str
            The directory portion of the path. If the path does not
            contain a directory component, an empty string is returned.

        Notes
        -----
        - The result depends on the operating system's path separator.
        - Use this method when you need the parent directory of a file.
        """
        file_obj = Path(file_path).expanduser().absolute()
        if file_obj.is_dir():
            return str(file_obj)
        elif file_obj.is_file():
            return str(file_obj.parent)
        else:
            fmt = 'FileNotFoundError: No such file or directory "{}"'
            cls.message = Text.format(fmt, file_path)       # noqa
            return ''

    @classmethod
    def get_filepath_timestamp_format1(cls, *args, prefix='', extension='',
                                       is_full_path=False, ref_datetime=None):
        """
        Construct a file path with a timestamp-based filename (format 1).

        This method builds a file path by joining the provided components
        (`*args`) and appending a filename that includes a timestamp. The
        timestamp is generated from either the current datetime or a
        user-supplied `ref_datetime`. Optional `prefix` and `extension`
        values can be applied to customize the filename. If `is_full_path=True`,
        the absolute path is returned.

        Parameters
        ----------
        *args : arguments
            One or more strings representing path components (e.g.,
            directories, subdirectories).
        prefix : str, optional
            A prefix to prepend to the base filename. Defaults to an empty string.
        extension : str, optional
            The file extension (without the dot). Defaults to an empty string.
        is_full_path : bool, optional
            If True, returns the absolute path. Defaults to False.
        ref_datetime : datetime.datetime, optional
            A reference datetime object to generate the timestamp.
            If None, the current datetime is used.

        Returns
        -------
        str
            A constructed file path with a timestamp-based filename.

        Notes
        -----
        - The timestamp format used is `YYYYMMDD_HHMMSS` (e.g., `20251215_213045`).
        - If `extension` is provided, it is appended with a leading dot.
        - Useful for generating unique filenames for logs, reports, or backups.
        """
        lst = list(args)

        ref_datetime = ref_datetime if isinstance(ref_datetime, datetime) else datetime.now()

        basename = '{:%Y%b%d_%H%M%S}'.format(ref_datetime)
        if prefix.strip():
            basename = '%s_%s' % (prefix.strip(), basename)

        if extension.strip():
            basename = '%s.%s' % (basename, extension.strip().strip('.'))

        lst.append(basename)
        file_path = cls.get_path(*lst) if is_full_path else str(Path(*lst))
        return file_path

    @classmethod
    @try_to_other_call
    def get_content(cls, file_path, on_failure=False):
        """
        Retrieve the content of a text file.

        This method reads and returns the content of the file located at
        `file_path`. It is decorated with `@try_to_other_call`, meaning
        exceptions can be suppressed or re-raised depending on the
        `on_failure` flag.

        Parameters
        ----------
        file_path : str
            The path to the file whose content should be read.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns an empty string.

        Returns
        -------
        str
            The content of the file as a string. If the read fails and
            `on_failure=False`, an empty string is returned.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - Use this method for simple text retrieval. For structured
          formats (JSON, YAML, CSV), use `File.load_json`,
          `File.load_yaml`, or `File.load_csv`.
        """
        cls.clean()
        cls.on_failure = on_failure

        filename = cls.get_path(file_path)  # noqa
        with open(filename, encoding="utf-8") as stream:
            content = stream.read()
            return content

    @classmethod
    def get_result_from_yaml_file(
        cls, file_path, base_dir='', is_stripped=True, dot_datatype=False,
        default=None, var_substitution=False, root_var_name='self'
    ):
        """
        Load and parse a YAML file, returning its contents.

        This method reads a YAML file from the given `file_path` and returns
        the parsed result. It supports optional preprocessing such as stripping
        whitespace, variable substitution, and conversion to a `DotObject`
- style
        structure for attribute-style access. If the file cannot be found or
        parsed, a `default` value is returned.

        Parameters
        ----------
        file_path : str
            Path to the YAML file.
        base_dir : str, optional
            Base directory to prepend to `file_path`. Defaults to an empty string.
        is_stripped : bool, optional
            If True, leading and trailing whitespace is removed from string values.
            Defaults to True.
        dot_datatype : bool, optional
            If True and the result is a dictionary, it is converted into a
            `DotObject` for attribute-style access. Defaults to False.
        default : object, optional
            Value to return if the file is not found or cannot be parsed.
            Defaults to an empty dictionary.
        var_substitution : bool, optional
            If True, performs internal variable substitution within the YAML
            content. Defaults to False.
        root_var_name : str, optional
            Root variable name used for substitution when `var_substitution=True`.
            Defaults to "self".

        Returns
        -------
        object
            Parsed YAML content. The type depends on the file contents:
            - dict (or `DotObject` if `dot_datatype=True`)
            - list
            - str
            - other YAML-supported types
            If the file cannot be loaded, returns `default`.

        Notes
        -----
        - Supports flexible YAML parsing with optional preprocessing.
        - Useful for configuration files, structured data, or templates.
        - Variable substitution allows dynamic values within YAML.

        Examples
        --------
        >>> File.get_result_from_yaml_file("config.yaml")
        {'setting': 'value', 'enabled': True}

        >>> File.get_result_from_yaml_file("config.yaml", dot_datatype=True)
        DotObject(setting='value', enabled=True)

        >>> File.get_result_from_yaml_file("missing.yaml", default={"fallback": True})
        {'fallback': True}

        >>> File.get_result_from_yaml_file("config.yaml", var_substitution=True, root_var_name="app")
        {'app_name': 'MyApp', 'version': '1.0'}
        """
        default = default or dict()

        cls.clean()
        yaml_result = default

        try:
            if base_dir:
                filename = cls.get_path(cls.get_dir(base_dir), file_path)   # noqa
            else:
                filename = cls.get_path(file_path)  # noqa

            with open(filename, encoding="utf-8") as stream:
                content = stream.read()
                if is_stripped:
                    content = content.strip()

                if content:
                    yaml_result = yaml.safe_load(content)
                    cls.message = Text.format('loaded {}', filename)        # noqa
                else:
                    cls.message = Text.format('"{}" file is empty.', filename)  # noqa

        except Exception as ex:
            cls.message = Text(ex)

        if var_substitution:
            yaml_result = substitute_variable(yaml_result,
                                              root_var_name=root_var_name)

        if isinstance(yaml_result, dict) and dot_datatype:
            dot_result = DotObject(yaml_result)     # noqa
            return dot_result
        else:
            return yaml_result

    @classmethod
    @try_to_call
    def save(cls, filename, data, on_failure=False):
        """
        Save data to a file.

        This method writes the given `data` into the specified `filename`.
        If the file does not exist, it is created. If it already exists,
        its contents are overwritten. It is decorated with `@try_to_call`,
        meaning exceptions can be suppressed or re-raised depending on the
        `on_failure` flag.

        Parameters
        ----------
        filename : str
            The path or name of the file where data will be saved.
        data : str
            The content to write into the file.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns False.

        Returns
        -------
        bool
            True if the file was successfully saved, otherwise False.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - Use `File.create` if you only want to create an empty file
          without writing content.

        Examples
        --------
        >>> File.save("output.txt", "Hello, world!")
        True

        >>> File.save("/restricted/path/file.txt", "data")
        False

        >>> File.save("output.txt", "Hello, world!", on_failure=True)
        True
        """
        cls.clean()
        cls.on_failure = on_failure

        if isinstance(data, list):
            content = str.join(STRING.NEWLINE, [str(item) for item in data])
        else:
            content = str(data)

        filename = cls.get_path(filename)   # noqa
        if not cls.create(filename):
            return False

        file_obj = Path(filename)
        file_obj.touch()
        file_obj.write_text(content)
        cls.message = Text.format('Successfully saved data to "{}" file', filename)     # noqa
        return True

    @classmethod
    @try_to_call
    def delete(cls, filename, on_failure=False):
        """
        Delete a file from the filesystem.

        This method attempts to remove the file specified by `filename`.
        It is decorated with `@try_to_call`, meaning exceptions can be
        suppressed or re-raised depending on the `on_failure` flag.

        Parameters
        ----------
        filename : str
            The path or name of the file to delete.
        on_failure : bool, optional
            Controls exception handling. If True, exceptions are re-raised.
            If False (default), exceptions are suppressed and the method
            returns False.

        Returns
        -------
        bool
            True if the file was successfully deleted, otherwise False.

        Notes
        -----
        - If `on_failure=False` and an error occurs, the class-level
          attributes `File.message` and `File.on_failure` are updated
          to reflect the error state.
        - This method only deletes files, not directories. Use
          `File.make_directory` or `File.make_dir` for directory management.

        Examples
        --------
        >>> File.delete("old_file.txt")
        True

        >>> File.delete("missing.txt")
        False

        >>> File.delete("old_file.txt", on_failure=True)
        True
        """
        cls.clean()
        cls.on_failure = on_failure

        filepath = File.get_path(filename)      # noqa
        file_obj = Path(filepath)
        if file_obj.is_dir():
            shutil.rmtree(filename)
            cls.message = Text.format('Successfully deleted "{}" folder', filename)     # noqa
        else:
            file_obj.unlink()
            cls.message = Text.format('Successfully deleted "{}" file', filename)       # noqa
        return True

    @classmethod
    def change_home_dir_to_generic(cls, filename):
        """
        Replace the user's home directory in a file path with a generic placeholder.

        This method substitutes the actual home directory portion of the given
        `filename` with a generic name (e.g., `~` or `HOME`). It is intended
        for display purposes only, so that file paths can be shown without
        exposing sensitive user-specific information.

        Parameters
        ----------
        filename : str
            The full file path that may include the user's home directory.

        Returns
        -------
        str
            A file path string where the home directory has been replaced
            with a generic placeholder.

        Notes
        -----
        - This method does not modify the actual filesystem path; it only
          returns a sanitized string for display.
        - Useful for logging, reporting, or presenting paths in a
          user-agnostic format.

        Examples
        --------
        >>> File.change_home_dir_to_generic("/home/user/documents/report.txt")
        'HOME/documents/report.txt'

        >>> File.change_home_dir_to_generic("C:\\Users\\Name\\Desktop\\notes.txt")
        'HOME/Desktop/notes.txt'
        """
        node = Path.home()
        home_dir = str(node)
        if isinstance(node, WindowsPath):
            replaced = '%HOMEDRIVE%\\%HOMEPATH%'
        else:
            replaced = '${HOME}'
        new_name = filename.replace(home_dir, replaced)
        return new_name

    @classmethod
    def is_duplicate_file(cls, file, source):
        """
        Check whether a file is a duplicate of another.

        This method compares the given `file` against a `source` file to
        determine if they are duplicates. The comparison may be based on
        file content, size, or other criteria depending on the underlying
        implementation.

        Parameters
        ----------
        file : str
            Path to the file being checked.
        source : str
            Path to the source file used for comparison.

        Returns
        -------
        bool
            True if the file is considered a duplicate of the source,
            otherwise False.

        Notes
        -----
        - This method is useful for detecting redundant files in a
          directory or validating copies.
        - The definition of "duplicate" depends on the implementation
          (e.g., exact content match, checksum comparison, or metadata).

        Examples
        --------
        >>> File.is_duplicate_file("copy.txt", "original.txt")
        True

        >>> File.is_duplicate_file("notes.txt", "report.txt")
        False
        """
        if isinstance(source, list):
            for other_file in source:
                chk = filecmp.cmp(file, other_file)
                if chk:
                    return True
            return False
        else:
            chk = filecmp.cmp(file, source)
            return chk

    @classmethod
    def get_list_of_filenames(cls, top='.', pattern='', excluded_duplicate=True):
        """
        Retrieve a list of filenames from a directory tree.

        This method scans the directory specified by `top` and returns a list
        of filenames that match the given `pattern`. Optionally, duplicate
        files can be excluded from the results.

        Parameters
        ----------
        top : str, optional
            The root directory to start scanning. Defaults to the current
            directory (`"."`).
        pattern : str, optional
            A filename pattern (e.g., wildcard or regex) used to filter results.
            Defaults to an empty string, which matches all files.
        excluded_duplicate : bool, optional
            If True (default), duplicate files are excluded from the results.
            If False, duplicates are included.

        Returns
        -------
        list of str
            A list of filenames that match the given criteria. If no files
            are found, an empty list is returned.

        Notes
        -----
        - Useful for batch processing, reporting, or searching files by pattern.
        - Duplicate detection is based on the implementation of
          `File.is_duplicate_file`.
        """
        cls.clean()

        empty_list = []

        if not cls.is_exist(top):
            File.message = 'The provided path IS NOT existed.'
            return empty_list

        if cls.is_file(top):
            if pattern:
                result = [top] if re.search(pattern, top) else empty_list
            else:
                result = [top]
            return result

        try:
            lst = []
            for dir_path, _dir_names, file_names in os.walk(top):
                for file_name in file_names:
                    if pattern and not re.search(pattern, file_name):
                        continue
                    file_path = str(Path(dir_path, file_name))

                    if excluded_duplicate:
                        is_duplicated = cls.is_duplicate_file(file_path, lst)   # noqa
                        not is_duplicated and lst.append(file_path)
                    else:
                        lst.append(file_path)
            return lst

        except Exception as ex:
            cls.message = Text(ex)
            return empty_list

    @classmethod
    @try_to_call
    def quicklook(cls, filename, lookup='', on_failure=False):
        cls.on_failure = on_failure

        if not cls.is_exist(filename):
            cls.message = Text.format('%r file is not existed.', filename)  # noqa
            return False

        content = cls.get_content(filename)

        if not content.strip():
            if content.strip() == lookup.strip():
                return True
            else:
                return False

        if not lookup.strip():
            return True

        if cls.message:
            return False

        if lookup in content:
            return True
        else:
            match = re.search(lookup, content)
            return bool(match)

    @classmethod
    def get_new_filename(cls, filename, new_name='', prefix='',
                         postfix='', new_extension=''):
        if File.is_dir(filename):
            return filename

        file_obj = Path(filename)

        if new_name:
            file_obj = file_obj.with_name(new_name)
            new_filename = str(file_obj)
            return new_filename

        new_ext = new_extension.strip()
        if new_ext:
            new_ext = '.%s' % new_ext.lstrip('.')
            file_obj = file_obj.with_suffix(new_ext)

        prefix = prefix.strip()
        if prefix:
            fn = file_obj.name
            if not fn.startswith(prefix):
                fn = '%s%s' % (prefix, fn)
                file_obj = file_obj.with_name(fn)

        postfix = postfix.strip()
        if postfix:
            fn_wo_ext = file_obj.stem
            ext = file_obj.suffix
            if not fn_wo_ext.endswith(postfix):
                fn = '%s%s%s' % (fn_wo_ext, postfix, ext)
                file_obj = file_obj.with_name(fn)

        new_filename = str(file_obj)
        return new_filename

    @classmethod
    def get_extension(cls, filename):
        """
        Return the file extension
        Parameters:
          filename (str): file name
        Returns:
          str: the file extension.
        Robot Framework Usage:
        # import library snippet in settings section: Library   genericlib.RFFile
        ${result}=   rf generic lib file get extension   filename.txt
        """
        file_obj = Path(filename)
        extension = file_obj.suffix[1:]
        return extension

    rf_generic_lib_file_get_extension = get_extension

    @classmethod
    def build_open_file_kwargs_from(cls, kwargs):
        file_kwargs = dict(mode='r', buffering=-1,
                           encoding=None, errors=None,
                           newline=None, closefd=True,
                           opener=None)
        if isinstance(kwargs, dict):
            for key in file_kwargs:
                if key in kwargs:
                    file_kwargs[key] = kwargs.pop(key)
        return file_kwargs

    @classmethod
    def load_text(cls, filename, **kwargs):
        """
        Load text file and return content of file as text.
        Parameters:
          filename (str): file name
          kwargs (dict): full open document, check this link
            + https://docs.python.org/3/library/functions.html#open
        Returns:
          str: content of file.
        Robot Framework Usage:
        # import library snippet in settings section: Library   genericlib.RFFile
        ${result}=   rf generic lib file load text   filename.txt
        # or
        ${result}=   rf generic lib file load text   filename.txt   mode=r   encoding=utf-8   errors=strict
        """
        file_kwargs = cls.build_open_file_kwargs_from(kwargs)
        with open(filename, **file_kwargs) as stream:
            content = stream.read()
            if isinstance(content, str):
                return content
            elif isinstance(content, bytes):
                # else content is isinstance of byte
                encoding = file_kwargs.get('encoding') or 'utf-8'
                errors = file_kwargs.get('errors') or 'strict'
                content = content.decode(encoding=encoding, errors=errors)
                return content
            else:
                raise Exception('Unknown file type')

    rf_generic_lib_file_load_text = load_text

    @classmethod
    def load_json(cls, filename, **kwargs):
        """
        Load JSON file and return JSON object.
        Parameters:
          filename (str): file name
          kwargs (dict): full open document, check these links
            + https://docs.python.org/3/library/json.html#module-json
            + https://docs.python.org/3/library/functions.html#open
        Returns:
          object: json object.
        Robot Framework Usage:
        # import library snippet in settings section: Library   genericlib.RFFile
        ${result}=   rf generic lib file load json   filename.json
        """
        file_kwargs = cls.build_open_file_kwargs_from(kwargs)
        json_content = cls.load_text(filename, **file_kwargs)
        json_obj = json.loads(json_content, **kwargs)
        return json_obj

    rf_generic_lib_file_load_json = load_json

    @classmethod
    def load_yaml(cls, filename, **kwargs):
        """
        Load YAML file and return YAML object.
        Parameters:
          filename (str): file name
          kwargs (dict): full open document, check this link
            + https://docs.python.org/3/library/functions.html#open
        Returns:
          object: yaml object.
        Robot Framework Usage:
        # import library snippet in settings section: Library   genericlib.RFFile
        ${result}=   rf generic lib file load yaml   filename.yaml
        """
        yaml_content = cls.load_text(filename, **kwargs)
        yaml_obj = yaml.safe_load(yaml_content)
        return yaml_obj

    rf_generic_lib_file_load_yaml = load_yaml

    @classmethod
    def load_csv(cls, filename, **kwargs):
        """
        Load CSV file and return list of dictionary.
        Parameters:
          filename (str): file name
          kwargs (dict): full open document,
            check these links
              + https://docs.python.org/3/library/csv.html#module-csv
              + https://docs.python.org/3/library/functions.html#open
        Returns:
          list: list of dictionary.
        Robot Framework Usage:
        # import library snippet in settings section: Library   genericlib.RFFile
        ${result}=   rf generic lib file load csv   filename.csv
        """
        lst = []
        file_kwargs = cls.build_open_file_kwargs_from(kwargs)
        csv_content = cls.load_text(filename, **file_kwargs)
        stream = csv.StringIO(csv_content)      # noqa
        rows = csv.DictReader(stream, **kwargs)
        for row in rows:
            lst.append(row)
        return lst

    rf_generic_lib_file_load_csv = load_csv
