"""
genericlib.text
===============

Enhanced string and text-processing utilities.

This module extends Python’s built-in `str` type with specialized subclasses
and helper functions for safer text handling, line validation, regex-based
pattern generation, and controlled escaping. It is designed to simplify
common text manipulation tasks while providing consistent error handling
and metadata preservation.

Use Cases
---------
- Safely represent exceptions as strings for logging or debugging.
- Validate and manipulate single-line text with preserved metadata.
- Convert matched text fragments into reusable regex patterns.
- Inspect Unicode whitespace/non-whitespace characters for parsing tasks.
- Escape regex patterns in a controlled way for readability.
- Wrap text for display or serialization with consistent quoting rules.

"""


import re
import string

from textwrap import dedent

from genericlib.exceptions import LineArgumentError
from genericlib.constant import STRING


class BaseText(str):
    """
    A string subclass that provides enhanced text representation.

    `BaseText` extends Python’s built-in `str` type to handle exceptions
    gracefully. When initialized with a `BaseException` instance, it
    automatically formats the exception into a readable string containing
    the exception type and message. Otherwise, it behaves like a normal
    string.

    This is useful for consistent error reporting and logging, ensuring
    exceptions are converted into human-readable text without requiring
    explicit formatting.

    Methods
    -------
    __new__(*args, **kwargs)
        Create a new `BaseText` instance. If the first argument is an
        exception, return a formatted string representation of it.
    """
    def __new__(cls, *args, **kwargs):
        arg0 = args[0] if args else None
        if args and isinstance(arg0, BaseException):
            txt = str.__new__(cls, '{}: {}'.format(type(arg0).__name__, arg0))
            return txt
        else:
            txt = str.__new__(cls, *args, **kwargs)
            return txt


class Text(BaseText):
    """
    A string subclass with extended text formatting and utility methods.

    `Text` builds on `BaseText` to provide additional functionality for
    safe string formatting, HTML wrapping, and regex-based splitting.
    It is designed to simplify common text manipulation tasks while
    gracefully handling exceptions.

    Methods
    -------
    format(*args, **kwargs) -> str
        Safely format a string using either old-style (`%`) or new-style
        (`str.format`) formatting. If formatting fails, returns a readable
        error message instead of raising an exception.
        - If called with no arguments, returns an empty string.
        - If called with one argument, returns it as a `Text` instance.
        - If called with multiple arguments, attempts formatting with
          `%` first, then falls back to `str.format`.

    wrap_html(tag, data, *args) -> str
        Wrap the given data in an HTML tag. Optional attributes can be
        provided as additional arguments.
        - If `data` is empty, produces a self-closing tag.
        - Attributes are joined with spaces and inserted into the tag.

    do_finditer_split(pattern) -> list[str]
        Split the string into segments based on regex matches.
        Returns a list containing alternating non-matching substrings
        and matched substrings.
    """
    @classmethod
    def format(cls, *args, **kwargs):
        """
        Safely format text using old-style (`%`) or new-style (`str.format`) string formatting.

        This method attempts to format a string with the provided arguments,
        supporting both positional and keyword-based formatting. It provides
        graceful error handling: if formatting fails, the exception is captured
        and returned as a readable `Text` instance instead of raising an error.

        Behavior
        --------
        - If called with no arguments, returns an empty string.
        - If called with one argument, returns it as a `Text` instance.
        - If called with multiple arguments:
            * Tries old-style (`%`) formatting first.
            * Falls back to new-style (`str.format`) if needed.
            * If both fail, returns a concatenated error message from both attempts.

        Parameters
        ----------
        *args : arguments
            Positional arguments used for formatting. The first argument is
            treated as the format string, and subsequent arguments are values
            to substitute.
        **kwargs : keyword arguments
            Keyword arguments used for new-style (`str.format`) formatting.

        Returns
        -------
        str
            The formatted string if successful, otherwise a string containing
            the error message(s).
        """
        if not args:
            text = ''
            return text
        else:
            if kwargs:
                fmt = args[0]
                try:
                    text = str(fmt).format(args[1:], **kwargs)
                    return text
                except Exception as ex:
                    text = cls(ex)
                    return text
            else:
                if len(args) == 1:
                    text = cls(args[0])
                    return text
                else:
                    fmt = args[0]
                    t_args = tuple(args[1:])
                    try:
                        if len(t_args) == 1 and isinstance(t_args[0], dict):
                            text = str(fmt) % t_args[0]
                        else:
                            text = str(fmt) % t_args

                        if text == fmt:
                            text = str(fmt).format(*t_args)
                        return text
                    except Exception as ex1:
                        try:
                            text = str(fmt).format(*t_args)
                            return text
                        except Exception as ex2:
                            text = '%s\n%s' % (cls(ex1), cls(ex2))
                            return text

    @classmethod
    def wrap_html(cls, tag, data, *args):
        """
        Wrap text content in an HTML element.

        This method generates an HTML string by wrapping the given `data`
        inside the specified `tag`. Optional attributes can be provided
        as additional arguments. If `data` is empty or whitespace, a
        self-closing tag is produced instead.

        Parameters
        ----------
        tag : str
            The HTML tag name (e.g., "div", "span", "p").
        data : str
            The text content to wrap inside the tag. If empty, a self-closing
            tag is generated.
        *args : arguments
            Optional attribute strings (e.g., "class='highlight'", "id='main'").
            Multiple attributes are joined with spaces.

        Returns
        -------
        str
            A string containing the generated HTML element.

        Behavior
        --------
        - If attributes are provided, they are inserted into the opening tag.
        - If `data` contains non-whitespace text, a normal opening/closing tag
          pair is generated.
        - If `data` is empty or whitespace, a self-closing tag is generated.
        """
        data = str(data)
        tag = str(tag).strip()
        attributes = [str(arg).strip() for arg in args if str(arg).strip()]
        if attributes:
            attrs_txt = str.join(STRING.SPACE_CHAR, attributes)
            if data.strip():
                result = '<{0} {1}>{2}</{0}>'.format(tag, attrs_txt, data)
            else:
                result = '<{0} {1}/>'.format(tag, attrs_txt)
        else:
            if data.strip():
                result = '<{0}>{1}</{0}>'.format(tag, data)
            else:
                result = '<{0}/>'.format(tag)
        return result

    def do_finditer_split(self, pattern):
        """
        Split the string into segments based on regex matches.

        This method uses `re.finditer` to locate all occurrences of the given
        regex `pattern` within the string. It returns a list containing
        alternating substrings: the non-matching text before each match,
        followed by the matched text itself. The final element includes any
        remaining text after the last match.

        Parameters
        ----------
        pattern : str
            A regular expression pattern used to identify matches within
            the string.

        Returns
        -------
        list of str
            A list of substrings consisting of:
            - Non-matching text before each match.
            - The matched text itself.
            - The trailing text after the last match (if any).

        Notes
        -----
        - If no matches are found, the entire string is returned as a single
          element in the list.
        - Useful for tokenizing text while preserving matched delimiters.
        """
        result = []
        start = 0
        m = None
        for m in re.finditer(pattern, self):
            pre_match = self[start:m.start()]
            match = m.group()
            result.append(pre_match)
            result.append(match)
            start = m.end()

        if m:
            post_match = self[m.end():]
            result.append(post_match)
        else:
            result.append(str(self))
        return result


