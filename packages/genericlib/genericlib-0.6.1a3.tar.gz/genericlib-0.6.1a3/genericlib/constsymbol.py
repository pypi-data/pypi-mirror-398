"""
genericlib.constsymbol
======================

Symbolic constants for the `genericlib` package.

This module centralizes commonly used symbolic characters as named constants.
By defining symbols in one place, it avoids scattering literal characters
throughout the codebase, improves readability, and ensures consistency when
working with punctuation, operators, delimiters, and other symbolic tokens.

Key Components
--------------
- SYMBOL:
    A class containing reusable constants for symbolic characters such as
    punctuation marks, mathematical operators, grouping symbols, and other
    special characters frequently used in parsing, formatting, or validation.

Use Cases
---------
- Replace hardcoded characters (e.g., `"+"`, `"-"`, `"="`) with descriptive
  constants for clarity.
- Provide consistent references to symbols across modules.
- Simplify parsing and validation logic by using named constants instead of
  inline literals.

"""


class SYMBOL:
    """
    Common symbol and punctuation constants for genericlib.

    This class centralizes frequently used symbolic characters to
    ensure consistency across the library. It includes operators,
    whitespace, punctuation marks, and bracket types, with aliases
    provided for readability in different contexts.

    Members
    -------
    PIPE, VERTICAL_LINE : str
        Vertical bar ("|").
    FORWARD_SLASH, BACK_SLASH : str
        Forward slash ("/") and backslash ("\\").
    SPACE : str
        Single space character.
    PLUS : str
        Plus sign ("+").
    ASTERISK, STAR, MULTIPLY : str
        Asterisk ("*"), with aliases for clarity in math or regex contexts.
    COMMA : str
        Comma (",").
    CARET : str
        Caret ("^").
    DOLLAR_SIGN : str
        Dollar sign ("$").
    QUESTION_MARK : str
        Question mark ("?").
    LEFT_PARENTHESIS, RIGHT_PARENTHESIS,
    LEFT_ROUND_BRACKET, RIGHT_ROUND_BRACKET : str
        Parentheses ("(", ")"), with aliases for round brackets.
    LEFT_CURLY_BRACKET, RIGHT_CURLY_BRACKET : str
        Curly braces ("{", "}").
    LEFT_SQUARE_BRACKET, RIGHT_SQUARE_BRACKET : str
        Square brackets ("[", "]").
    LEFT_ANGLE_BRACKET, RIGHT_ANGLE_BRACKET : str
        Angle brackets ("<", ">").

    Notes
    -----
    - Aliases (e.g., STAR, MULTIPLY) are provided to improve semantic
      clarity depending on usage context.
    - Centralizing symbols avoids repeated hardcoding and reduces
      risk of typos.

    Examples
    --------
    >>> SYMBOL.PIPE
    '|'

    >>> SYMBOL.LEFT_SQUARE_BRACKET + "item" + SYMBOL.RIGHT_SQUARE_BRACKET
    '[item]'

    >>> regex = SYMBOL.CARET + "pattern" + SYMBOL.DOLLAR_SIGN
    '^pattern$'
    """
    PIPE = '|'
    VERTICAL_LINE = '|'

    FORWARD_SLASH = '/'
    BACK_SLASH = '\\'

    SPACE = ' '

    PLUS = '+'
    ASTERISK = '*'
    STAR = '*'
    MULTIPLY = '*'
    COMMA = ','

    CARET = '^'

    DOLLAR_SIGN = '$'

    QUESTION_MARK = '?'

    LEFT_PARENTHESIS = '('
    RIGHT_PARENTHESIS = ')'
    LEFT_ROUND_BRACKET = '('
    RIGHT_ROUND_BRACKET = ')'

    LEFT_CURLY_BRACKET = '{'
    RIGHT_CURLY_BRACKET = '}'

    LEFT_SQUARE_BRACKET = '['
    RIGHT_SQUARE_BRACKET = ']'

    LEFT_ANGLE_BRACKET = '<'
    RIGHT_ANGLE_BRACKET = '>'
