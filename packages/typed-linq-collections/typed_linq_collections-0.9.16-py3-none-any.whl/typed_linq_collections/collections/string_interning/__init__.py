"""String interning collections for memory-efficient string storage.

This module provides specialized collection classes that automatically intern string values,
reducing memory usage when the same strings are stored repeatedly.

Classes:
    QInterningList: A list that interns all string elements.
    QInterningStringSet: A set that interns all string elements.
    QKeyInterningDict: A dictionary that interns string keys.
    QKeyValueInterningDict: A dictionary that interns both string keys and values.

Functions:
    set_default_intern_func: Set the default interning function for all new instances.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from typed_linq_collections.collections.string_interning.q_interning_list import QInterningList
from typed_linq_collections.collections.string_interning.q_interning_string_set import QInterningStringSet
from typed_linq_collections.collections.string_interning.q_key_interning_dict import QKeyInterningDict
from typed_linq_collections.collections.string_interning.q_key_value_interning_dict import QKeyValueInterningDict

if TYPE_CHECKING:
    from collections.abc import Callable

# The default interning function used by all string interning collections
default_intern_func: Callable[[str], str] = sys.intern


def set_default_intern_func(func: Callable[[str], str]) -> None:
    """Set the default string interning function for all new collection instances.

    This allows you to configure a custom interning function once, which will be used
    by all subsequently created interning collections (unless overridden with the
    intern_func parameter in the constructor).

    Args:
        func: The interning function to use. Should take a string and return a string.
              Pass sys.intern to reset to the default behavior.

    Examples:
        >>> import sys
        >>> from typed_linq_collections.collections.string_interning import (
        ...     set_default_intern_func, QInterningList
        ... )
        >>> # Use uppercase as the "interning" function
        >>> set_default_intern_func(lambda s: s.upper())
        >>> lst = QInterningList(['hello', 'world'])
        >>> list(lst)
        ['HELLO', 'WORLD']
        >>> # Reset to default
        >>> set_default_intern_func(sys.intern)
    """
    global default_intern_func
    default_intern_func = func


__all__ = [
    "QInterningList",
    "QInterningStringSet",
    "QKeyInterningDict",
    "QKeyValueInterningDict",
    "set_default_intern_func",
]