class BaseLine(str):
    """
    A string subclass representing a single line of text with preserved metadata.

    `BaseLine` extends Python's built-in `str` type to enforce that the input
    `data` consists of exactly one line. It captures both the raw line content
    and metadata about the line, including the text portion and any trailing
    newline characters.

    Construction
    ------------
    When a new `BaseLine` object is created:
    - If `data` contains exactly one line, the object is initialized and
      metadata attributes are stored on the class:
        * `_raw_data` : the original line string
        * `_data`     : regex match object for the line content (excluding newline)
        * `_joiner`   : regex match object for trailing newline characters
    - If `data` contains multiple lines, a `LineArgumentError` is raised.

    Raises
    ------
    LineArgumentError
        If `data` contains more than one line.

    Notes
    -----
    - This class is useful for parsing text files line by line while preserving
      both the content and newline information.
    - Metadata attributes (`_raw_data`, `_data`, `_joiner`) are stored at
      the class level, not the instance level.

    Examples
    --------
    >>> line = BaseLine("Hello world\\n")
    >>> isinstance(line, str)
    True
    >>> line
    'Hello world\\n'

    >>> BaseLine("Line1\\nLine2")
    Traceback (most recent call last):
        ...
    LineArgumentError: data argument is multi-lines. MUST be a single line.
    """
    def __new__(cls, data, *args):
        new_base_line_obj = str.__new__(cls, data)
        lines = new_base_line_obj.splitlines(keepends=True)
        if len(lines) == 1:
            __line = lines[0] if lines else ''
            new_base_line_obj._raw_data = __line
            new_base_line_obj._data = re.match(r"([^\r\n]+)?", __line).group()
            new_base_line_obj._joiner = re.search(r"([\r\n]+)?$", __line).group()
            return new_base_line_obj
        else:
            error = "data argument is multi-lines.  MUST be a single line."
            raise LineArgumentError(error)


