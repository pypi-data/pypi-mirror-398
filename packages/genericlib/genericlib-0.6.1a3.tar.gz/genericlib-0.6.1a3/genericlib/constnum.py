"""
genericlib.constnum
===================

Numeric and index constants for the `genericlib` package.

This module defines commonly used integer values as named constants to improve
readability and reduce the need for hardcoded numbers throughout the codebase.
It provides two complementary classes:

- NUMBER:
    General-purpose numeric constants (digits, teens, multiples of ten, and
    larger values such as hundred and thousand). These constants are useful
    wherever explicit numeric values are required.

- INDEX:
    Mirrored numeric constants intended specifically for indexing contexts
    (e.g., array positions, loop counters, or ordered identifiers). By using
    named constants instead of raw integers, code becomes more descriptive
    and self-documenting.

Use Cases
---------
- Replace "magic numbers" with descriptive constants.
- Improve clarity in loops, ranges, and indexing operations.
- Provide consistent numeric references across the package.
"""


class NUMBER:
    """
    Numeric constants for genericlib.

    This class defines commonly used integer values as named constants,
    improving readability and reducing the need to hardcode numbers
    throughout the codebase. It includes single digits, teens, tens,
    and larger values such as hundred and thousand.

    Members
    -------
    ZERO–NINE : int
        Constants for digits 0 through 9.
    TEN–NINETEEN : int
        Constants for numbers 10 through 19.
    TWENTY, THIRTY, FORTY, FIFTY, SIXTY, SEVENTY, EIGHTY, NINETY : int
        Constants for multiples of ten.
    HUNDRED : int
        Constant for 100.
    THOUSAND : int
        Constant for 1000.

    Examples
    --------
    >>> NUMBER.FIVE
    5

    >>> NUMBER.HUNDRED + NUMBER.TWENTY
    120
    """
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    ELEVEN = 11
    TWELVE = 12
    THIRTEEN = 13
    FOURTEEN = 14
    FIFTEEN = 15
    SIXTEEN = 16
    SEVENTEEN = 17
    EIGHTEEN = 18
    NINETEEN = 19
    TWENTY = 20
    THIRTY = 30
    FORTY = 40
    FIFTY = 50
    SIXTY = 60
    SEVENTY = 70
    EIGHTY = 80
    NINETY = 90
    HUNDRED = 100
    THOUSAND = 1000


class INDEX:
    """
    Index constants for genericlib.

    This class mirrors the numeric constants defined in `NUMBER` but is
    intended for use in indexing contexts (e.g., array positions, loop
    counters, or ordered identifiers). By providing named constants,
    it improves clarity when referring to positions rather than raw
    integers.

    Members
    -------
    ZERO–NINE : int
        Constants for indices 0 through 9.
    TEN–NINETEEN : int
        Constants for indices 10 through 19.
    TWENTY, THIRTY, FORTY, FIFTY, SIXTY, SEVENTY, EIGHTY, NINETY : int
        Constants for multiples of ten.
    HUNDRED : int
        Constant for index 100.
    THOUSAND : int
        Constant for index 1000.

    Examples
    --------
    >>> data = ["a", "b", "c"]
    >>> data[INDEX.ZERO]
    'a'

    >>> range(INDEX.TEN)
    range(0, 10)
    """
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    ELEVEN = 11
    TWELVE = 12
    THIRTEEN = 13
    FOURTEEN = 14
    FIFTEEN = 15
    SIXTEEN = 16
    SEVENTEEN = 17
    EIGHTEEN = 18
    NINETEEN = 19
    TWENTY = 20
    THIRTY = 30
    FORTY = 40
    FIFTY = 50
    SIXTY = 60
    SEVENTY = 70
    EIGHTY = 80
    NINETY = 90
    HUNDRED = 100
    THOUSAND = 1000
