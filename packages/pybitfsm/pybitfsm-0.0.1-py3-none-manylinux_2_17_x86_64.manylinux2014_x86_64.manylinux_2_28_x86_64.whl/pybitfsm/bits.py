'''Support routines for bit manipulation in Python.'''


def parse(s: str, digits='01') -> int:
    """Converts a string representing a bit sequence to an integer.

    The optional parameter `digits` specifies which characters represent
    zero and one bits.

    >>> parse('0 1 0 1')
    10
    >>> parse('1 0 0 1 1 0')
    25
    >>> parse('1 _ _ 1 1 _', digits='_1')
    25
    >>> parse('0', digits='')
    Traceback (most recent call last):
        ...
    ValueError: digits must contain exactly two characters
    >>> parse('1 _')
    Traceback (most recent call last):
        ...
    ValueError: Unrecognized binary digit: "_"

    """
    if len(digits) != 2:
        raise ValueError(f'digits must contain exactly two characters')
    s = s.replace(' ', '')
    result = 0
    for index, ch in enumerate(s):
        try:
            result |= digits.index(ch) << index
        except ValueError:
            raise ValueError(f'Unrecognized binary digit: "{ch}"') from None
    return result


def format(k: int, bits: int, digits='01') -> str:
    """Converts a `k`-bit integer representing a bit sequence to a string.

    The optional parameter `digits` specifies which characters represent
    zero and one bits.

    >>> format(17, 9123)
    '1 1 0 0 0 1 0 1 1 1 0 0 0 1 0 0 0'
    >>> format(17, 9123, digits='_1')
    '1 1 _ _ _ 1 _ 1 1 1 _ _ _ 1 _ _ _'
    >>> format(1, '0', digits='')
    Traceback (most recent call last):
        ...
    ValueError: digits must contain exactly two characters
    >>> format(0, 0)
    ''

    """
    if len(digits) != 2:
        raise ValueError(f'digits must contain exactly two characters')
    result = []
    for i in range(k):
        result.append(digits[bits & 1])
        bits = bits >> 1
    return ' '.join(result)


def is_set(x: int, i: int) -> bool:
    '''Returns True if the bit position `i` in `x` is 1, or False otherwise.

    >>> is_set(2, 0)
    False
    >>> is_set(2, 1)
    True
    >>> is_set(5, 0)
    True
    >>> is_set(5, 1)
    False
    >>> is_set(5, 2)
    True

    '''
    return ((x >> i) & 1) == 1


def clear(x: int, i: int) -> int:
    '''Returns `x` with bit position `i` set to 0.

    >>> clear(1, 0)
    0
    >>> clear(2, 0)
    2
    >>> clear(15, 2)
    11

    '''
    return x & ~(1 << i)


def get(x: int, i: int) -> int:
    '''Returns the value of bit position `i` in `x`.

    >>> get(1, 0)
    1
    >>> get(5, 1)
    0
    >>> get(5, 0)
    1
    '''

    return (x >> i) & 1


def set(x: int, i: int) -> int:
    '''Returns `x` with bit position `i` set to 1.

    >>> set(0, 0)
    1
    >>> set(3, 1)
    3
    >>> set(5, 1)
    7

    '''
    return x | (1 << i)


def truncate(k: int, x: int) -> int:
    '''Truncates the arbitrary-length integer `x` to `k` bits.

    >>> truncate(2, 7)
    3
    >>> truncate(0, 7)
    0
    >>> truncate(3, 9)
    1
    >>> truncate(4, -2)
    14

    '''
    return x & ((1 << k) - 1)


def prefix_xor(k: int, x: int) -> int:
    '''Computes the `k`-bit prefix XOR-sum of the arbitrary-length integer `x`.

    >>> prefix_xor(3, 0)
    0
    >>> prefix_xor(3, 0b001)
    7
    >>> prefix_xor(3, 0b011)
    1
    >>> prefix_xor(3, 0b101)
    3

    '''
    i = 1
    while i < k:
        x ^= x << i
        i *= 2
    return truncate(k, x)