class Line(BaseLine):
    """
    A specialized string subclass representing a single line of text with
    additional utilities for whitespace handling, validation, and regex-based
    pattern conversion.

    `Line` extends `BaseLine` to provide convenient properties and methods
    for analyzing and manipulating a single line of text. It enforces the
    single-line constraint and exposes metadata such as leading/trailing
    whitespace, emptiness checks, and regex-based tokenization.

    Properties
    ----------
    joiner : str
        Trailing newline characters captured from the original line.
    raw_data : str
        The raw line string as originally provided.
    clean_line : str
        The line with leading and trailing whitespace removed.
    is_empty : bool
        True if the line is completely empty.
    is_optional_empty : bool
        True if the line contains only whitespace characters.
    leading : str
        Leading whitespace characters at the start of the line.
    trailing : str
        Trailing whitespace characters at the end of the line.
    is_leading : bool
        True if the line has leading whitespace.
    is_trailing : bool
        True if the line has trailing whitespace.

    Class Methods
    -------------
    is_line(data, on_failure=False) -> bool
        Validate whether `data` represents a single line. Returns True if valid.
        If invalid and `on_failure=True`, raises `LineArgumentError`.

    Instance Methods
    ----------------
    convert_to_regex_pattern() -> str
        Convert the line into a regex pattern string. Splits the line into
        matched/unmatched segments using punctuation and whitespace patterns,
        then recombines them into a regex-compatible representation.

    do_finditer_split(data, pattern=r'\\s+') -> list
        Split `data` into a sequence of matched and unmatched objects using
        regex `finditer`. Returns a list of `PreMatchedObject`, `MatchedObject`,
        `PostMatchedObject`, or `BaseMatchedObject` instances.

    Returns
    -------
    Line
        A `Line` instance wrapping a single line of text.

    Raises
    ------
    LineArgumentError
        If initialized with multi-line data or if `is_line` validation fails
        with `on_failure=True`.

    Notes
    -----
    - This class is useful for parsing structured text files where whitespace
      and punctuation patterns are significant.
    - The regex-based splitting allows fine-grained analysis of line content.

    Examples
    --------
    >>> line = Line("   Hello world      ")
    >>> line.clean_line
    'Hello world'
    >>> line.leading
    '   '
    >>> line.trailing
    '      '
    >>> line.is_empty
    False
    >>> Line.is_line("Single line")
    True
    >>> Line.is_line("Line1\\nLine2", on_failure=False)
    False
    >>> Line.is_line("Line1\\nLine2", on_failure=True)
    Traceback (most recent call last):
        ...
    LineArgumentError: data argument is multi-lines. MUST be a single line.
    >>> line.convert_to_regex_pattern()
    '(Hello)(\\s+)(world)'
    """
    @property
    def joiner(self):
        """
        Get the trailing newline characters associated with the line.

        This property returns the newline sequence (e.g., "\n", "\r\n") that
        was originally captured when the `Line` object was created. It reflects
        the line terminator used in the source text.

        Returns
        -------
        str
            The newline characters at the end of the line, or emtpy string if no
            newline was present.

        Notes
        -----
        - Useful for preserving exact line endings when reconstructing or
          reformatting text files.
        - The value is derived from the regex match performed during
          `BaseLine` initialization.

        Examples
        --------
        >>> line = Line("Hello world\\n")
        >>> line.joiner
        '\\n'

        >>> line = Line("Hello world")
        >>> line.joiner is ""
        True
        """
        return self._joiner

    @property
    def raw_data(self):
        """
        Get the original, unmodified line string.

        This property returns the exact line content as it was provided
        when the `Line` object was created, including any whitespace and
        newline characters. Unlike `clean_line`, it does not strip or
        alter the text in any way.

        Returns
        -------
        str
            The raw line string, identical to the input passed during
            initialization.

        Notes
        -----
        - Useful when you need to preserve the original formatting of
          the line for logging, debugging, or reconstruction.
        - For a trimmed version of the line, use the `clean_line`
          property instead.

        Examples
        --------
        >>> line = Line("   Hello world\\n")
        >>> line.raw_data
        '   Hello world\\n'

        >>> line.clean_line
        'Hello world'
        """
        return self._raw_data

    @property
    def clean_line(self):
        """
        Get the line content with leading and trailing whitespace removed.

        This property returns a "cleaned" version of the line by stripping
        all surrounding whitespace characters (spaces, tabs, newlines).
        It is useful when you want the meaningful text content without
        formatting artifacts.

        Returns
        -------
        str
            The line string with leading and trailing whitespace removed.

        Notes
        -----
        - Unlike `raw_data`, which preserves the original formatting,
          `clean_line` provides a normalized version of the text.
        - This is equivalent to calling `self.strip()`.

        Examples
        --------
        >>> line = Line("   Hello world   \\n")
        >>> line.raw_data
        '   Hello world   \\n'
        >>> line.clean_line
        'Hello world'

        >>> Line("").clean_line
        ''
        """
        return self.strip()

    @property
    def is_empty(self):
        """
        Check whether the line is completely empty.

        This property evaluates whether the `Line` instance contains no
        characters at all. It differs from `is_optional_empty`, which
        considers lines consisting only of whitespace as "empty."

        Returns
        -------
        bool
            True if the line is an empty string (`""`), otherwise False.

        Notes
        -----
        - Use `is_empty` to detect truly blank lines.
        - Use `is_optional_empty` to detect lines that contain only
          whitespace characters (spaces, tabs, etc.).

        Examples
        --------
        >>> Line("").is_empty
        True

        >>> Line("   ").is_empty
        False

        >>> Line("Hello").is_empty
        False
        """
        return self == ""

    @property
    def is_optional_empty(self):
        """
        Check whether the line consists only of whitespace characters.

        This property evaluates whether the `Line` instance contains one or
        more characters, but all of them are whitespace (spaces, tabs, etc.).
        It differs from `is_empty`, which requires the line to be completely
        blank (`""`).

        Returns
        -------
        bool
            True if the line contains only whitespace characters, otherwise False.

        Notes
        -----
        - Use `is_optional_empty` to detect lines that are visually empty but
          technically contain whitespace.
        - This is useful for text parsing where whitespace-only lines should
          be treated as optional or ignorable.

        Examples
        --------
        >>> Line("").is_optional_empty
        False

        >>> Line("   ").is_optional_empty
        True

        >>> Line("\\t\\t").is_optional_empty
        True

        >>> Line("Hello").is_optional_empty
        False
        """
        return bool(re.match(r"\s+$", self))

    @property
    def leading(self):
        """
        Get the leading whitespace characters at the start of the line.

        This property extracts and returns any whitespace (spaces, tabs, etc.)
        that appears at the beginning of the line. If no leading whitespace is
        present, an empty string is returned.

        Returns
        -------
        str
            The leading whitespace characters at the start of the line,
            or an empty string if none exist.

        Notes
        -----
        - Useful for analyzing indentation or formatting in structured text.
        - For a boolean check, use the `is_leading` property to determine
          whether the line has leading whitespace.

        Examples
        --------
        >>> Line("    Hello").leading
        '    '

        >>> Line("Hello").leading
        ''

        >>> Line("\\tIndented").leading
        '\\t'
        """
        leading_chars = re.match(r'(\s+)?', self).group()
        return leading_chars

    @property
    def trailing(self):
        """
        Get the trailing whitespace characters at the end of the line.

        This property extracts and returns any whitespace (spaces, tabs, etc.)
        that appears at the end of the line. If no trailing whitespace is
        present, an empty string is returned.

        Returns
        -------
        str
            The trailing whitespace characters at the end of the line,
            or an empty string if none exist.

        Notes
        -----
        - Useful for analyzing formatting, alignment, or detecting
          extraneous spaces in structured text.
        - For a boolean check, use the `is_trailing` property to determine
          whether the line has trailing whitespace.

        Examples
        --------
        >>> Line("Hello    ").trailing
        '    '

        >>> Line("Hello").trailing
        ''

        >>> Line("Hello\\t").trailing
        '\\t
        """
        trailing_chars = re.search(r'(\s+)?$', self).group().rstrip('\r\n')
        return trailing_chars

    @property
    def is_leading(self):
        """
        Check whether the line has leading whitespace.

        This property evaluates whether the `Line` instance begins with one
        or more whitespace characters (spaces, tabs, etc.). It is a boolean
        convenience wrapper around the `leading` property.

        Returns
        -------
        bool
            True if the line starts with whitespace, otherwise False.

        Notes
        -----
        - Use `leading` to retrieve the actual whitespace characters.
        - This property is useful for detecting indentation or formatting
          in structured text.

        Examples
        --------
        >>> Line("    Hello").is_leading
        True

        >>> Line("Hello").is_leading
        False

        >>> Line("\\tIndented").is_leading
        True
        """
        return len(self.leading) > 0

    @property
    def is_trailing(self):
        """
        Check whether the line has trailing whitespace.

        This property evaluates whether the `Line` instance ends with one
        or more whitespace characters (spaces, tabs, etc.). It is a boolean
        convenience wrapper around the `trailing` property.

        Returns
        -------
        bool
            True if the line ends with whitespace, otherwise False.

        Notes
        -----
        - Use `trailing` to retrieve the actual whitespace characters.
        - This property is useful for detecting formatting issues such as
          unnecessary spaces at the end of a line.

        Examples
        --------
        >>> Line("Hello    ").is_trailing
        True

        >>> Line("Hello").is_trailing
        False

        >>> Line("Hello\\t").is_trailing
        True
        """
        return len(self.trailing) > 0

    @classmethod
    def is_line(cls, data, on_failure=False):
        """
        Validate whether the given data represents a single line of text.

        This class method checks if `data` can be interpreted as exactly one
        line (including optional trailing newline characters). If the input
        contains multiple lines, the behavior depends on the `on_failure` flag.

        Parameters
        ----------
        data : str
            The string or object to validate. It will be converted to a string
            before checking.
        on_failure : bool, optional
            Controls error handling when multiple lines are detected.
            - If False (default), the method returns False.
            - If True, a `LineArgumentError` is raised.

        Returns
        -------
        bool
            True if `data` is a valid single line, False if multiple lines
            are detected and `on_failure=False`.

        Raises
        ------
        LineArgumentError
            If `data` contains multiple lines and `on_failure=True`.

        Notes
        -----
        - A "line" is defined as a string that produces exactly one element
          when split with `splitlines(keepends=True)`.
        - This method is useful for enforcing single-line constraints before
          constructing `Line` or `BaseLine` objects.

        Examples
        --------
        >>> Line.is_line("Hello world")
        True

        >>> Line.is_line("Hello\\nWorld")
        False

        >>> Line.is_line("Hello\\nWorld", on_failure=True)
        Traceback (most recent call last):
            ...
        LineArgumentError: data argument is multi-lines. MUST be a single line.
        """
        lines = str(data).splitlines(keepends=True)
        if len(lines) == 1:
            return True

        if on_failure:
            error = "data argument is multi-lines.  MUST be a single line."
            raise LineArgumentError(error)
        else:
            return False

    def convert_to_regex_pattern(self):
        """
        Convert the line into a regex-compatible pattern string.

        This method analyzes the line and transforms it into a regular
        expression pattern that represents its structure. It detects
        punctuation clusters and whitespace sequences, splits the line
        into matched/unmatched segments, and then recombines them into
        a regex pattern string.

        Workflow
        --------
        1. Define a punctuation-based regex (`punct_pat`) and a whitespace
           regex (`other_pat`).
        2. If the line contains repeated punctuation followed by spaces,
           split it using `do_finditer_split` with the punctuation pattern.
           - Subsegments are further split by whitespace.
        3. Else if the line contains whitespace, split it using
           `do_finditer_split` with the whitespace pattern.
        4. If neither punctuation nor whitespace is found, wrap the entire
           line in a `BaseMatchedObject`.
        5. Concatenate all segments into a regex pattern string by calling
           `to_pattern()` on each matched object.

        Returns
        -------
        str
            A regex pattern string representing the structure of the line.

        Notes
        -----
        - This method is useful for converting textual lines into regex
          patterns for validation, parsing, or matching structured text.
        - Relies on helper classes (`BaseMatchedObject`, `PreMatchedObject`,
          `MatchedObject`, `PostMatchedObject`) to represent different
          segments of the line.

        Examples
        --------
        >>> line = Line("Hello   World")
        >>> line.convert_to_regex_pattern()
        '(Hello)(\\s+)(World)'

        >>> line = Line("...   ...")
        >>> line.convert_to_regex_pattern()
        '(\\.\\.\\. +)(\\1+)'

        >>> line = Line("PlainText")
        >>> line.convert_to_regex_pattern()
        '(PlainText)'
        """
        result = []
        punct_pat = BaseMatchedObject.punctuation_pattern
        pat = f'({punct_pat}+ +)\\1+'
        other_pat = r'\s+'
        if re.search(pat, self):
            items = self.do_finditer_split(self, pattern=pat)
            for item in items:
                if isinstance(item, (PreMatchedObject, PostMatchedObject)):
                    lst = self.do_finditer_split(item.data, pattern=other_pat)
                    result.extend(lst)
                else:
                    result.append(item)
        elif re.search(other_pat, self):
            result = self.do_finditer_split(self, pattern=other_pat)
        else:
            result = [BaseMatchedObject(self)]
        text_pattern = ''.join(elmt.to_pattern() for elmt in result)
        return text_pattern

    def do_finditer_split(self, data, pattern=r'\s+'):  # noqa
        """
        Split a string into matched and unmatched segments using regex finditer.

        This method iterates over all matches of the given regex `pattern`
        within `data` and constructs a sequence of objects representing
        the text before, during, and after each match. It preserves both
        matched substrings and unmatched portions for fine-grained analysis.

        Parameters
        ----------
        data : str
            The string to be split into segments.
        pattern : str, optional
            A regular expression pattern used to identify split points.
            Defaults to ``r'\\s+'`` (whitespace sequences).

        Returns
        -------
        list
            A list of segment objects, which may include:
            - `PreMatchedObject` : text before a match
            - `MatchedObject`    : the matched substring
            - `PostMatchedObject`: text after the last match
            - `BaseMatchedObject`: the entire string if no matches are found

        Notes
        -----
        - Empty segments are skipped (objects with `is_empty=True` are not added).
        - This method is typically used by `convert_to_regex_pattern` to
          tokenize a line into regex-compatible components.
        - The returned objects expose methods like `to_pattern()` for
          converting segments into regex strings.

        Examples
        --------
        >>> line = Line("Hello   World")
        >>> segments = line.do_finditer_split("Hello   World", pattern=r'\\s+')
        >>> [type(item).__name__ for item in segments]      # noqa
        ['PreMatchedObject', 'MatchedObject', 'PostMatchedObject']

        >>> line.do_finditer_split("PlainText", pattern=r'\\s+')
        [BaseMatchedObject('PlainText')]
        """
        result = []
        start = 0
        match = None
        for match in re.finditer(pattern, data):
            pre_obj = PreMatchedObject(match, start)
            not pre_obj.is_empty and result.append(pre_obj)

            matched_obj = MatchedObject(match)
            result.append(matched_obj)
            start = match.end()

        if match is not None:
            post_obj = PostMatchedObject(match, start)
            not post_obj.is_empty and result.append(post_obj)
        else:
            result.append(BaseMatchedObject(data))
        return result


