"""
genericlib.constant
===================

Constants and utility classes for genericlib.

This module centralizes constant definitions and supporting logic
used throughout the library. It provides:

- Case/space-insensitive string comparison utilities (`ICSValue`,
  `ICSStripValue`).
- Execution codes (`ECODE`) for success/failure reporting.
- Common string constants (`STRING`, `LSSTRING`, `TEXT`) for
  standardized values used in parsing, validation, and metadata.

Classes
-------
ICSValue : object
    Utility for evaluating string equality while ignoring case and
    collapsing multiple spaces. Supports optional regex-based
    equality checks and stripping.
ICSStripValue : ICSValue
    Variant of `ICSValue` that also strips leading/trailing whitespace
    before comparison.
ECODE : enum.IntFlag
    Execution codes for status reporting:
    - SUCCESS (0)
    - BAD (1)
    - PASSED (alias for SUCCESS)
    - FAILED (alias for BAD)
STRING : object
    Collection of common string constants (e.g., newline, space,
    punctuation, keywords).
LSSTRING : object
    Logical string constants defined using `ICSStripValue` for
    case/space-insensitive evaluation of boolean values.
TEXT : object
    Constants representing text categories (digits, words, phrases,
    punctuation, etc.) for parsing and validation contexts.

Aliases
-------
STR : STRING
    Shortcut alias for `STRING`.
"""

import re
from enum import IntFlag


