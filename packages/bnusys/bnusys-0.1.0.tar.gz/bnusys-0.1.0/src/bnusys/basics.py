"""Basic math helper functions for myexamplelib."""


def add(a, b):
    """Return the sum of a and b."""
    return a + b


def subtract(a, b):
    """Return the difference a - b."""
    return a - b


def mean(values):
    """Return the arithmetic mean of an iterable of numbers.

    Raises
    ------
    ValueError
        If `values` is empty.
    """
    values = list(values)
    if not values:
        raise ValueError("mean() arg is an empty sequence")
    return sum(values) / len(values)