class BaseMatchedObject:
    """
    Represents a fragment of matched text and converts it into the most
    appropriate regular‑expression pattern.

    This class is used when reconstructing or generalizing text matches into
    regex components. Given a piece of text (either a literal string or a
    `re.Match` object), it analyzes the content and determines which category
    it belongs to:

    - **Whitespace sequences**
      Collapses runs of whitespace into a normalized pattern, optionally using
      an user‑provided or default separator.

    - **Repeated punctuation**
      Detects sequences like "!!!", "...", or "???" and converts them into
      quantifier‑based regex fragments such as `!{2,}` or `(\\.){2,}`.

    - **Repeated punctuation + space sequences**
      Handles patterns like ". . . " or "! ! " and produces grouped patterns
      such as `(\\. ){2,}`.

    - **Literal text**
      Any other text is escaped and treated as a literal regex component.

    The `to_pattern()` method orchestrates this classification by querying each
    pattern‑generation method in priority order and returning the first
    applicable regex fragment.

    Attributes:
        punctuation_pattern (str):
            Character class used to detect punctuation.
        repeated_punctuation_pattern (str):
            Pattern for identifying repeated punctuation runs.
        repeated_punctuations_space_pattern (str):
            Pattern for identifying repeated punctuation‑plus‑space runs.
        default_separator (str):
            Default whitespace pattern used when normalizing whitespace.
        user_separator (str):
            Optional user‑provided override for whitespace normalization.
        match (re.Match | None):
            The original match object, if provided.
        data (str):
            The raw matched text content.

    Properties:
        is_empty (bool):
            True if the matched text is an empty string.

    Methods:
        change_separator(separator, user_pattern):
            Updates whitespace normalization behavior.
        to_pattern():
            Returns the regex fragment representing this matched object.
        get_whitespace_pattern():
            Produces a regex for whitespace sequences.
        get_text_pattern():
            Produces a literal‑text regex.
        get_repeated_puncts_pattern():
            Produces a regex for repeated punctuation.
        get_repeated_puncts_space_pattern():
            Produces a regex for repeated punctuation‑plus‑space sequences.
    """
    punctuation_pattern = r'[!\"#$%&\'()*+,./:;<=>?@\[\\\]\^_`{|}~-]'
    repeated_punctuation_pattern = f'({punctuation_pattern}+?)\\1+'
    repeated_punctuations_space_pattern = f'({punctuation_pattern}+ +)\\1+'
    default_separator = ''
    user_separator = ''

    def __init__(self, match):
        self.match = match if isinstance(match, re.Match) else None
        self.data = match if isinstance(match, str) else ''

    @property
    def is_empty(self):
        """
        Indicates whether the data of matched object contains any text.

        Returns:
            bool: True if the underlying matched data is an empty string,
            meaning no meaningful content was captured; otherwise False.
        """
        return self.data == ''

    def change_separator(self, separator=' ', user_pattern=''):
        """
        Updates the whitespace‑normalization behavior for this matched object.

        This method controls how whitespace sequences are converted into regex
        patterns. An user‑provided pattern takes precedence over the default
        separator. If `user_pattern` is supplied, it will be used verbatim when
        generating whitespace patterns; otherwise, `separator` defines the default
        regex fragment used to represent whitespace runs.

        Args:
            separator (str): The default regex fragment to use when normalizing
                whitespace (e.g., " ", r"\\s"). Ignored if `user_pattern` is set.
            user_pattern (str): An explicit regex pattern that overrides the
                default separator for whitespace handling.
        """
        self.user_separator = user_pattern
        self.default_separator = separator

    def to_pattern(self):
        """
        Returns the most appropriate regular‑expression fragment for this matched
        object.

        The method evaluates the underlying text (`self.data`) against several
        pattern‑generation rules—whitespace, repeated punctuation‑with‑spaces,
        repeated punctuation, and literal text—in that priority order. Each helper
        method reports whether its pattern applies. The first applicable pattern is
        selected and returned.

        Returns:
            str: A regex fragment representing the normalized form of the matched
            text. This fragment is guaranteed to be non‑empty and suitable for
            inclusion in a larger composed pattern.
        """
        result = dict()
        result.update(self.get_whitespace_pattern())
        result.update(self.get_repeated_puncts_space_pattern())
        result.update(self.get_repeated_puncts_pattern())
        result.update(self.get_text_pattern())
        pattern = [key for key, value in result.items() if value][0]
        return pattern

    def get_whitespace_pattern(self):
        """
        Generates a regex fragment representing a run of whitespace characters.

        This method is selected only when the matched text consists entirely of
        whitespace. It normalizes the whitespace into a regex pattern based on the
        following rules:

        - If an user‑provided separator pattern is set, that pattern is returned
          verbatim.
        - Otherwise, the default separator is used if one has been configured.
        - If no separators are configured, the method distinguishes between:
            * pure space characters → represented as " " or " +"
            * mixed whitespace (tabs, newlines, etc.) → represented as r"\\s" or r"\\s+"
        - The pattern is pluralized with "+" when the whitespace run contains more
          than one character.

        Returns:
            dict: A mapping of `{pattern: True}` if whitespace applies, or
            `{'': False}` if the text is not a whitespace sequence.
        """
        if not re.match(r'\s+$', self.data):
            return {'': False}

        if self.user_separator:
            return self.user_separator, True

        total = len(self.data)
        is_space = self.data[0] == ' ' and len(set(self.data)) == 1
        if self.default_separator:
            pattern = self.default_separator
        else:
            pattern = ' ' if is_space else r'\s'
        pattern = f'{pattern}+' if total > 1 else pattern

        return {pattern: True}

    def get_text_pattern(self):
        """
        Produces a regex fragment that matches the text exactly as it appears.

        This method is used when the matched content does not fall into any of the
        specialized categories (whitespace, repeated punctuation, or punctuation‑
        with‑spaces). The text is escaped using a soft‑escape routine so that any
        characters with special meaning in regular expressions are treated
        literally.

        Returns:
            dict: A mapping of `{escaped_text: True}`, indicating that this literal
            pattern applies.
        """
        pattern = do_soft_regex_escape(self.data)
        return {pattern: True}

    def get_repeated_puncts_pattern(self):
        """
        Generates a regex fragment for sequences composed entirely of punctuation,
        with special handling for repeated punctuation runs.

        This method applies only when the matched text contains nothing but
        punctuation characters. It scans the string for groups of repeated
        punctuation (e.g., "!!!", "...", "??") and rewrites each run into a
        quantifier‑based regex such as `!{2,}` or `(\\.){2,}`. Mixed punctuation
        sequences are preserved literally between repeated runs.

        If no repeated punctuation is found, the entire string is simply escaped
        and returned as a literal pattern.

        Returns:
            dict: A mapping of `{pattern: True}` if the text consists solely of
            punctuation, or `{'': False}` if the rule does not apply.
        """
        if not re.match(f'{self.punctuation_pattern}+$', self.data):
            return {'': False}
        else:
            start, m, pattern = 0, None, ''
            for m in re.finditer(self.repeated_punctuation_pattern, self.data):
                pattern += do_soft_regex_escape(self.data[start:m.start()])
                found = m.group()
                repeated = str.join('', dict(zip(found, found)))
                fmt = '%s{2,}' if len(repeated) == 1 else '(%s){2,}'
                pattern += fmt % do_soft_regex_escape(repeated)
                start = m.end()
            else:
                if m:
                    pattern += do_soft_regex_escape(self.data[m.end():])
                    return {pattern: True}
                else:
                    pattern = do_soft_regex_escape(self.data)
                    return {pattern: True}

    def get_repeated_puncts_space_pattern(self):
        """
        Generates a regex fragment for sequences where punctuation characters are
        repeatedly followed by one or more spaces.

        This method applies only when the entire matched text consists of repeated
        units of the form "<punctuation><space>" (e.g., ". ", "!  ", "? ? "). It
        identifies the repeated unit, escapes the punctuation portion, determines
        whether the space portion should be represented as a single space or " +",
        and constructs a grouped pattern such as `(\\. ){2,}` or `(\\!  ){2,}`.

        Returns:
            dict: A mapping of `{pattern: True}` if the text matches the repeated
            punctuation‑plus‑space structure, or `{'': False}` if it does not.
        """
        match = re.match(f'{self.repeated_punctuations_space_pattern}$', self.data)
        if not match:
            return {'': False}
        found = match.groups()[0]
        puncts_pat = do_soft_regex_escape(found.strip())
        space_pat = ' +' if '  ' in found else ' '
        pattern = '(%s%s){2,}' % (puncts_pat, space_pat)
        return {pattern: True}


