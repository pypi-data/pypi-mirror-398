"""
GenericLib: A collection of reusable utilities for text processing, data
structures, constants, platform helpers, and formatted output.

This package consolidates commonly used components into a single namespace,
making it easier to import and work with them across applications. It exposes
a curated set of classes, functions, and constants through `__all__` for
convenient access.

Available components include:

- **Collection utilities**
  - `DictObject`: Dictionary wrapper with attribute-style access.
  - `DotObject`: Object-like interface for nested dictionaries.
  - `substitute_variable`: Helper for variable substitution in strings.

- **Text and file utilities**
  - `Text`: String manipulation and formatting helpers.
  - `File`: File I/O abstraction.
  - `RFFile`: Robot Framework–specific file utilities.

- **Search**
  - `Wildcard`: Pattern matching with wildcard support.

- **Constants**
  - `ECODE`: Error codes.
  - `ICSValue`, `ICSStripValue`: Specialized constant values.
  - `STRING`, `STR`, `TEXT`: String-related constants.
  - `NUMBER`, `INDEX`: Numeric constants.
  - `SYMBOL`: Symbolic constants.
  - `PATTERN`: Regular expression patterns.
  - `STRUCT`, `SLICE`: Structural constants.

- **Utilities**
  - `Printer`: Formatted printing of structured data.
  - `Misc`: General-purpose type checking and validation.
  - `MiscFunction`: Safe function invocation and error handling.
  - `MiscOutput`: Shell command execution with captured results.
  - `MiscObject`: Object manipulation and cleanup helpers.
  - `Tabular`: Tabular data formatting.
  - `get_data_as_tabular`, `print_data_as_tabular`: Convenience functions
    for tabular display.

- **Configuration**
  - `version`: Current package version.

The `__all__` list defines the public API of this package, ensuring that only
the most relevant and stable components are exported when using
`from genericlib import *`.
"""

from genericlib.collection import DictObject
from genericlib.collection import DotObject
from genericlib.collection import substitute_variable

from genericlib.text import Text
from genericlib.file import File

from genericlib.search import Wildcard

from genericlib.constant import ICSValue
from genericlib.constant import ICSStripValue
from genericlib.constant import ECODE
from genericlib.constant import STRING
from genericlib.constant import STR
from genericlib.constant import TEXT
from genericlib.constnum import NUMBER
from genericlib.constnum import INDEX
from genericlib.constsymbol import SYMBOL
from genericlib.constpattern import PATTERN
from genericlib.conststruct import STRUCT
from genericlib.conststruct import SLICE

from genericlib.utils import Printer
from genericlib.utils import Misc
from genericlib.utils import MiscOutput
from genericlib.utils import MiscFunction
from genericlib.utils import MiscObject
from genericlib.utils import Tabular
from genericlib.utils import get_data_as_tabular
from genericlib.utils import print_data_as_tabular

from genericlib.config import version

from genericlib.robotframeworklib import RFFile

__all__ = [
    'DictObject',
    'DotObject',

    'ECODE',
    'ICSValue',
    'ICSStripValue',
    'STRING',
    'STR',

    'INDEX',
    'NUMBER',
    'SYMBOL',
    'PATTERN',

    'STRUCT',
    'SLICE',
    'TEXT',

    'File',
    'RFFile',

    'Wildcard',

    'Misc',
    'MiscFunction',
    'MiscOutput',
    'MiscObject',

    'Printer',

    'Text',

    'Tabular',
    'get_data_as_tabular',
    'print_data_as_tabular',

    'substitute_variable',

    'version',
]
