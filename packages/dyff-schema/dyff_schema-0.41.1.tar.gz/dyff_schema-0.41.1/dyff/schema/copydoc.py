# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0


def copydoc(fromfunc):
    """Copy the docstring of ``fromfunc``.

    If the annotated function has its own docstring, it will be appended after
    the docstring of ``fromfunc``.

    Args:
      fromfunc: The function to copy the docstring from (usually the
        the implementation of the annotation function in a superclass).
      sep: The separator to insert between the ``fromfunc`` docstring and
        the annotated function's docstring.

    See: https://stackoverflow.com/a/13743316
    """

    def _decorator(func):
        # Functions annotated with @property don't have __qualname__ or __name__
        if hasattr(fromfunc, "__qualname__"):
            sourcedoc = f"{fromfunc.__doc__}\n\nSee: {fromfunc.__qualname__}"
        else:
            sourcedoc = fromfunc.__doc__

        if func.__doc__ is None:
            func.__doc__ = sourcedoc
        else:
            func.__doc__ = f"{sourcedoc}\n\n{func.__doc__}"
        return func

    return _decorator
