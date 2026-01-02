"""
genericlib.search
=================

Wildcard parsing and regex conversion utilities.

This module provides tools for interpreting shell-style wildcard expressions
and converting them into valid regular expression (regex) patterns. It is
designed to simplify text matching scenarios where users supply flexible
patterns containing wildcards, bracket expansions, numeric ranges, POSIX
character classes, and whitespace variations.

Key Components
--------------
- Wildcard:
    A parser and converter that transforms wildcard expressions into regex
    patterns. Supports case-insensitivity, relaxed whitespace handling,
    anchoring, and multi-line input. Useful for building search utilities,
    text parsers, and validation logic.

Dependencies
------------
- `re`: Used for regex compilation and matching.
- `genericlib.utils.Misc`: Provides helper functions for type checking and
  validation.
- `genericlib.constant.STRING`, `genericlib.constnum.NUMBER`,
  `genericlib.constsymbol.SYMBOL`, `genericlib.constpattern.PATTERN`,
  `genericlib.conststruct.SLICE`: Shared constants used for parsing and
  pattern construction.

Use Cases
---------
- Converting user-friendly wildcard input into regex for text search.
- Supporting flexible matching in configuration files or command-line tools.
- Parsing structured input with bracket expansions or numeric ranges.
- Handling whitespace variations in user-supplied patterns.

"""


import re

from genericlib.utils import Misc
from genericlib.constant import STRING
from genericlib.constnum import NUMBER
from genericlib.constsymbol import SYMBOL
from genericlib.constpattern import PATTERN

from genericlib.conststruct import SLICE