class ICSValue:
    """
    A utility class for case-insensitive and space-insensitive string comparison.

    This class wraps a string value and provides customized equality checks
    that ignore differences in letter case and normalize multiple spaces.
    Optionally, leading/trailing whitespace can be stripped, and equality
    can be evaluated against regex patterns or explicit values.

    Parameters
    ----------
    value : str
        The string value to wrap and compare.
    equality : str or list or tuple, optional
        A regex pattern or collection of patterns/values used to evaluate
        equality against other strings. Defaults to '' (no pattern).
    stripped : bool, optional
        If True, leading and trailing whitespace is removed before comparison.
        Defaults to False.

    Notes
    -----
    - Comparisons normalize multiple spaces into a single space.
    - If `equality` is provided, comparisons are performed against the
      specified regex pattern(s) or values.
    - Supports comparison with both raw strings and other `ICSValue` instances.

    Examples
    --------
    >>> ICSValue("Hello   World") == "hello world"
    True

    >>> ICSValue("Test", equality="^te.*$") == "TEsting"
    True

    >>> ICSValue("  value  ", stripped=True) == "VALUE"
    True
    """
    def __init__(self, value, equality='', stripped=False):
        """
        Initialize an ICSValue instance for case-insensitive and
        space-normalized string comparison.

        Parameters
        ----------
        value : str
            The string value to wrap. It will be converted to a string
            internally if not already.
        equality : str or list or tuple, optional
            A regex pattern or collection of patterns/values used to
            evaluate equality against other strings. Defaults to an empty
            string, meaning direct normalized comparison is used.
        stripped : bool, optional
            If True, leading and trailing whitespace is removed from both
            values before comparison. Defaults to False.

        Notes
        -----
        - All comparisons are performed in lowercase.
        - Multiple spaces are collapsed into a single space.
        - If `equality` is provided, comparisons are performed against
          regex patterns (case-insensitive) or literal values.

        Examples
        --------
        >>> v = ICSValue("Hello   World")
        >>> v == "hello world"
        True

        >>> v = ICSValue("Test", equality="^te.*$")
        >>> v == "TEsting"
        True

        >>> v = ICSValue("  value  ", stripped=True)
        >>> v == "VALUE"
        True
        """
        self.value = str(value)
        self.equality = equality
        self.stripped = stripped

    def __eq__(self, other):
        """
        Compare this value with another for equality, ignoring case and
        normalizing whitespace.

        The comparison logic:
        - Converts both values to lowercase.
        - Collapses multiple spaces into a single space.
        - Optionally strips leading/trailing whitespace if `stripped=True`.
        - If `equality` is provided:
            * If it is a list/tuple, each item is treated as a regex pattern
              or literal string to match against `other`.
            * If it is a single string, it is treated as a regex pattern
              (case-insensitive). If regex fails, falls back to literal
              string comparison.
        - If `equality` is not provided, performs a direct normalized
          string comparison.

        Parameters
        ----------
        other : str or ICSValue
            The value to compare against. Can be a raw string or another
            `ICSValue` instance.

        Returns
        -------
        bool
            True if the values are considered equal under the rules above,
            False otherwise.

        Examples
        --------
        >>> ICSValue("Hello   World") == "hello world"
        True

        >>> ICSValue("Test", equality="^te.*$") == "TEsting"
        True

        >>> ICSValue("  value  ", stripped=True) == "VALUE"
        True
        """
        value1 = self.value.lower()

        if isinstance(other, self.__class__):
            value2 = other.value.lower()
        else:
            value2 = str(other).lower()

        value1 = re.sub(' +', ' ', value1)
        value2 = re.sub(' +', ' ', value2)

        if self.stripped:
            value1 = value1.strip()
            value2 = value2.strip()

        if self.equality:
            if isinstance(self.equality, (list, tuple)):
                is_equal = True
                for item in self.equality:
                    item = str(item)
                    try:
                        is_equal = bool(re.match(item, value2, re.I))
                    except Exception as ex:     # noqa
                        item = re.sub(' +', ' ', item.lower())
                        is_equal &= item == value2
                return is_equal
            else:
                pattern = str(self.equality)
                try:
                    is_equal = bool(re.match(pattern, value2, re.I))
                except Exception as ex:     # noqa
                    equality = re.sub(' +', ' ', str(self.equality).lower())
                    is_equal = equality == value2
                return is_equal
        else:
            chk = value1 == value2
        return chk

    def __repr__(self):
        """
        Return the official string representation of the ICSValue instance.

        This method returns the `repr()` of the underlying string value,
        making it suitable for debugging and logging. It ensures that
        when an `ICSValue` object is printed in interactive sessions
        or inspected, the wrapped string is displayed in a clear,
        unambiguous form.

        Returns
        -------
        str
            The `repr()` of the stored string value.

        Examples
        --------
        >>> v = ICSValue("Hello World")
        >>> repr(v)
        "'Hello World'"
        """
        return repr(self.value)

    def __str__(self):
        """
        Return the user-friendly string representation of the ICSValue instance.

        Unlike `__repr__`, which is intended for debugging, this method
        returns the raw stored string value directly. It provides a clean,
        human-readable representation suitable for display, logging, or
        text output.

        Returns
        -------
        str
            The underlying string value stored in the ICSValue instance.

        Examples
        --------
        >>> v = ICSValue("Hello World")
        >>> str(v)
        'Hello World'
        """
        return self.value


class ICSStripValue(ICSValue):
    """
    A specialized variant of ICSValue that performs case-insensitive,
    space-normalized, and whitespace-stripped string comparison.

    This class behaves like `ICSValue` but always removes leading and
    trailing whitespace before evaluating equality. It is useful when
    comparing values where surrounding spaces should be ignored in
    addition to case and spacing differences.

    Parameters
    ----------
    value : str
        The string value to wrap and compare.
    equality : str or list or tuple, optional
        A regex pattern or collection of patterns/values used to
        evaluate equality against other strings. Defaults to ''.

    Notes
    -----
    - Comparisons are case-insensitive.
    - Multiple spaces are collapsed into a single space.
    - Leading and trailing whitespace is always stripped.

    Examples
    --------
    >>> ICSStripValue("  Hello   World  ") == "hello world"
    True

    >>> ICSStripValue("Value", equality="^val.*$") == "VALUE123"
    True
    """
    def __init__(self, value, equality=''):
        super().__init__(value, equality=equality, stripped=True)


