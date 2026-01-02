"""
genericlib.conststruct
======================

Structural and slice constants for the `genericlib` package.

This module centralizes reusable empty data structures and commonly used
slice objects. By defining these constants in one place, it reduces
duplication, improves readability, and provides a consistent way to
reference frequently used structures and sequence operations.

Key Components
--------------
- STRUCT:
    Provides reusable empty data structures such as an empty list and
    empty dictionary. These constants help avoid repeatedly instantiating
    new empty objects throughout the codebase.

- SLICE:
    Defines commonly used slice objects for indexing lists, strings, and
    other sequence types. Centralizing slice definitions improves clarity
    when accessing sequence elements and reduces reliance on "magic slice"
    literals scattered across the code.

Use Cases
---------
- Replace inline `[]` or `dict()` with descriptive constants for clarity.
- Use predefined slices (`[:1]`, `[-1:]`, `[1:]`, etc.) to make indexing
  operations more self-documenting.
- Simplify code that frequently manipulates sequences by using named slice
  constants instead of hardcoded slice expressions.
"""


from genericlib.constnum import NUMBER


class STRUCT:
    """
    Common structural constants for genericlib.

    This class provides reusable empty data structures to avoid
    repeatedly instantiating them throughout the codebase.

    Members
    -------
    EMPTY_LIST : list
        An empty list (`[]`).
    EMPTY_DICT : dict
        An empty dictionary (`dict()`).

    Examples
    --------
    >>> STRUCT.EMPTY_LIST
    []

    >>> STRUCT.EMPTY_DICT
    {}
    """
    EMPTY_LIST = []
    EMPTY_DICT = dict()


class SLICE:
    """
    Predefined slice constants for genericlib.

    This class defines commonly used slice objects for indexing
    lists, strings, and other sequence types. By centralizing
    slice definitions, it improves readability and reduces
    duplication in code that frequently accesses sequence
    elements.

    Members
    -------
    FIRST_ITEM : slice
        Slice for the first element (`[:1]`).
    LAST_ITEM : slice
        Slice for the last element (`[-1:]`).
    GET_FIRST : slice
        Alias for FIRST_ITEM.
    GET_LAST : slice
        Alias for LAST_ITEM.
    EVERYTHING : slice
        Slice for the entire sequence (`[:]`).
    SKIP_FROM_FIRST : slice
        Slice skipping the first element (`[1:]`).
    SKIP_FROM_SECOND : slice
        Slice skipping the first two elements (`[2:]`).
    SKIP_FROM_THIRD : slice
        Slice skipping the first three elements (`[3:]`).
    TAKE_TO_LAST : slice
        Slice up to (but not including) the last element (`[:-1]`).
    TAKE_TO_SECOND_LAST : slice
        Slice up to (but not including) the last two elements (`[:-2]`).
    TAKE_TO_THIRD_LAST : slice
        Slice up to (but not including) the last three elements (`[:-3]`).
    FIRST_TO_LAST : slice
        Slice from the first element to the last (exclusive) (`[1:-1]`).
    SECOND_TO_SECOND_LAST : slice
        Slice from the second element to the second-to-last (exclusive) (`[2:-2]`).
    THIRD_TO_THIRD_LAST : slice
        Slice from the third element to the third-to-last (exclusive) (`[3:-3]`).

    Examples
    --------
    >>> lst = [0, 1, 3, 5]
    >>> lst[SLICE.FIRST_ITEM]
    [0]

    >>> lst[SLICE.LAST_ITEM]
    [5]

    >>> lst[SLICE.SKIP_FROM_SECOND]
    [3, 5]

    >>> "01234567"[SLICE.SECOND_TO_SECOND_LAST]
    '2345'
    """
    FIRST_ITEM = slice(None, NUMBER.ONE)        # e.g., assert [0, 1, 3, 5][SLICE.FIRST_ITEM] == [0]
    LAST_ITEM = slice(-NUMBER.ONE, None)        # e.g., assert [0, 1, 3, 5][SLICE.LAST_ITEM] == [5]

    GET_FIRST = slice(None, NUMBER.ONE)        # e.g., assert [0, 1, 3, 5][SLICE.GET_FIRST] == [0]
    GET_LAST = slice(-NUMBER.ONE, None)        # e.g., assert [0, 1, 3, 5][SLICE.GET_LAST] == [5]

    # e.g., lst = [0, 1, 3, 5]; assert lst[SLICE.EVERYTHING] == lst and id(lst[SLICE.EVERYTHING] != id(lst)
    EVERYTHING = slice(None, None)

    SKIP_FROM_FIRST = slice(NUMBER.ONE, None)           # e.g., assert [0, 1, 3, 5][SLICE.SKIP_FROM_FIRST] == [1, 3, 5]
    SKIP_FROM_SECOND = slice(NUMBER.TWO, None)          # e.g., assert [0, 1, 3, 5][SLICE.SKIP_FROM_SECOND] == [3, 5]
    SKIP_FROM_THIRD = slice(NUMBER.THREE, None)         # e.g., assert [0, 1, 3, 5][SLICE.SKIP_FROM_THIRD] == [5]
    TAKE_TO_LAST = slice(None, -NUMBER.ONE)             # e.g., assert [0, 1, 3, 5][SLICE.TAKE_TO_LAST] == [0, 1, 3]
    TAKE_TO_SECOND_LAST = slice(None, -NUMBER.TWO)      # e.g. assert [0, 1, 3, 5][SLICE.TAKE_TO_SECOND_LAST] == [0, 1]
    TAKE_TO_THIRD_LAST = slice(None, -NUMBER.THREE)     # e.g. assert [0, 1, 3, 5][SLICE.TAKE_TO_THIRD_LAST] == [0]

    # e.g., assert '01234567'[SLICE.FIRST_TO_LAST] == '123456'
    FIRST_TO_LAST = slice(NUMBER.ONE, -NUMBER.ONE)
    # e.g., assert '01234567'[SLICE.SECOND_TO_SECOND_LAST] == '2345'
    SECOND_TO_SECOND_LAST = slice(NUMBER.TWO, -NUMBER.TWO)
    # e.g., assert e.g. '01234567'[SLICE.THIRD_TO_THIRD_LAST] == '4'
    THIRD_TO_THIRD_LAST = slice(NUMBER.THREE, -NUMBER.THREE)
