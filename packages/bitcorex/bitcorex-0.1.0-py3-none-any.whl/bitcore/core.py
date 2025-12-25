def is_even(n: int) -> bool:
    """Check if number is even using bitwise."""
    return (n & 1) == 0

def is_odd(n: int) -> bool:
    """Check if number is odd using bitwise."""
    return (n & 1) == 1

def bit_count(n: int) -> int:
    """Count number of set bits (Hamming weight)."""
    count = 0
    while n:
        count += n & 1
        n >>= 1
    return count