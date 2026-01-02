"""
genericlib.misc
===============
Miscellaneous utility functions for genericlib.

This module provides helper routines that support standardized program
termination and other lightweight operations. It is intended to centralize
common functionality that does not belong to a specific domain module.


Notes
-----
- Exit codes are defined in `genericlib.ECODE` and should be used consistently
  across the application.
- This module is designed for lightweight, generic helpers that simplify
  application control flow.
"""


import sys

from genericlib import ECODE


def sys_exit(success=True, msg=''):
    """
    Terminate the program with a standardized exit code.

    This function prints an optional message and exits the program using
    predefined exit codes from `genericlib.ECODE`. It ensures consistent
    handling of success and failure termination across the application.

    Parameters
    ----------
    success : bool, optional
        Flag indicating whether the program should exit successfully.
        - True → exit with `ECODE.SUCCESS`
        - False → exit with `ECODE.BAD`
        Default is True.
    msg : str, optional
        An optional message to print before exiting. Default is an empty string.

    Returns
    -------
    None
        This function does not return. It terminates the program by calling
        `sys.exit()` with the appropriate exit code.

    Notes
    -----
    - `ECODE.SUCCESS` and `ECODE.BAD` must be defined in `genericlib.ECODE`.
    - If `msg` is provided, it is printed to standard output before termination.
    - This function is intended for controlled program termination and should
      be used instead of calling `sys.exit()` directly.
    """

    if msg:
        print(msg)
    exit_code = ECODE.SUCCESS if success else ECODE.BAD
    sys.exit(exit_code)
