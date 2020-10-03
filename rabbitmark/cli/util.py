"""
util.py - miscellaneous CLI utilities
"""

def truncate(string: str, max_length: int) -> str:
    """
    Truncate /string/ to at most /max_length/ using an ellipsis.
    max_length must be at least 3.

    >>> truncate("The quick brown fox jumps over the lazy dog.", 10)
    'The qui...'

    >>> truncate("I fit already.", 20)
    'I fit already.'

    >>> truncate("The quick brown fox jumps over the lazy dog.", 2)
    Traceback (most recent call last):
      ...
    AssertionError: max_length must be at least 3...
    """
    assert max_length > 3, \
        "max_length must be at least 3, as an ellipsis is 3 characters itself"
    if len(string) > max_length:
        string = string[:max_length - 3] + '...'
    return string
