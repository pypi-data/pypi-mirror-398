"""
genericlib.collection
=====================

Enhanced dictionary and object-like data structures with dot-notation access.

This module provides specialized dictionary subclasses that make working with
structured or nested data more intuitive. By supporting both traditional
key-based indexing and attribute-style dot notation, these classes reduce
boilerplate and improve readability when handling JSON-like data, configuration
objects, or API responses.

Key Components
--------------
- DictObject:
    A dictionary subclass that synchronizes keys with attributes. Values can be
    accessed or updated interchangeably via `obj['key']` or `obj.key`. Reserved
    Python keywords are automatically suffixed with an underscore to avoid
    conflicts.

    Behavior:
    - Setting an attribute also updates the dictionary.
    - Setting a dictionary key also updates the corresponding attribute.
    - Reserved keywords (e.g., `class`, `def`, `return`) are renamed with a
      trailing underscore when used as attributes.

- DotObject:
    A recursive extension of DictObject that wraps nested dictionaries as
    DotObject instances. This enables deep attribute-style access to complex,
    hierarchical data structures without manual conversion.

    Behavior:
    - Accessing a nested dictionary returns a DotObject.
    - Both attribute-style and key-based access are supported at all levels.

Dependencies
------------
- `re`: Used for keyword handling and pattern matching.
- `deepcopy`: Ensures safe copying of nested structures.
- `genericlib.constant.STRING` and `genericlib.constnum.NUMBER`: Provide shared
  constants used for validation and type handling.

Use Cases
---------
- Simplifying access to JSON-like data structures.
- Building configuration objects that can be navigated with dot notation.
- Improving readability when working with nested dictionaries in applications
  such as data parsing, configuration management, or API responses.

"""


import re
from copy import deepcopy

from genericlib.constnum import NUMBER
from genericlib.constant import STRING


class DictObject(dict):
    """
    A dictionary subclass that supports both key-based and attribute-style access.

    DictObject automatically synchronizes dictionary keys with object attributes,
    allowing values to be accessed and updated via either dot notation or
    standard dictionary indexing. Reserved Python keywords are suffixed with
    an underscore to avoid conflicts.

    Behavior
    --------
    - Setting an attribute also updates the dictionary.
    - Setting a dictionary key also updates the corresponding attribute.
    - Reserved keywords (e.g., `class`, `def`, `return`) are renamed with a
      trailing underscore when used as attributes.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize a DictObject instance.

        This constructor behaves like the standard `dict` initializer but
        additionally synchronizes keys with attributes. Any key-value pairs
        provided at initialization are immediately available both through
        dictionary-style access (`obj["key"]`) and attribute-style access
        (`obj.key`), subject to reserved keyword handling.

        Parameters
        ----------
        *args : arguments
            Positional arguments passed to the base `dict` constructor.
        **kwargs : keyword arguments
            Keyword arguments passed to the base `dict` constructor. These
            become both dictionary keys and object attributes.

        Notes
        -----
        - Reserved Python keywords (e.g., `class`, `def`, `return`) are
          suffixed with an underscore when exposed as attributes.
        - Initialization calls `update` internally to ensure attributes
          are created for all keys.
        """
        super().__init__(*args, **kwargs)
        self.update(*args, **kwargs)

    def __setattr__(self, attr, value):
        """
        Assign an attribute and synchronize it with the dictionary.

        This method overrides the default attribute assignment to ensure
        that setting an attribute also updates the underlying dictionary.
        The attribute name becomes a dictionary key, and the assigned value
        is stored in both places. Reserved Python keywords are suffixed with
        an underscore when exposed as attributes.

        Parameters
        ----------
        attr : str
            The attribute name to assign.
        value : Any
            The value to associate with the attribute and dictionary key.

        Notes
        -----
        - Attribute assignment automatically calls `update` to keep the
          dictionary in sync.
        - Reserved keywords (e.g., `class`, `def`, `return`) are renamed
          with a trailing underscore when used as attributes.
        - A special flag `is_updated_attr` is included in the update to
          distinguish attribute-based updates from dictionary-based ones.
        """
        super().__setattr__(attr, value)
        self.update(**{attr: value, 'is_updated_attr': False})

    def __setitem__(self, key, value):
        """
        Assign a dictionary key and synchronize it with attributes.

        This method overrides the standard dictionary item assignment to
        ensure that setting a key also updates the corresponding attribute
        on the object. Keys that are valid Python identifiers can be accessed
        via dot notation (`obj.key`) as well as dictionary-style indexing
        (`obj["key"]`). Reserved Python keywords are suffixed with an
        underscore when exposed as attributes.

        Parameters
        ----------
        key : str
            The dictionary key to assign.
        value : Any
            The value to associate with the key and attribute.

        Notes
        -----
        - Key assignment automatically calls `update` to keep attributes
          synchronized with dictionary entries.
        - Reserved keywords (e.g., `class`, `def`, `return`) are renamed
          with a trailing underscore when used as attributes.
        - Unlike `__setattr__`, this method does not add the `is_updated_attr`
          flag, since the update originates from dictionary-style assignment.
        """
        super().__setitem__(key, value)
        self.update({key: value})       # noqa

    def update(self, *args, is_updated_attr=True, **kwargs):
        """
        Update the dictionary and synchronize attributes.

        This method extends the standard `dict.update` behavior by ensuring
        that newly added or modified keys are also available as object
        attributes. Keys that are valid Python identifiers can be accessed
        via dot notation (`obj.key`). Reserved Python keywords are suffixed
        with an underscore when exposed as attributes.

        Parameters
        ----------
        *args : arguments
            Positional arguments passed to the base `dict.update`.
        is_updated_attr : bool, optional
            Flag indicating whether attributes should be updated alongside
            dictionary keys. Defaults to True.
        **kwargs : keyword arguments
            Keyword arguments passed to the base `dict.update`.

        Notes
        -----
        - Reserved keywords (e.g., `class`, `def`, `return`) are renamed
          with a trailing underscore when used as attributes.
        - If `is_updated_attr` is False, only the dictionary is updated,
          without creating or modifying attributes.
        - Keys must match the regex pattern `[a-z]\\w*` (case-insensitive)
          to be exposed as attributes.
        """
        chk_lst = [
            'False', 'None', 'True',
            'and', 'as', 'assert', 'await', 'break', 'class', 'continue',
            'def', 'del', 'else', 'except', 'finally', 'for', 'from',
            'global', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not',
            'pass', 'raise', 'return', 'try', 'while', 'with'
        ]

        obj = dict(*args, **kwargs)
        super().update(obj)
        if is_updated_attr:
            for attr, value in obj.items():
                if isinstance(attr, str) and re.match(r'(?i)[a-z]\w*$', attr):
                    attr = '%s_' % attr if attr in chk_lst else attr
                    setattr(self, attr, value)


