"""
genericlib.constpattern
=======================

Regular expression pattern constants for text parsing and validation.

This module centralizes reusable regex strings that are frequently used
throughout the `genericlib` package. By defining named constants for common
patterns (whitespace, digits, words, punctuation, etc.), it avoids scattering
hardcoded regex literals across the codebase and improves readability,
maintainability, and consistency.

Key Components
--------------
- PATTERN:
    A class containing categorized regex constants for general wildcards,
    whitespace, line breaks, digits, letters, punctuation, words, phrases,
    mixed content, and non-whitespace groups. These constants are defined as
    raw regex strings and can be used directly with Python's `re` module.

- get_ref_pattern_by_name:
    A helper function that retrieves a regex pattern constant from `PATTERN`
    by name (case-insensitive). Provides a default fallback if the requested
    pattern is not found.

Use Cases
---------
- Simplifying regex usage in parsing and validation tasks.
- Providing consistent patterns for whitespace handling, tokenization, and
  text normalization.
- Reducing duplication of regex literals across modules.
"""


class PATTERN:
    """
    Regular expression pattern constants for genericlib.

    This class centralizes regex strings used for parsing and validating
    text. It defines reusable patterns for whitespace, digits, numbers,
    letters, punctuation, words, phrases, and mixed content. By providing
    named constants, it avoids hardcoding regex literals throughout the
    codebase and improves readability.

    Categories
    ----------
    General
        ANYTHING, ZOANYTHING, SOMETHING, EVERYTHING
        Basic wildcard patterns ('.', '.?', '.*', '.+').
    Spaces & Whitespace
        SPACE, SPACES, MTONESPACES, MORETHANONESPACES, ATLONESPACES,
        ATLEASTONESPACES, ZOSPACE, ZOSPACES, SPACEATSOS, SPACESATSOS,
        SPACEATEOS, SPACESATEOS
        Patterns for single/multiple spaces, optional spaces, and spaces
        at start/end of string.
        WHITESPACE, WHITESPACES, ZOWHITESPACES
        Regex for whitespace characters.
    Line Breaks
        CRNL, CR_NL, MULTICRNL, ZOMULTICRNL
        Patterns for carriage return/newline combinations.
    Digits & Numbers
        DIGIT, DIGITS, NUMBER, MIXED_NUMBER
        Patterns for numeric values and mixed numeric formats.
    Letters & Alphanumerics
        LETTER, LETTERS, ALPHABET_NUMERIC
        Patterns for alphabetic and alphanumeric characters.
    Punctuation
        PUNCT, PUNCTS, PUNCTS_OR_PHRASE, PUNCTS_OR_GROUP,
        PUNCTS_PHRASE, PUNCTS_GROUP, CHECK_PUNCT, CHECK_PUNCTS,
        CHECK_PUNCTS_GROUP, SPACE_PUNCT, MULTI_SPACE_PUNCTS
        Regex for punctuation characters and grouped punctuation.
    Graphical Characters
        GRAPH
        Pattern for visible ASCII characters.
    Words & Phrases
        WORD, WORDS, PHRASE, WORD_OR_GROUP, WORD_GROUP
        Patterns for words, phrases, and grouped words.
    Mixed Content
        MIXED_WORD, MIXED_WORDS, MIXED_PHRASE, MIXED_WORD_OR_GROUP,
        MIXED_WORD_GROUP
        Patterns for mixed alphanumeric and symbol content.
    Non-Whitespace
        NON_WHITESPACE, NON_WHITESPACES, NON_WHITESPACES_OR_PHRASE,
        NON_WHITESPACES_PHRASE, NON_WHITESPACES_OR_GROUP,
        NON_WHITESPACES_GROUP
        Patterns for non-whitespace characters in various groupings.

    Notes
    -----
    - All constants are defined as raw regex strings.
    - Use these patterns with Python's `re` module for matching,
      searching, or validation.

    Examples
    --------
    >>> import re
    >>> re.match(PATTERN.DIGITS, "12345") is not None
    True

    >>> re.match(PATTERN.WORDS, "hello world") is not None
    True
    """

    ANYTHING = '.'
    ZOANYTHING = '.?'
    SOMETHING = '.*'
    EVERYTHING = '.+'

    SPACE = ' '
    SPACES = ' +'
    MTONESPACES = '  +'
    MORETHANONESPACES = MTONESPACES
    ATLONESPACES = '  +'
    ATLEASTONESPACES = ATLONESPACES
    ZOSPACE = ' ?'
    ZOSPACES = ' *'
    SPACEATSOS = '^ '
    SPACESATSOS = '^ +'
    SPACEATEOS = ' $'
    SPACESATEOS = ' +$'

    WHITESPACE = r'\s'
    WHITESPACES = r'\s+'
    ZOWHITESPACES = r'\s*'

    CRNL = r'\r?\n|\r'
    CR_NL = CRNL
    MULTICRNL = r'[\r\n]+'
    ZOMULTICRNL = r'[\r\n]*'

    DIGIT = r'\d'
    DIGITS = '%s+' % DIGIT

    NUMBER = r'\d*[.]?\d+'
    MIXED_NUMBER = r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'

    LETTER = '[a-zA-Z]'
    LETTERS = '%s+' % LETTER

    ALPHABET_NUMERIC = '[a-zA-Z0-9]'

    PUNCT = r'[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    PUNCTS = '%s+' % PUNCT
    PUNCTS_OR_PHRASE = '%s( %s)*' % (PUNCTS, PUNCTS)
    PUNCTS_OR_GROUP = '%s( +%s)*' % (PUNCTS, PUNCTS)
    PUNCTS_PHRASE = '%s( %s)+' % (PUNCTS, PUNCTS)
    PUNCTS_GROUP = '%s( +%s)+' % (PUNCTS, PUNCTS)
    CHECK_PUNCT = '%s$' % PUNCT
    CHECK_PUNCTS = '%s$' % PUNCTS
    CHECK_PUNCTS_GROUP = ' *%s *$' % PUNCTS_GROUP

    SPACE_PUNCT = r'[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    MULTI_SPACE_PUNCTS = '%s+' % SPACE_PUNCT

    GRAPH = r'[\x21-\x7e]'

    WORD = r'[a-zA-Z][a-zA-Z0-9]*'
    WORDS = r'%s( %s)*' % (WORD, WORD)
    PHRASE = r'%s( %s)+' % (WORD, WORD)
    WORD_OR_GROUP = r'%s( +%s)*' % (WORD, WORD)
    WORD_GROUP = r'%s( +%s)+' % (WORD, WORD)

    MIXED_WORD = r'[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*'
    MIXED_WORDS = '%s( %s)*' % (MIXED_WORD, MIXED_WORD)
    MIXED_PHRASE = '%s( %s)+' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_OR_GROUP = '%s( +%s)*' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_GROUP = '%s( +%s)+' % (MIXED_WORD, MIXED_WORD)

    NON_WHITESPACE = r'\S'
    NON_WHITESPACES = r'%s+' % NON_WHITESPACE
    NON_WHITESPACES_OR_PHRASE = r'%s( %s)*' % (NON_WHITESPACES, NON_WHITESPACES)
    NON_WHITESPACES_PHRASE = r'%s( %s)+' % (NON_WHITESPACES, NON_WHITESPACES)
    NON_WHITESPACES_OR_GROUP = r'%s( +%s)*' % (NON_WHITESPACES, NON_WHITESPACES)
    NON_WHITESPACES_GROUP = r'%s( +%s)+' % (NON_WHITESPACES, NON_WHITESPACES)


def get_ref_pattern_by_name(name, default=None):
    """
    Retrieve a regex pattern constant by name.

    Converts the given name to uppercase and looks up the corresponding
    attribute in the `PATTERN` class. If the name is not found, returns
    the provided default or `PATTERN.NON_WHITESPACES_OR_GROUP`.

    Parameters
    ----------
    name : str
        The name of the pattern constant (case-insensitive).
    default : str, optional
        A fallback regex pattern if the name is not found. Defaults to
        `PATTERN.NON_WHITESPACES_OR_GROUP`.

    Returns
    -------
    str
        The regex pattern string associated with the given name.

    Examples
    --------
    >>> get_ref_pattern_by_name("digit")
    '\\d'

    >>> get_ref_pattern_by_name("unknown", default=PATTERN.WORD)
    '[a-zA-Z][a-zA-Z0-9]*'
    """
    default = default or PATTERN.NON_WHITESPACES_OR_GROUP
    attr = name.upper()
    pattern = getattr(PATTERN, attr, default)
    return pattern