class MatchedObject(BaseMatchedObject):
    """
    Specialized matched‑text wrapper that always derives its content from a
    regular‑expression match object.

    Unlike `BaseMatchedObject`, which may receive either a raw string or a
    match object, this subclass assumes a valid `re.Match` instance and
    extracts the matched text directly via `match.group()`. This ensures that
    `self.data` always reflects the exact substring captured by the regex
    engine, including any surrounding context or grouping behavior.

    Args:
        match (re.Match): The match object from which to extract the text.
    """
    def __init__(self, match):
        super().__init__(match)
        self.data = match.group()


class PreMatchedObject(BaseMatchedObject):
    """
    Represents the text that appears immediately before a regex match.

    This subclass extracts a substring from the original input string,
    beginning at a specified `start` index and ending at the start position
    of the provided `re.Match` object. It is useful when reconstructing or
    analyzing the context surrounding a match, such as capturing leading
    whitespace, punctuation, or other structural markers that precede the
    main matched segment.

    Args:
        match (re.Match): The match object whose starting position defines
            the end of the pre‑match slice.
        start (int): The index in the original string where the pre‑match
            region begins.
    """
    def __init__(self, match, start):
        super().__init__(match)
        self.data = match.string[start: match.start()]


class PostMatchedObject(BaseMatchedObject):
    """
    Represents the text that appears immediately after a regex match.

    This subclass extracts the substring from the original input string
    beginning at the given `start` index and continuing to the end of the
    string. It is typically used to capture trailing context that follows a
    matched segment, such as punctuation, whitespace, or structural markers
    that occur after the main match.

    Args:
        match (re.Match): The match object whose underlying string provides
            the source text.
        start (int): The index in the original string where the post‑match
            region begins.
    """
    def __init__(self, match, start):
        super().__init__(match)
        self.data = match.string[start:]