class DotObject(DictObject):
    """
    A recursive extension of DictObject that supports nested dot access.

    DotObject wraps nested dictionaries as DotObject instances, enabling
    deep attribute-style access without manual conversion.

    Behavior
    --------
    - Accessing a nested dictionary returns a DotObject.
    - Both attribute-style and key-based access are supported at all levels.
    """
    def __getattribute__(self, attr):
        """
        Retrieve an attribute, wrapping nested dictionaries as DotObject.

        This method overrides the default attribute access to ensure that
        when an attribute corresponds to a dictionary value, it is returned
        as a `DotObject` rather than a plain `dict`. This enables recursive
        dot-style access for nested structures.

        Parameters
        ----------
        attr : str
            The attribute name to retrieve.

        Returns
        -------
        Any
            The attribute value. If the value is a dictionary, it is wrapped
            in a `DotObject`; otherwise, the raw value is returned.
        Notes
        -----
        - Non-dictionary values are returned unchanged.
        - This behavior allows seamless navigation of deeply nested
          dictionaries using attribute-style access.
        """
        value = super().__getattribute__(attr)
        return DotObject(value) if isinstance(value, dict) else value   # noqa

    def __getitem__(self, key):
        """
        Retrieve a dictionary item, wrapping nested dictionaries as DotObject.

        This method overrides standard dictionary item access to ensure that
        when a key corresponds to a dictionary value, it is returned as a
        `DotObject` rather than a plain `dict`. This enables recursive
        dot-style access for nested structures, even when using bracket
        notation.

        Parameters
        ----------
        key : str
            The dictionary key to retrieve.

        Returns
        -------
        Any
            The value associated with the given key. If the value is a
            dictionary, it is wrapped in a `DotObject`; otherwise, the
            raw value is returned.

        Notes
        -----
        - Non-dictionary values are returned unchanged.
        - This behavior complements `__getattribute__`, allowing both
          attribute-style (`obj.user.name`) and key-style (`obj["user"]["name"]`)
          access to work seamlessly with nested dictionaries.
        """
        value = super().__getitem__(key)
        return DotObject(value) if isinstance(value, dict) else value   # noqa


