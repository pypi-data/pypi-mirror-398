def is_power_of_two(n: int) -> bool:
    """Return True if n is a power of two."""
    return n > 0 and (n & (n - 1)) == 0

def lowest_set_bit(n: int) -> int:
    """Return the lowest set bit (value)."""
    return n & (-n)