def get_generic_error_msg(instance, fmt, *other):
    """
    Constructs a standardized error message string for the given instance.

    The function prefixes the message with the class name of the instance,
    formatted as "<ClassName>Error", and then applies the provided format
    string `fmt` along with any additional arguments. This produces a
    consistent error‑message structure across different classes.

    Example output:
        "MyClassError - invalid value: 42"

    Args:
        instance: The object whose class name is used as the error prefix.
        fmt (str): A format string describing the error message body.
        *other: Additional values to be interpolated into `fmt`.

    Returns:
        str: A fully formatted error message string.
    """
    args = ['%sError' % instance.__class__.__name__]
    args.extend(other)
    new_fmt = '%%s - %s' % fmt
    err_msg = new_fmt % tuple(args)
    return err_msg


def get_whitespace_chars(k=8, to_list=True):
    """
    Returns all Unicode characters within the range 0 to 2**k that are
    recognized as whitespace by the regular‑expression engine.

    The function scans the first 2**k code points and collects every character
    for which ``re.search(r"\\s", char)`` succeeds. This is useful for
    determining which whitespace characters Python's regex engine treats as
    whitespace in a given Unicode range.

    Args:
        k (int): The exponent defining the upper bound of the scanned Unicode
            range. Characters from 0 to 2**k (exclusive) are tested.
        to_list (bool): If True, the result is returned as a ``frozenset`` of
            characters. If False, the characters are concatenated into a
            single string.

    Returns:
        frozenset[str] | str: The collection of detected whitespace characters,
        either as a set or a concatenated string depending on ``to_list``.
    """
    lst = [chr(i) for i in range(pow(2, k)) if re.search(r"\s", chr(i))]
    return frozenset(lst) if to_list else str.join('', lst)