class ECODE(IntFlag):
    """
    Execution status codes for genericlib.

    This enumeration defines symbolic constants for representing
    success and failure states in a standardized way. It inherits
    from `enum.IntFlag`, allowing bitwise operations if needed.

    Members
    -------
    SUCCESS : int
        Indicates successful execution (value = 0).
    BAD : int
        Indicates failed execution (value = 1).
    PASSED : int
        Alias for SUCCESS, provided for semantic clarity.
    FAILED : int
        Alias for BAD, provided for semantic clarity.

    Notes
    -----
    - Using named constants improves readability compared to raw
      integers (e.g., `sys.exit(ECODE.SUCCESS)` instead of `sys.exit(0)`).
    - Aliases (`PASSED`, `FAILED`) make code more expressive in
      testing or reporting contexts.

    Examples
    --------
    >>> ECODE.SUCCESS
    <ECODE.SUCCESS: 0>

    >>> ECODE.FAILED == ECODE.BAD
    True

    >>> import sys
    >>> sys.exit(ECODE.SUCCESS)  # exit with success code
    """
    SUCCESS = 0
    BAD = 1
    PASSED = SUCCESS
    FAILED = BAD


class STRING:
    """
    Common string constants for genericlib.

    This class centralizes frequently used string values to ensure
    consistency across the library. It includes symbols, whitespace
    characters, keywords, and identifiers used in parsing, validation,
    and metadata handling.

    Members
    -------
    EMPTY : str
        Empty string ("").
    NEWLINE : str
        Newline character ("\n").
    LINEFEED : str
        Line feed character ("\n").
    CARRIAGE_RETURN : str
        Carriage return character ("\r").
    TRUE : str
        Literal "True".
    FALSE : str
        Literal "False".
    FORWARD_FLASH : str
        Forward slash ("/").
    EQUAL_SYMBOL : str
        Equal sign ("=").
    SPACE_CHAR : str
        Single space (" ").
    DOUBLE_SPACES : str
        Two consecutive spaces ("  ").
    DOT_CHAR : str
        Dot character (".").
    UNDERSCORE_CHAR : str
        Underscore ("_").
    COLON_CHAR : str
        Colon (":").
    COMMA_CHAR : str
        Comma (",").
    ...
    ...
    ...
    """
    EMPTY = ''
    NEWLINE = '\n'
    LINEFEED = '\n'
    CARRIAGE_RETURN = '\r'
    TRUE = 'True'
    FALSE = 'False'
    FORWARD_FLASH = '/'
    EQUAL_SYMBOL = '='
    SPACE_CHAR = ' '
    DOUBLE_SPACES = '  '
    DOT_CHAR = '.'
    UNDERSCORE_CHAR = '_'
    COLON_CHAR = ':'
    COMMA_CHAR = ','

    CMDLINE = 'cmdline'
    CMDLINES = 'cmdlines'
    NAME = 'name'
    DESCRIPTION = 'description'
    LOGIN = 'login'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'
    SUBMIT = 'submit'

    START = 'start'
    END = 'end'
    MIDDLE = 'middle'
    FIRST = 'first'
    LAST = 'last'

    EXECUTION = 'execution'
    BATCH = 'batch'
    TEST_SCRIPT = 'test_script'
    STATIC = 'static'
    HIDDEN_INPUT_FIELD = 'hidden_input_field'
    TEMPLATE_RESULT = 'template_result'
    SCRIPT_RESULT = 'script_result'
    SEARCHED_TEMPLATE = 'searched_template'
    BUILT_TEMPLATE = 'built_template'
    BUILT_SCRIPT = 'built_script'
    SAVED_TEMPLATE = 'saved_template'
    ITERATIVE_TEST = 'iterative_test'
    ITERATIVE_RESULT = 'iterative_result'
    BATCH_ACTION = 'batch_action'
    BATCH_RESULT = 'batch_result'
    ROBOT = 'robot'
    PY = 'py'
    TEST_ = 'test_'

    UNSUPPORTED_PARSING = 'unsupported parsing'


STR = STRING