class Wildcard:
    """
    A parser and converter for shell-style wildcard expressions into
    regular expression (regex) patterns.

    The `Wildcard` class interprets user-supplied strings containing
    wildcards, bracket expansions, numeric ranges, POSIX character
    classes, and whitespace variations, and transforms them into valid
    regex patterns suitable for text matching. It supports both single-line
    and multi-line input, optional case-insensitivity, relaxed
    whitespace handling, and anchoring from start to end.

    Parameters
    ----------
    data : str
        The input string containing wildcard expressions to be parsed.
    is_leading : bool, optional
        If True, allows matching at the beginning of the string (default: False).
    is_trailing : bool, optional
        If True, allows matching at the end of the string (default: False).
    ignore_case : bool, optional
        If True, regex matching will be case-insensitive (default: True).
    relax : bool, optional
        If True, relaxes whitespace handling by treating multiple spaces
        as equivalent (default: False).
    used_whitespace : bool, optional
        If True, preserves explicit whitespace characters in the regex
        pattern; otherwise, normalizes them (default: False).
    from_start_to_end : bool, optional
        If True, anchors the regex pattern to match from start to end of
        the input string (default: True).

    Attributes
    ----------
    pattern : str
        The compiled regex pattern generated from the input data.
    is_multiline : bool
        Indicates whether the input data contains newline characters.
    ws_placeholder : str
        Placeholder token for single whitespace substitution.
    multi_ws_placeholder : str
        Placeholder token for multiple whitespace substitution.
    ws_repl : str
        Regex replacement pattern for single whitespace.
    multi_ws_repl : str
        Regex replacement pattern for multiple whitespace.
    failure_fmt : str
        Format string used when integer parsing fails.

    Key Features
    ------------
    - Escapes special regex characters while preserving wildcard semantics.
    - Expands curly, round, and square bracket expressions.
    - Supports shell-style expansions such as `{a..z}`, `{1..10}`, and `{foo,bar}`.
    - Handles POSIX character classes (e.g., `[:digit:]`, `[:alpha:]`).
    - Provides whitespace normalization and optional relaxed matching.
    - Anchors patterns to start/end when requested.
    - Supports both single-line and multi-line input parsing.

    Notes
    -----
    The class automatically processes the input string during initialization.
    Use the `pattern` property to retrieve the final regex string.
    """
    def __init__(self, data, is_leading=False, is_trailing=False,
                 ignore_case=True, relax=False, used_whitespace=False,
                 from_start_to_end=True):
        self.data = str(data)
        self.is_leading = is_leading
        self.is_trailing = is_trailing
        self.ignore_case = ignore_case
        self.is_multiline = bool(re.search(PATTERN.CRNL, self.data))
        self.relax = relax
        self.used_whitespace = used_whitespace
        self.from_start_to_end = from_start_to_end

        self.ws_placeholder = '__placeholder_whitespace_pat__'
        self.multi_ws_placeholder = '__placeholder_whitespaces_pat__'

        self.ws_repl = PATTERN.WHITESPACE if used_whitespace else PATTERN.SPACE
        self.multi_ws_repl = PATTERN.WHITESPACES if used_whitespace else PATTERN.SPACES
        self.ws_pattern = self.ws_repl
        self.multi_ws_pattern = self.multi_ws_repl

        if self.relax:
            self.ws_repl = self.multi_ws_repl

        self._pattern = STRING.EMPTY
        self.failure_fmt = 'unsupported parsing integers (%s, %s)'
        self.process()

    @property
    def pattern(self):
        """
        str: The fully processed regular expression pattern.

        This property returns the compiled regex string generated from the
        input `data` after all wildcard expansions, bracket parsing, POSIX
        character class replacements, whitespace normalization, and optional
        anchoring. The value is computed during initialization by calling
        `process()` and reflects the final form of the pattern that can be
        used directly with Python's `re` module for matching.

        Notes
        -----
        - The pattern respects the configuration flags provided at
          initialization (e.g., `ignore_case`, `is_leading`, `is_trailing`,
          `relax`, `used_whitespace`, `from_start_to_end`).
        - For multiline input, line-by-line parsing is applied before
          concatenation.
        - The returned string is not a compiled regex object; use
          `re.compile(wildcard.pattern)` if you need a compiled pattern.
        """
        return self._pattern

    def process(self):
        """
        Build and assign the final regex pattern from the input data.

        This method is automatically invoked during initialization to
        transform the raw `data` string into a usable regex pattern. It
        first checks for special `--regex` markers and replaces them with
        appropriate spacing tokens. If no such markers are found, it
        delegates parsing to either `parse_multiline` or `parse_line`
        depending on whether the input contains newline characters.

        The resulting pattern is then optionally anchored to the start
        (`^`) and end (`$`) of the string, and case-insensitivity is
        applied if `ignore_case` is enabled. The computed regex string is
        stored in the private attribute `_pattern` and exposed via the
        `pattern` property.

        Notes
        -----
        - Handles detection and substitution of `--regex` flags with
          zero-or-more space patterns when present.
        - Chooses between single-line and multi-line parsing based on
          `is_multiline`.
        - Applies anchoring if `from_start_to_end` is True.
        - Applies case-insensitive matching if `ignore_case` is True.
        - The final regex string is not compiled; use
          `re.compile(self.pattern)` if a compiled regex object is needed.
        """
        p = r'(?i)(?P<start>^ *--regex *)|(?P<end> +--regex *$)|(?P<middle> *--regex +)'
        match = re.search(p, self.data)
        if match:
            start = match.groupdict().get(STRING.START, STRING.EMPTY)
            end = match.groupdict().get(STRING.END, STRING.EMPTY)
            middle = match.groupdict().get(STRING.MIDDLE, STRING.EMPTY)
            if start:
                replaced = PATTERN.ZOSPACES if len(start) > NUMBER.EIGHT else STRING.EMPTY
            elif end:
                replaced = PATTERN.ZOSPACES if len(end) > NUMBER.EIGHT else STRING.EMPTY
            else:
                replaced = PATTERN.ZOSPACES if len(middle) > NUMBER.EIGHT else STRING.EMPTY
            self._pattern = re.sub(p, replaced, self.data)
        else:
            method = self.parse_multiline if self.is_multiline else self.parse_line
            pattern = method(self.data)     # noqa

            if self.from_start_to_end and pattern[SLICE.GET_FIRST] != SYMBOL.CARET:
                pattern = '^%s' % pattern

            if self.from_start_to_end and pattern[SLICE.GET_LAST] != SYMBOL.DOLLAR_SIGN:
                pattern = '%s$' % pattern

            if self.ignore_case:
                pattern = '(?i)%s' % pattern
            self._pattern = pattern

    def escape_data(self, data):        # noqa
        """
        Escape and normalize special characters in a wildcard string.

        This method scans the input `data` for regex metacharacters and
        wildcard symbols, and converts them into safe or equivalent regex
        fragments. It ensures that literal characters are properly escaped
        while preserving wildcard semantics such as `?`, `*`, and `+`.

        Transformation rules
        --------------------
        - Leading/trailing spaces are collapsed into a single space pattern
          if more than one is present.
        - `?` is converted into a zero-or-one match pattern.
        - `*` is converted into a zero-or-more match pattern.
        - `+` is converted into a one-or-more match pattern.
        - Other regex metacharacters (e.g., `.`, `[`, `]`, `(`, `)`, `{`, `}`,
          `^`, `$`) are escaped to ensure literal matching.
        - Backslashes preceding metacharacters are preserved to respect
          explicit escaping in the input.

        Parameters
        ----------
        data : str
            The input string containing potential wildcard or regex symbols.

        Returns
        -------
        str
            A regex-safe string with wildcard symbols expanded and other
            special characters escaped.

        Notes
        -----
        - This method is typically used internally by parsing functions
          (e.g., `parse_curly_bracket`, `parse_shell_expansion`) to sanitize
          substrings before building the final regex pattern.
        - The returned string is not compiled; use `re.compile(...)` if a
          compiled regex object is required.
        """
        if re.match(PATTERN.SPACESATEOS, data):
            return data if len(data) <= NUMBER.ONE else PATTERN.SPACES

        start = NUMBER.ZERO
        item = None
        lst = []
        for item in re.finditer(r'(\\?)([.*+?\[{}\]^$)(])', data):
            pre_matched = data[start:item.start()]
            lst.append(pre_matched)
            matched_data = item.group()
            first, last = item.groups()
            if first == SYMBOL.BACK_SLASH:
                lst.append(matched_data)
            else:
                if last == SYMBOL.QUESTION_MARK:
                    lst.append(PATTERN.ZOANYTHING)
                elif last == SYMBOL.ASTERISK:
                    lst.append(PATTERN.SOMETHING)
                elif last == SYMBOL.PLUS:
                    lst.append(PATTERN.EVERYTHING)
                else:
                    escaped_txt = re.escape(matched_data)
                    lst.append(escaped_txt)
            start = item.end()

        if lst:
            post_matched = data[item.end():]
            lst.append(post_matched)
        else:
            lst.append(data)

        pattern = str.join(STRING.EMPTY, lst)
        return pattern

    def get_pattern_for_two_unsigned_int(self, v1, v2):     # noqa
        """
        Construct a regex pattern that matches all unsigned integers
        between two given values.

        This method generates a compact regular expression capable of
        matching any integer in the inclusive range defined by `v1` and
        `v2`. It accounts for differences in digit width (single-digit,
        double-digit, etc.) and produces optimized bracket or grouped
        patterns to cover the range without explicitly listing every
        number.

        Parameters
        ----------
        v1 : int
            The first unsigned integer in the range.
        v2 : int
            The second unsigned integer in the range.

        Returns
        -------
        str
            A regex string that matches all integers between `v1` and `v2`
            (inclusive). If the range cannot be expressed with the current
            logic, returns a failure message defined by `self.failure_fmt`.

        Examples
        --------
        - `get_pattern_for_two_unsigned_int(3, 7)` → `'[3-7]'`
        - `get_pattern_for_two_unsigned_int(5, 12)` → `'[5-9]|(1[0-2])'`
        - `get_pattern_for_two_unsigned_int(10, 25)` → `'(1[0-9])|(2[0-5])'`

        Notes
        -----
        - Only supports non-negative integers (unsigned).
        - Delegates to sub-patterns depending on whether the range spans
          one-digit or two-digit numbers.
        - For ranges ending at 100, special handling ensures inclusion of
          `'100'`.
        - Used internally by `get_pattern_for_two_numbers` to handle
          positive ranges.
        """
        small, large = min(v1, v2), max(v1, v2)
        first_small = int(Misc.get_first_char(small))
        last_small = int(Misc.get_last_char(small))
        first_large = int(Misc.get_first_char(large))
        last_large = int(Misc.get_last_char(large))
        small_width, large_width = len(str(small)), len(str(large))

        repl_pat = r'(\[(\d)-\2\])'
        repl_val = r'\2'

        if v1 == v2:
            return str(v1)
        elif small_width == NUMBER.ONE and large_width == NUMBER.ONE:
            pattern = '[%s-%s]' % (small, large)
            return pattern
        elif small_width == NUMBER.ONE and large_width == NUMBER.TWO:
            if first_large == NUMBER.ONE:
                args = (small, last_large)
                pattern = '[%s-9]|(1[0-%s])' % args
                pattern = re.sub(repl_pat, repl_val, pattern)
                return pattern
            elif first_large == NUMBER.TWO:
                if last_large != NUMBER.NINE:
                    args = (small, first_large, last_large)
                    pattern = '[%s-9]|(1[0-9])|(%s[0-%s])' % args
                    pattern = re.sub(repl_pat, repl_val, pattern)
                    return pattern
                else:
                    pattern = '[%s-9]|([1-2][0-9])' % small
                    pattern = re.sub(repl_pat, repl_val, pattern)
                    return pattern
            else:
                if last_large != NUMBER.NINE:
                    args = (small, first_large - NUMBER.ONE, first_large, last_large)
                    pattern = '[%s-9]|([1-%s][0-9])|(%s[0-%s])' % args
                    pattern = re.sub(repl_pat, repl_val, pattern)
                    return pattern
                else:
                    args = (small, first_large)
                    pattern = '[%s-9]|([1-%s][0-9])' % args
                    pattern = re.sub(repl_pat, repl_val, pattern)
                    return pattern

        elif small_width == NUMBER.TWO and large_width == NUMBER.TWO:
            if first_small == first_large:
                args = (first_small, last_small, last_large)
                pattern = '%s[%s-%s]' % args
                pattern = re.sub(repl_pat, repl_val, pattern)
                return pattern
            elif first_small + NUMBER.ONE == first_large:
                args = (first_small, last_small,
                        first_large, last_large)
                pattern = '(%s[%s-9])|(%s[0-%s])' % args
                pattern = re.sub(repl_pat, repl_val, pattern)
                return pattern
            else:
                if last_large != NUMBER.NINE:
                    args = (first_small,
                            last_small, first_small + NUMBER.ONE,
                            first_large - NUMBER.ONE, first_large, last_large)
                    pattern = '(%s[%s-9])|([%s-%s][0-9])|(%s[0-%s])' % args
                    pattern = re.sub(repl_pat, repl_val, pattern)
                    return pattern
                else:
                    args = (first_small, last_small, first_small + 1, first_large)
                    pattern = '(%s[%s-9])|([%s-%s][0-9])' % args
                    pattern = re.sub(repl_pat, repl_val, pattern)
                    return pattern

        elif small < NUMBER.HUNDRED and large == NUMBER.HUNDRED:
            pattern = self.get_pattern_for_two_unsigned_int(small, 99)
            pattern = ('(%s)|(100)' if pattern.isdigit() else '%s|(100)') % pattern
            pattern = re.sub(repl_pat, repl_val, pattern)
            return pattern

        return self.failure_fmt

    def get_pattern_for_two_numbers(self, v1, v2):
        """
        Construct a regex pattern that matches all integers between two values.

        This method generates a regular expression capable of matching any
        integer in the inclusive range defined by `v1` and `v2`. Unlike
        `get_pattern_for_two_unsigned_int`, this method supports both positive
        and negative ranges by delegating to the unsigned helper for non-negative
        values and adding appropriate handling for negative numbers.

        Parameters
        ----------
        v1 : int or str
            The first integer in the range (can be negative).
        v2 : int or str
            The second integer in the range (can be negative).

        Returns
        -------
        str
            A regex string that matches all integers between `v1` and `v2`
            (inclusive). If the range cannot be expressed with the current
            logic, returns a failure message defined by `self.failure_fmt`.

        Examples
        --------
        - `get_pattern_for_two_numbers(3, 7)` → `'[3-7]'`
        - `get_pattern_for_two_numbers(-5, -2)` → `'(-[2-5])'`
        - `get_pattern_for_two_numbers(-3, 3)` → `'((-3)|([0-3]))'`

        Notes
        -----
        - Delegates to `get_pattern_for_two_unsigned_int` when both values
          are non-negative.
        - Handles ranges where both values are negative by converting them
          to positive equivalents and prefixing with `-`.
        - For ranges spanning negative to positive, constructs two sub-patterns
          and joins them with alternation (`|`).
        - Used internally by `parse_shell_expansion` when expanding numeric
          ranges like `{1..10}` or `{-5..5}`.
        """
        lst = [int(v1), int(v2)]
        small, large = min(lst), max(lst)

        if small == large:
            pattern = str(small)
            return pattern
        if small >= NUMBER.ZERO and large >= NUMBER.ZERO:
            pattern = self.get_pattern_for_two_unsigned_int(small, large)
            if pattern.startswith(STRING.UNSUPPORTED_PARSING):
                failure = self.failure_fmt % (small, large)
                return failure
            pattern = '(%s)' % pattern if SYMBOL.LEFT_PARENTHESIS in pattern else pattern
            return pattern
        elif small <= NUMBER.ZERO and large <= NUMBER.ZERO:
            pattern = self.get_pattern_for_two_numbers(abs(small), abs(large))
            if pattern.startswith(STRING.UNSUPPORTED_PARSING):
                failure = self.failure_fmt % (small, large)
                return failure
            pattern = '(-%s)' % pattern if pattern else pattern
            return pattern
        else:
            pattern1 = self.get_pattern_for_two_numbers(NUMBER.ZERO, small)
            pattern2 = self.get_pattern_for_two_numbers(NUMBER.ZERO, large)
            if pattern1.startswith(STRING.UNSUPPORTED_PARSING):
                failure = self.failure_fmt % (small, large)
                return failure
            if pattern2.startswith(STRING.UNSUPPORTED_PARSING):
                failure = self.failure_fmt % (small, large)
                return failure

            pattern1 = '(%s)' % pattern1 if pattern1[SLICE.GET_FIRST] == '-' else pattern1
            pattern = '(%s|%s)' % (pattern1, pattern2)
            return pattern

    def parse_shell_expansion(self, data):
        """
        Expand shell-style brace expressions into regex patterns.

        This method interprets common shell expansion syntax inside curly
        braces (`{}`) and converts it into equivalent regular expression
        fragments. It supports three main forms of expansion:

        1. Alphabetic ranges: `{a..z}` → `'[a-z]'`
        2. Numeric ranges: `{-5..10}` → regex covering all integers in range
        3. Comma-separated lists: `{foo,bar,baz}` → `'(foo|bar|baz)'`

        Parameters
        ----------
        data : str
            The input string containing a shell-style brace expansion.

        Returns
        -------
        str
            A regex string representing the expanded form of the input.
            If no expansion is detected, returns the escaped input string.

        Examples
        --------
        - `parse_shell_expansion("{a..f}")` → `'[a-f]'`
        - `parse_shell_expansion("{1..3}")` → `'[1-3]'`
        - `parse_shell_expansion("{foo,bar}")` → `'(foo|bar)'`
        - `parse_shell_expansion("{,baz}")` → `'(baz)?'`  (optional empty item)

        Notes
        -----
        - Alphabetic ranges larger than 26 characters include additional
          escaped symbols to cover extended ASCII ranges.
        - Numeric ranges are delegated to `get_pattern_for_two_numbers`
          for proper handling of signed and unsigned integers.
        - Empty items in comma-separated lists are treated as optional
          matches (`?`).
        - If the input does not match any expansion pattern, the string
          is passed through `escape_data` for safe regex conversion.
        """
        match1 = re.match(r'(?i)\{(?P<first>[a-z])[.]{2}(?P<last>[a-z])}', data)
        match2 = re.match(r'(?i)\{(?P<first>-?\d+)[.]{2}(?P<last>-?\d+)}', data)
        match3 = re.match(r'(?i)\{[^,]*(,[^,]*)+}', data)

        if match1:
            first = match1.group(STRING.FIRST)
            last = match1.group(STRING.LAST)
            v1 = first if first < last else last
            v2 = last if first < last else first
            total = ord(v2) - ord(v1)
            if total > 26:
                other = re.escape('[\\]^_`')
                pattern = '[%s-Za-%s%s]' % (v1, v2, other)
            else:
                pattern = '[%s-%s]' % (v1, v2)
            return pattern
        elif match2:
            first = int(match2.group(STRING.FIRST))
            last = int(match2.group(STRING.LAST))
            pattern = self.get_pattern_for_two_numbers(first, last)
            return pattern
        elif match3:
            is_empty_item = False
            lst = []
            for item in str.split(data[SLICE.FIRST_TO_LAST], SYMBOL.COMMA):
                if item:
                    escaped_txt = self.escape_data(item)
                    lst.append(escaped_txt)
                else:
                    is_empty_item = True
            if lst:
                pattern = '(%s)' % str.join(SYMBOL.VERTICAL_LINE, lst)
                pattern = '%s?' % pattern if is_empty_item else pattern
                return pattern
            else:
                return STRING.EMPTY
        else:
            pattern = self.escape_data(data)
            return pattern

    def has_curly_bracket(self, data):      # noqa
        """
        Check whether a string contains a curly-brace expression.

        This method scans the input `data` for the presence of a substring
        enclosed in curly braces (`{...}`), which may represent a shell-style
        expansion or regex quantifier. It accounts for optional escaping with
        backslashes to avoid false positives.

        Parameters
        ----------
        data : str
            The input string to inspect.

        Returns
        -------
        bool
            True if the string contains at least one curly-brace expression,
            False otherwise.

        Examples
        --------
        - `has_curly_bracket("foo{bar,baz}")` → True
        - `has_curly_bracket("abc\\{123\\}")` → True (escaped braces still detected)
        - `has_curly_bracket("plain text")` → False

        Notes
        -----
        - This method does not expand or parse the contents of the braces;
          use `parse_curly_bracket` for full expansion.
        - Escaped braces (`\\{...\\}`) are still considered matches.
        """
        match = re.search(r'(\\?)[{][^}]+\1[}]', data)
        result = bool(match)
        return result

    def parse_curly_bracket(self, data):
        """
        Parse and expand curly-brace expressions into regex patterns.

        This method scans the input string for substrings enclosed in curly
        braces (`{...}`) and converts them into appropriate regex fragments.
        It supports multiple forms of brace usage, including numeric ranges,
        shell-style expansions, and comma-separated lists. Escaped braces
        are preserved as literals.

        Parsing rules
        -------------
        - Empty brace lists (e.g., `{,}`) are treated as empty matches.
        - Numeric quantifiers (e.g., `{3}`, `{2,5}`) are preserved as-is
          for regex repetition semantics.
        - Shell-style expansions (e.g., `{a..z}`, `{1..10}`, `{foo,bar}`)
          are delegated to `parse_shell_expansion` for conversion.
        - Other brace contents are escaped to ensure safe regex usage.

        Parameters
        ----------
        data : str
            The input string containing one or more curly-brace expressions.

        Returns
        -------
        str
            A regex-safe string with curly-brace expressions expanded or
            escaped as appropriate.

        Examples
        --------
        - `parse_curly_bracket("foo{bar,baz}qux")`
          → `"foo(bar|baz)qux"`
        - `parse_curly_bracket("num{1..3}")`
          → `"num[1-3]"`
        - `parse_curly_bracket("word{2,4}")`
          → `"word{2,4}"` (kept as quantifier)

        Notes
        -----
        - This method is typically used internally by `parse_data` and
          `parse_line` to handle brace expansions before building the
          final regex pattern.
        - Escaped braces (`\\{...\\}`) are preserved as literal text.
        - Delegates to `escape_data` for safe handling of non-expansion
          substrings.
        """
        if re.search(r'\{.+?}', data):
            lst = []
            start = NUMBER.ZERO
            item = None
            for item in re.finditer(r'(\\?)[{][^}]+\1[}]', data):
                pre_matched = data[start:item.start()]
                # escaped_txt = re.escape(pre_matched)
                escaped_txt = self.escape_data(pre_matched)
                lst.append(escaped_txt)
                matched_txt = item.group()
                match_a = re.match(r'(\\?)[{] *(, *)+\1[}]', matched_txt)
                match1 = re.match(r'(\\?)[{] *\d+ *\1[}]', matched_txt)
                match2 = re.match(r'(\\?)[{] *\d* *, *\d* *\1[}]', matched_txt)
                match3 = re.match(r'[{][^}]+[}]', matched_txt)

                if match_a:
                    lst.append(STRING.EMPTY)
                elif match1 or match2:
                    new_matched_txt = matched_txt.replace('\\', '')
                    lst.append(new_matched_txt)
                elif match3:
                    expanded_txt = self.parse_shell_expansion(matched_txt)
                    lst.append(expanded_txt)
                else:
                    escaped_txt = self.escape_data(matched_txt)
                    lst.append(escaped_txt)
                start = item.end()
            if lst:
                post_matched = data[item.end():]
                escaped_txt = self.escape_data(post_matched)
                lst.append(escaped_txt)
            else:
                escaped_txt = self.escape_data(data)
                lst.append(escaped_txt)
            data = str.join(STRING.EMPTY, lst)
        else:
            data = self.escape_data(data)
        return data

    def parse_round_bracket(self, data):
        """
        Parse and expand round-bracket expressions into regex patterns.

        This method scans the input string for substrings enclosed in
        parentheses (`(...)`) and recursively converts them into valid
        regex fragments. It ensures that nested bracketed expressions are
        handled correctly, while also applying square-bracket parsing and
        whitespace normalization to surrounding text.

        Parsing rules
        -------------
        - Empty input returns an empty string.
        - Leading/trailing spaces are collapsed into a single space pattern.
        - Each parenthesized group is recursively parsed to handle nested
          round brackets.
        - Escaped parentheses are preserved as literal characters.
        - Text outside parentheses is passed through `parse_square_bracket`
          and `replace_whitespace` for safe regex conversion.

        Parameters
        ----------
        data : str
            The input string containing one or more round-bracket expressions.

        Returns
        -------
        str
            A regex-safe string with round-bracket expressions expanded or
            escaped as appropriate.

        Examples
        --------
        - `parse_round_bracket("(foo|bar)")`
          → `"(foo|bar)"`
        - `parse_round_bracket("a(b(c|d))e")`
          → `"a(b(c|d))e"` (nested parsing applied)
        - `parse_round_bracket("x (y z)")`
          → `"x (y z)"` (whitespace normalized)

        Notes
        -----
        - This method is typically used internally by `parse_line` to
          process parenthesized groups before building the final regex
          pattern.
        - Delegates to `parse_square_bracket` for handling bracketed
          character classes inside or outside parentheses.
        - Whitespace inside and around groups is normalized using
          `replace_whitespace`.
        """
        line = data
        if not line:
            return STRING.EMPTY
        elif re.match(PATTERN.SPACESATEOS, line):
            return PATTERN.SPACES

        lst = []
        start = NUMBER.ZERO
        item = None

        for item in re.finditer(r'(\\?)\((.+)(\1\))', line):
            pre_matched = line[start:item.start()]
            parsed_pre_matched = self.parse_square_bracket(pre_matched)
            parsed_pre_matched = self.replace_whitespace(parsed_pre_matched)
            lst.append(parsed_pre_matched)
            left, middle, right = item.groups()
            sub_pat = self.parse_round_bracket(middle)
            if sub_pat == SYMBOL.BACK_SLASH:
                parsed_matched_txt = '\\(%s\\)' % sub_pat
            else:
                parsed_matched_txt = '(%s)' % sub_pat
            lst.append(parsed_matched_txt)
            start = item.end()

        if lst:
            post_matched = line[item.end():]
            parsed_post_matched = self.parse_square_bracket(post_matched)
            parsed_post_matched = self.replace_whitespace(parsed_post_matched)
            lst.append(parsed_post_matched)
        else:
            parsed_txt = self.parse_square_bracket(line)
            parsed_txt = self.replace_whitespace(parsed_txt)
            lst.append(parsed_txt)

        pattern = str.join(STRING.EMPTY, lst)

        return pattern

    def parse_square_bracket(self, data):
        """
        Parse and expand square-bracket expressions into regex patterns.

        This method scans the input string for substrings enclosed in square
        brackets (`[...]`) and converts them into valid regex fragments. It
        ensures that character classes and negated sets are handled correctly,
        while also parsing surrounding text and normalizing whitespace.

        Parsing rules
        -------------
        - Empty input returns an empty string.
        - Leading/trailing spaces are collapsed into a single space pattern.
        - Each square-bracketed group is preserved as a regex character class.
        - Negated sets beginning with `[!...]` are converted into proper regex
          syntax (`[^...]`).
        - Text outside brackets is passed through `parse_data` and
          `replace_whitespace` for safe regex conversion.

        Parameters
        ----------
        data : str
            The input string containing one or more square-bracket expressions.

        Returns
        -------
        str
            A regex-safe string with square-bracket expressions preserved and
            surrounding text properly parsed.

        Examples
        --------
        - `parse_square_bracket("[abc]")`
          → `"[abc]"`
        - `parse_square_bracket("[!0-9]")`
          → `"[^0-9]"`
        - `parse_square_bracket("foo[xyz]bar")`
          → `"foo[xyz]bar"`

        Notes
        -----
        - This method is typically used internally by `parse_round_bracket`
          and `parse_line` to process character classes before building the
          final regex pattern.
        - Whitespace inside and around bracketed groups is normalized using
          `replace_whitespace`.
        - Delegates to `parse_data` for handling non-bracketed substrings.
        """
        line = data
        if not line:
            return STRING.EMPTY
        elif re.match(PATTERN.SPACESATEOS, line):
            return PATTERN.SPACES

        lst = []
        start = NUMBER.ZERO
        item = None

        for item in re.finditer(r'\[.+?]', line):
            pre_matched = line[start:item.start()]
            parsed_pre_matched = self.parse_data(pre_matched)
            parsed_pre_matched = self.replace_whitespace(parsed_pre_matched)
            lst.append(parsed_pre_matched)
            matched_txt = item.group()
            if matched_txt.startswith('[!'):
                matched_txt = '[^%s' % matched_txt[SLICE.SKIP_FROM_SECOND]
            lst.append(matched_txt)
            start = item.end()

        if lst:
            post_matched = line[item.end():]
            parsed_post_matched = self.parse_data(post_matched)
            parsed_post_matched = self.replace_whitespace(parsed_post_matched)
            lst.append(parsed_post_matched)
        else:
            parsed_txt = self.parse_data(line)
            parsed_txt = self.replace_whitespace(parsed_txt)
            lst.append(parsed_txt)

        pattern = str.join(STRING.EMPTY, lst)

        return pattern

    def parse_data(self, data):
        """
        Parse and expand generic substrings into regex-safe fragments.

        This method processes arbitrary text segments, looking for nested
        expressions enclosed in parentheses or curly braces, and converts
        them into valid regex components. It ensures that brace expansions
        and quantifiers are handled correctly while preserving literal text
        through escaping.

        Parsing rules
        -------------
        - Empty input returns an empty string.
        - Leading/trailing spaces are collapsed into a single space pattern.
        - Parenthesized substrings are detected and passed through
          `parse_curly_bracket` for expansion.
        - Curly-brace expressions inside or outside parentheses are expanded
          using `parse_curly_bracket` (which may delegate to
          `parse_shell_expansion`).
        - Text outside of bracketed expressions is escaped to ensure regex safety.

        Parameters
        ----------
        data : str
            The input string containing arbitrary text and possible bracketed
            expressions.

        Returns
        -------
        str
            A regex-safe string with bracketed expressions expanded and
            surrounding text properly escaped.

        Examples
        --------
        - `parse_data("foo{bar,baz}")`
          → `"foo(bar|baz)"`
        - `parse_data("(abc{1..3})")`
          → `"(abc[1-3])"`
        - `parse_data("plain text")`
          → `"plain text"` (escaped if necessary)

        Notes
        -----
        - This method is a general-purpose parser used internally by
          `parse_square_bracket` and `parse_line` to handle non-bracketed
          substrings.
        - Delegates to `parse_curly_bracket` for brace handling and
          `escape_data` for safe literal conversion.
        - Supports nested parentheses and braces by iteratively parsing
          matched groups.
        """
        if re.match(PATTERN.SPACESATEOS, data):
            return data if len(data) <= NUMBER.ONE else PATTERN.SPACES

        start = NUMBER.ZERO
        item = None
        lst = []
        for item in re.finditer(r'(\\?)[(].*\1[)]', data):
            pre_matched = data[start:item.start()]
            parsed_pre_matched = self.parse_curly_bracket(pre_matched)
            lst.append(parsed_pre_matched)

            parsed_matched = self.parse_curly_bracket(item.group())
            lst.append(parsed_matched)
            start = item.end()

        if lst:
            post_matched = data[item.end():]
            parsed_post_match = self.parse_curly_bracket(post_matched)
            lst.append(parsed_post_match)
        else:
            parsed_data = self.parse_curly_bracket(data)
            lst.append(parsed_data)

        pattern = str.join(STRING.EMPTY, lst)
        return pattern

    def mark_posix_char_class(self, line):      # noqa
        """
        Mark POSIX character classes in a string with placeholders.

        This method scans the input `line` for POSIX-style character
        classes (e.g., `[:alpha:]`, `[:digit:]`, `[:space:]`) and replaces
        them with internal placeholder tokens. These placeholders are later
        substituted back into proper regex ranges by
        `replace_posix_char_class`.

        Parameters
        ----------
        line : str
            The input string potentially containing POSIX character classes.

        Returns
        -------
        str
            A string where each recognized POSIX character class has been
            replaced with a unique placeholder token.

        Examples
        --------
        - `mark_posix_char_class("foo[:digit:]bar")`
          → `"foo__placeholder_digit_pat__bar"`
        - `mark_posix_char_class("[:alpha:]-[:space:]")`
          → `"__placeholder_alpha_pat__-__placeholder_space_pat__"`

        Notes
        -----
        - Supported POSIX classes include: `alpha`, `alnum`, `blank`,
          `cntrl`, `digit`, `graph`, `lower`, `print`, `space`, `upper`,
          and `xdigit`.
        - Placeholders are named using the format
          `__placeholder_<class>_pat__`.
        - This method does not perform substitution into actual regex
          ranges; use `replace_posix_char_class` for that step.
        - Typically used internally by `parse_line` before final regex
          assembly.
        """
        lst = ['alpha', 'alnum', 'blank', 'cntrl', 'digit', 'graph',
               'lower', 'print', 'space', 'upper', 'xdigit']

        for item in lst:
            pat = r'(?i)\[:%s:\]' % item
            placeholder = '__placeholder_%s_pat__' % item
            line = re.sub(pat, placeholder, line)

        return line

    def replace_posix_char_class(self, line):   # noqa
        """
        Replace POSIX character class placeholders with actual regex ranges.

        This method scans the input `line` for placeholder tokens previously
        inserted by `mark_posix_char_class` (e.g.,
        `__placeholder_digit_pat__`, `__placeholder_alpha_pat__`) and
        substitutes them with their corresponding regex character ranges.

        Supported POSIX classes
        -----------------------
        - alpha   → `a-zA-Z`
        - alnum   → `a-zA-Z0-9`
        - blank   → space or tab (` \t`)
        - cntrl   → ASCII control characters (`\\x00-\\x1f\\x7f`)
        - digit   → `0-9`
        - graph   → visible ASCII characters (`\\x21-\\x7e`)
        - lower   → `a-z`
        - print   → printable ASCII characters (`\\x20-\\x7e`)
        - space   → space or tab (` \t`)
        - upper   → `A-Z`
        - xdigit  → hexadecimal digits (`a-fA-F0-9`)

        Parameters
        ----------
        line : str
            The input string containing POSIX class placeholders.

        Returns
        -------
        str
            A regex-safe string with placeholders replaced by actual
            character ranges.

        Examples
        --------
        - `replace_posix_char_class("foo__placeholder_digit_pat__bar")`
          → `"foo0-9bar"`
        - `replace_posix_char_class("__placeholder_alpha_pat__")`
          → `"a-zA-Z"`

        Notes
        -----
        - This method is the counterpart to `mark_posix_char_class`.
        - Placeholders are replaced with raw regex ranges, not enclosed
          in brackets; ensure they are used inside `[...]` when building
          character classes.
        - Typically used internally by `parse_line` after marking
          placeholders to finalize the regex pattern.
        """
        tbl = dict(
            alpha=r'a-zA-Z',
            alnum=r'a-zA-Z0-9',
            blank=r' \t',
            cntrl=r'\x00-\x1f\x7f',
            digit=r'0-9',
            graph=r'\x21-\x7e',
            lower=r'a-z',
            print=r'\x20-\x7e',
            space=r' \t',
            upper=r'A-Z',
            xdigit=r'a-fA-F0-9'
        )
        for key, replaced in tbl.items():
            replacing = '__placeholder_%s_pat__' % key
            line = line.replace(replacing, replaced)
        return line

    def mark_word_bound(self, line):        # noqa
        """
        Mark word-boundary expressions in a string with placeholders.

        This method scans the input `line` for word-boundary markers written
        in the form `\\<...\\>` and replaces them with internal placeholder
        tokens. These placeholders are later substituted into proper regex
        word-boundary anchors (`\\b`) by `replace_word_bound`.

        Parameters
        ----------
        line : str
            The input string potentially containing word-boundary markers.

        Returns
        -------
        str
            A string where each recognized word-boundary marker has been
            replaced with a placeholder token.

        Examples
        --------
        - `mark_word_bound("foo\\<bar\\>baz")`
          → `"foo__placeholder_wb_pat__bar__placeholder_wb_pat__baz"`

        Notes
        -----
        - Placeholders are named using the format `__placeholder_wb_pat__`.
        - This method does not insert actual regex anchors; use
          `replace_word_bound` to restore them as `\\b`.
        - Typically used internally by `parse_line` before final regex
          assembly to safely handle word-boundary markers.
        """
        pat = r'(\\<)(.*?)(\\>)'
        line = re.sub(pat, r'__placeholder_wb_pat__\2__placeholder_wb_pat__', line)
        return line

    def replace_word_bound(self, line):     # noqa
        """
        Replace word-boundary placeholders with actual regex anchors.

        This method scans the input `line` for placeholder tokens previously
        inserted by `mark_word_bound` (e.g., `__placeholder_wb_pat__`) and
        substitutes them with the regex word-boundary anchor (`\\b`).

        Parameters
        ----------
        line : str
            The input string containing word-boundary placeholders.

        Returns
        -------
        str
            A regex-safe string with placeholders replaced by `\\b` anchors.

        Examples
        --------
        - `replace_word_bound("foo__placeholder_wb_pat__bar__placeholder_wb_pat__baz")`
          → `"foo\\bbar\\bbaz"`

        Notes
        -----
        - This method is the counterpart to `mark_word_bound`.
        - Placeholders are replaced with `\\b`, which matches a position
          between a word character (`\\w`) and a non-word character (`\\W`).
        - Typically used internally by `parse_line` after marking placeholders
          to finalize the regex pattern.
        """
        line = line.replace('__placeholder_wb_pat__', r'\b')
        return line

    def replace_whitespace(self, line):
        """
        Normalize and replace whitespace sequences with regex-safe patterns.

        This method scans the input `line` for runs of spaces and replaces
        them with appropriate regex fragments that represent flexible
        whitespace matching. It distinguishes between single spaces and
        multiple consecutive spaces, and applies quantifiers when present.

        Parsing rules
        -------------
        - Single spaces are replaced with `self.ws_pattern` (default: `\\s` or literal space).
        - Multiple spaces are replaced with `self.multi_ws_pattern` (default: `\\s+` or multiple spaces).
        - If a quantifier (`+`, `*`, `?`) immediately follows a space sequence,
          the sequence is preserved as-is to respect explicit repetition.
        - Text outside of whitespace runs is left unchanged.

        Parameters
        ----------
        line : str
            The input string containing literal spaces or whitespace sequences.

        Returns
        -------
        str
            A regex-safe string with whitespace sequences normalized and
            replaced by flexible regex patterns.

        Examples
        --------
        - `replace_whitespace("foo bar")`
          → `"foo\\sbar"`
        - `replace_whitespace("foo   bar")`
          → `"foo\\s+bar"`
        - `replace_whitespace("foo + bar")`
          → `"foo + bar"` (quantifier preserved)

        Notes
        -----
        - The behavior depends on initialization flags:
          - If `used_whitespace=True`, explicit whitespace characters are preserved.
          - If `relax=True`, multiple spaces are treated as equivalent to single spaces.
        - Typically used internally by `parse_square_bracket`, `parse_round_bracket`,
          and `parse_line` to ensure consistent whitespace handling in regex patterns.
        """
        start = NUMBER.ZERO
        item = None
        lst = []
        for item in re.finditer(r'( +)([+*?]?)', line):
            pre_matched = line[start:item.start()]
            lst.append(pre_matched)
            matched_txt = item.group()
            first, last = item.groups()
            is_single_ws = len(matched_txt) == NUMBER.ONE
            if last:
                lst.append(matched_txt)
            else:
                lst.append(self.ws_pattern if is_single_ws else self.multi_ws_pattern)
            start = item.end()
        if lst:
            post_matched = line[item.end():]
            lst.append(post_matched)
            pattern = str.join(STRING.EMPTY, lst)
            return pattern
        else:
            return line

    def parse_line(self, data):
        """
        Parse a single line of input into a regex-safe pattern.

        This method processes one line of text containing wildcard or
        shell-style expressions and converts it into a valid regex string.
        It handles anchors, whitespace normalization, POSIX character
        classes, word-boundary markers, and bracketed expressions to build
        a complete regex fragment for the line.

        Parsing rules
        -------------
        - Empty input returns an empty string.
        - Leading/trailing spaces are collapsed into regex whitespace
          patterns (`self.ws_pattern` or `self.multi_ws_pattern`).
        - A leading `^` or trailing `$` is preserved as start/end anchors.
        - POSIX character classes (e.g., `[:digit:]`) are marked with
          placeholders and later replaced with regex ranges.
        - Word-boundary markers (`\\<...\\>`) are marked with placeholders
          and later replaced with `\\b`.
        - Round-bracket groups are parsed recursively via
          `parse_round_bracket`.
        - Leading/trailing whitespace or explicit `is_leading`/`is_trailing`
          flags add flexible whitespace patterns before or after the line.

        Parameters
        ----------
        data : str
            A single line of input containing wildcard expressions.

        Returns
        -------
        str
            A regex-safe string representing the parsed line.

        Examples
        --------
        - `parse_line("^foo bar$")`
          → `"^\\s*foo\\sbar\\s*$"`
        - `parse_line("abc[:digit:]")`
          → `"abc0-9"`
        - `parse_line("foo\\<bar\\>baz")`
          → `"foo\\bbar\\bbaz"`

        Notes
        -----
        - This method is the core parser for single-line input and is
          invoked by `process` when `is_multiline` is False.
        - It integrates multiple helpers:
          - `mark_posix_char_class` / `replace_posix_char_class`
          - `mark_word_bound` / `replace_word_bound`
          - `parse_round_bracket`
          - `replace_whitespace`
        - Anchoring (`^...$`) is applied only if not already present and
          if `from_start_to_end` is True.
        """
        line = data
        if not line:
            return STRING.EMPTY
        elif re.match(PATTERN.SPACESATEOS, line):
            return PATTERN.SPACES

        is_start_of_line = False
        if line[SLICE.GET_FIRST] == SYMBOL.CARET:
            line = line[SLICE.SKIP_FROM_FIRST]
            is_start_of_line = True

        is_end_of_line = False
        if line[SLICE.GET_LAST] == SYMBOL.DOLLAR_SIGN:
            line = line[SLICE.TAKE_TO_LAST]
            is_end_of_line = True

        is_started_space = bool(re.match(PATTERN.SPACE, line))
        is_ended_space = bool(re.search(PATTERN.SPACEATEOS, line))
        line = line.strip()

        line = self.mark_posix_char_class(line)
        line = self.mark_word_bound(line)

        pattern = self.parse_round_bracket(line)

        if is_started_space or self.is_leading:
            pattern = '%s*%s' % (self.ws_pattern, pattern)
        if is_ended_space or self.is_trailing:
            pattern = '%s%s*' % (pattern, self.ws_pattern)

        pattern = self.replace_posix_char_class(pattern)
        pattern = self.replace_word_bound(pattern)

        if is_start_of_line and pattern and pattern[SLICE.GET_FIRST] != SYMBOL.CARET:
            pattern = '^%s' % pattern

        if is_end_of_line and pattern and pattern[SLICE.GET_LAST] != SYMBOL.DOLLAR_SIGN:
            pattern = '%s$' % pattern

        return pattern

    def parse_multiline(self, data):
        """
        Parse multi-line input into a combined regex-safe pattern.

        This method processes text containing multiple lines (separated by
        newline characters) and converts each line into a regex fragment
        using `parse_line`. It then joins the fragments together with
        alternation (`|`) so that the resulting regex matches any of the
        provided lines.

        Parsing rules
        -------------
        - Empty input returns an empty string.
        - Each line is individually parsed with `parse_line`, applying
          whitespace normalization, anchors, POSIX class handling, and
          bracket expansion.
        - Lines are combined into a single regex string using alternation.
        - Leading/trailing whitespace in each line is normalized before
          joining.

        Parameters
        ----------
        data : str
            A multi-line string containing wildcard or shell-style
            expressions. Lines are separated by `\\n`.

        Returns
        -------
        str
            A regex-safe string that matches any of the parsed lines.

        Examples
        --------
        - `parse_multiline("foo\\nbar")`
          → `"(foo|bar)"`
        - `parse_multiline("^abc$\\ndef")`
          → `"(^abc$|def)"`

        Notes
        -----
        - This method is the companion to `parse_line` and is invoked by
          `process` when `is_multiline=True`.
        - Useful for building regex patterns from configuration files,
          lists of keywords, or multi-line user input.
        - Delegates all per-line parsing logic to `parse_line` to ensure
          consistency between single-line and multi-line handling.
        """
        lst = []
        for line in re.split(PATTERN.MULTICRNL, data):
            pat = self.parse_line(line)
            lst.append(pat)

        pattern = str.join(PATTERN.MULTICRNL, lst)
        return pattern