ASCII_WHITESPACE_CHARS = get_whitespace_chars(k=8, to_list=True)
ASCII_WHITESPACE_STRING = get_whitespace_chars(k=8, to_list=False)
WHITESPACE_CHARS = get_whitespace_chars(k=16, to_list=True)
WHITESPACE_STRING = get_whitespace_chars(k=16, to_list=False)


def get_non_whitespace_chars(k=8, to_list=True):
    """
    Returns all Unicode characters within the range 0 to 2**k that are *not*
    recognized as whitespace by the regular‑expression engine.

    The function scans the first 2**k code points and collects every character
    for which ``re.search(r"\\s", char)`` fails. This provides a quick way to
    inspect which characters Python's regex engine treats as non‑whitespace
    within a given Unicode slice.

    Args:
        k (int): The exponent defining the upper bound of the scanned Unicode
            range. Characters from 0 to 2**k (exclusive) are tested.
        to_list (bool): If True, the result is returned as a ``frozenset`` of
            characters. If False, the characters are concatenated into a
            single string.

    Returns:
        frozenset[str] | str: The collection of detected non‑whitespace
        characters, either as a set or a concatenated string depending on
        ``to_list``.
    """
    lst = [chr(i) for i in range(pow(2, k)) if not re.search(r"\s", chr(i))]
    return frozenset(lst) if to_list else str.join('', lst)