class LSSTRING:
    """
    Logical string constants with case-insensitive and space-stripped comparison.

    This class defines boolean-like string values (`TRUE`, `FALSE`) using
    `ICSStripValue`, ensuring that comparisons ignore case, normalize
    whitespace, and strip leading/trailing spaces. It provides a consistent
    way to evaluate textual representations of truth values across the
    library.

    Members
    -------
    TRUE : ICSStripValue
        Represents the string "true" in a case-insensitive, space-stripped form.
    FALSE : ICSStripValue
        Represents the string "false" in a case-insensitive, space-stripped form.

    Examples
    --------
    >>> LSSTRING.TRUE == " True "
    True

    >>> LSSTRING.FALSE == "FALSE"
    True
    """
    TRUE = ICSStripValue('true')
    FALSE = ICSStripValue('false')


class TEXT:
    """
    Text category constants for genericlib.

    This class defines standardized string labels representing
    categories of textual elements. These constants are used in
    parsing, validation, and classification tasks to ensure
    consistency across the library.

    Members
    -------
    ALPHABET_NUMERIC : str
        Label for alphanumeric content.

    DIGIT, DIGITS : str
        Labels for single or multiple digits.

    GRAPH : str
        Label for graphical characters.

    LETTER, LETTERS : str
        Labels for single or multiple alphabetic characters.

    NUMBER : str
        Label for numeric values.

    MIXED_NUMBER, MIXED_WORD, MIXED_WORDS, MIXED_WORD_OR_PHRASE,
    MIXED_WORD_OR_GROUP, MIXED_PHRASE, MIXED_WORD_GROUP : str
        Labels for mixed content categories combining numbers,
        words, or phrases.

    NON_WHITESPACE, NON_WHITESPACES, NON_WHITESPACES_OR_PHRASE,
    NON_WHITESPACES_OR_GROUP, NON_WHITESPACES_PHRASE,
    NON_WHITESPACES_GROUP : str
        Labels for non-whitespace content, in singular, plural,
        phrase, or group forms.

    PUNCT, PUNCTS, PUNCTS_OR_PHRASE, PUNCTS_OR_GROUP,
    PUNCTS_PHRASE, PUNCTS_GROUP : str
        Labels for punctuation characters, in singular, plural,
        phrase, or group forms.

    WORD, WORDS, WORD_OR_PHRASE, WORD_OR_GROUP, PHRASE,
    WORD_GROUP : str
        Labels for word-based content, including single words,
        multiple words, phrases, or grouped words.

    Notes
    -----
    - These constants provide a unified vocabulary for describing
      text structures.
    - Using centralized labels avoids hard-coding and improves
      readability in parsing logic.
    """
    ALPHABET_NUMERIC = 'alphabet_numeric'

    DIGIT = 'digit'
    DIGITS = 'digits'

    GRAPH = 'graph'

    LETTER = 'letter'
    LETTERS = 'letters'

    NUMBER = 'number'

    MIXED_NUMBER = 'mixed_number'
    MIXED_WORD = 'mixed_word'
    MIXED_WORDS = 'mixed_words'
    MIXED_WORD_OR_PHRASE = 'mixed_word_or_phrase'
    MIXED_WORD_OR_GROUP = 'mixed_word_or_group'
    MIXED_PHRASE = 'mixed_phrase'
    MIXED_WORD_GROUP = 'mixed_word_group'

    NON_WHITESPACE = 'non_whitespace'
    NON_WHITESPACES = 'non_whitespaces'
    NON_WHITESPACES_OR_PHRASE = 'non_whitespace_or_phrase'
    NON_WHITESPACES_OR_GROUP = 'non_whitespace_or_group'
    NON_WHITESPACES_PHRASE = 'non_whitespace_phrase'
    NON_WHITESPACES_GROUP = 'non_whitespace_group'

    PUNCT = 'punct'
    PUNCTS = 'puncts'
    PUNCTS_OR_PHRASE = 'puncts_or_phrase'
    PUNCTS_OR_GROUP = 'puncts_or_group'
    PUNCTS_PHRASE = 'puncts_phrase'
    PUNCTS_GROUP = 'puncts_group'

    WORD = 'word'
    WORDS = 'words'
    WORD_OR_PHRASE = 'word_or_phrase'
    WORD_OR_GROUP = 'word_or_group'
    PHRASE = 'phrase'
    WORD_GROUP = 'word_group'