def substitute_variable(data, root_var_name='self'):
    """
    Substitute variable placeholders within a nested data structure.

    This function traverses dictionaries and lists, replacing string values
    that contain variable placeholders (e.g., "{self.name}") with actual
    values from the provided data structure. Placeholders support dot notation
    for nested attributes.

    Parameters
    ----------
    data : dict
        The input dictionary containing values and placeholders.
    root_var_name : str, optional
        The root variable name used for substitution. Defaults to "self".

    Returns
    -------
    dict
        A new dictionary with placeholders substituted. If no substitutions
        are found, the original data is returned unchanged.

    Notes
    -----
    - Placeholders must be enclosed in curly braces (e.g., "{self.key}").
    - Supports nested dictionaries and lists.
    - Uses DotObject internally to allow attribute-style substitution.

    Examples
    --------
    >>> test_data = {
    ...     "user": {"name": "Alice"},
    ...     "greeting": "Hello {self.user.name}!"
    ... }
    >>> substitute_variable(test_data)
    {'user': {'name': 'Alice'}, 'greeting': 'Hello Alice!'}
    """     # noqa
    def replace(txt, **kwargs):
        """
        Replace variable placeholders within a text string.

        This helper function scans the given text for placeholders enclosed
        in curly braces (e.g., "{self.attr.subattr}") and attempts to replace
        them with values provided in `kwargs`. Placeholders support dot notation
        for nested attributes. If substitution fails, the original placeholder
        is preserved.

        Parameters
        ----------
        txt : str
            The input text containing placeholders.
        **kwargs : keywords arguments
            Mapping of variable names to values used for substitution.
            If a single variable is provided, the regex pattern is scoped
            to that variable name. Otherwise, a general pattern is used.

        Returns
        -------
        str
            A new string with placeholders substituted where possible.
            If no substitutions are made, the original text is returned.

        Notes
        -----
        - Placeholders must be enclosed in curly braces `{}`.
        - Dot notation is supported for nested attributes (e.g., "{self.user.name}").
        - Substitution uses Python's `str.format` mechanism.
        - If substitution raises an exception, the placeholder is left unchanged.

        Examples
        --------
        >>> replace("Hello {self.name}!", self={"name": "Alice"})
        'Hello Alice!'

        >>> replace("Value: {obj.value}", obj={"value": 42})
        'Value: 42'

        >>> replace("Unchanged: {missing.key}", data={"other": "x"})
        'Unchanged: {missing.key}'
        """
        if len(kwargs) == NUMBER.ONE:
            var_name = list(kwargs)[NUMBER.ZERO]
            pattern = r'(?i)[{]%s([.][a-z]\w*)+[}]' % var_name
        else:
            pattern = r'(?i)[{][a-z]\w*([.][a-z]\w*)+[}]'
        lines = txt.splitlines()
        for index, line in enumerate(lines):
            if line.strip():
                lst = []
                start = NUMBER.ZERO
                for match in re.finditer(pattern, line):
                    lst.append(line[start:match.start()])
                    start = match.end()
                    matched_result = match.group()
                    try:
                        val = matched_result.format(**kwargs)
                        lst.append(val)
                    except Exception as ex:     # noqa
                        lst.append(matched_result)
                else:
                    if lst:
                        lst.append(line[start:])
                        lines[index] = str.join(STRING.EMPTY, lst)

        new_txt = str.join(STRING.NEWLINE, lines)
        return new_txt

    def substitute(node, variables_):
        """
        Recursively substitute variable placeholders within a nested data structure.

        This helper function traverses dictionaries and lists, replacing string
        values that contain placeholders with actual values from the provided
        `variables_` mapping. Placeholders can use dot notation to reference
        nested attributes. Non-string values are left unchanged.

        Parameters
        ----------
        node : dict or list
            The data structure to process. Must be a dictionary or list; other
            types are ignored.
        variables_ : dict
            A mapping of variable names to values used for substitution. Passed
            into `replace` for string substitution.

        Returns
        -------
        None
            The function mutates the input `node` in place, updating string
            values with substituted results.

        Notes
        -----
        - For dictionaries: each key's value is processed recursively.
        - For lists: each item is processed recursively.
        - String values are substituted using either `replace` (for dicts) or
          `str.format` (for lists).
        - Non-dict and non-list nodes are ignored.

        Examples
        --------
        >>> test_data = {"user": {"name": "{self.name}"}}
        >>> substitute(data, {"self": {"name": "Alice"}})
        >>> test_data
        {'user': {'name': 'Alice'}}

        >>> items = ["Hello {obj.greeting}", {"nested": "{obj.value}"}]
        >>> substitute(items, {"obj": {"greeting": "World", "value": 42}})
        >>> items
        ['Hello World', {'nested': '42'}]
        """     # noqa
        if isinstance(node, dict):
            for key, val in node.items():
                if isinstance(val, dict) or isinstance(val, list):
                    substitute(val, variables_)
                else:
                    if isinstance(val, str):
                        new_val = replace(val, **variables_)
                        node[key] = new_val
        elif isinstance(node, list):
            for index, item in enumerate(node):
                if isinstance(item, dict) or isinstance(item, list):
                    substitute(item, variables_)
                else:
                    if isinstance(item, str):
                        new_item = item.format(obj=variables_)
                        node[index] = new_item
        else:
            return

    if not isinstance(data, dict):
        return data

    substituted_data = DotObject(deepcopy(data))        # noqa
    substitute(substituted_data, {root_var_name: substituted_data})
    new_data = deepcopy(data)
    variables = {root_var_name: substituted_data}
    substitute(new_data, variables)
    return new_data