ASCII_NON_WHITESPACE_CHARS = get_non_whitespace_chars(k=8, to_list=True)
ASCII_NON_WHITESPACE_STRING = get_non_whitespace_chars(k=8, to_list=False)
NON_WHITESPACE_CHARS = get_non_whitespace_chars(k=16, to_list=True)
NON_WHITESPACE_STRING = get_non_whitespace_chars(k=16, to_list=False)


def do_soft_regex_escape(pattern):
    """
    Performs a controlled, "soft" escaping of characters for use in regular
    expressions.

    Unlike ``re.escape()``, which escapes nearly all non‑alphanumeric
    characters, this function selectively escapes only those characters that
    must be escaped for safe regex usage. Characters that appear in
    ``string.punctuation`` but are not regex metacharacters are left
    unescaped, preserving readability and producing more concise patterns.

    The function iterates through each character in the input string,
    conditionally escaping it based on two checks:
        • Characters that are true regex metacharacters (e.g., ``^ $ . ? * + | { } [ ] ( )``)
          are always escaped.
        • Other punctuation characters are left as‑is unless ``re.escape`` is
          required for correctness.

    The resulting pattern is validated by compiling it with ``re.compile`` to
    ensure it is syntactically valid.

    Args:
        pattern (str): The raw text to be converted into a safely usable
            regular‑expression fragment.

    Returns:
        str: A regex‑safe version of the input string with only the necessary
        characters escaped.
    """
    chk1 = f'{string.punctuation} '
    chk2 = '^$.?*+|{}[]()\\'
    result = []
    for char in pattern:
        escape_char = re.escape(char)
        if char in chk1:
            result.append(escape_char if char in chk2 else char)
        else:
            result.append(escape_char)
    new_pattern = ''.join(result)
    re.compile(new_pattern)
    return new_pattern


def enclose_string(text, quote='"', is_new_line=False):
    """
    Wraps the given text in either single quotes or triple quotes, with
    optional newline formatting for multi‑line content.

    The function first escapes any occurrences of the chosen quote character
    within the text. If the input contains multiple lines, it is enclosed in
    triple quotes (e.g., `'''text'''`). When `is_new_line` is True, the
    enclosed text is placed on its own line between the opening and closing
    triple quotes. Single‑line input is enclosed using a single pair of the
    specified quote character.

    Args:
        text (str): The text to enclose.
        quote (str): The quote character to use (default is `"`). This
            character is repeated three times for triple‑quoted output.
        is_new_line (bool): If True, multi‑line text is placed on a new line
            inside the triple‑quoted block.

    Returns:
        str: The text wrapped in either single or triple quotes, with internal
        quote characters escaped as needed.
    """
    text = str(text)
    reformat_txt = text.replace(quote, '\\' + quote)

    if len(re.split(r'\r?\n|\r', text)) > 1:
        fmt = f'{quote*3}\n%s\n{quote*3}' if is_new_line else f'{quote*3}%s{quote*3}'
        enclosed_txt = fmt % reformat_txt
        return enclosed_txt
    else:
        enclosed_txt = f'{quote}{reformat_txt}{quote}'
        return enclosed_txt


def dedent_and_strip(txt):
    """
    Convert input to string, remove common leading indentation, and strip
    leading/trailing whitespace.

    Parameters
    ----------
    txt : str
        The input object to process. It will be converted to a string
        before unindenting and stripping.

    Returns
    -------
    str
        A new string with common leading indentation removed and
        leading/trailing whitespace stripped.

    Notes
    -----
    This function is useful for normalizing multi-line text blocks
    (e.g., docstrings, templates) so they can be compared or displayed
    consistently.
    """
    new_txt = dedent(str(txt)).strip()
    return new_txt
