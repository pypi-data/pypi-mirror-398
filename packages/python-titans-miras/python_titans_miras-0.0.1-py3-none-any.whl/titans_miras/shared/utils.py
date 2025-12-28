def is_not_none(v):
    """
    Check if a value is not None.

    Args:
        v: Value to check

    Returns:
        True if v is not None, False otherwise
    """
    return v is not None


def identity(t):
    """
    Identity function that returns its input unchanged.

    Args:
        t: Input value

    Returns:
        The input value unchanged
    """
    return t


def xnor(x, y):
    """
    Logical XNOR (equivalence) operation.

    Returns True if both inputs have the same truth value,
    False otherwise.

    Args:
        x: First boolean value
        y: Second boolean value

    Returns:
        True if x == y, False otherwise
    """
    return not (x ^ y)


def divisible_by(num, den):
    """
    Check if a number is divisible by another.

    Args:
        num: Number to check (dividend)
        den: Divisor

    Returns:
        True if num is divisible by den (num % den == 0), False otherwise
    """
    return (num % den) == 0
