import pytest
from bitcore import *

def test_is_even():
    assert is_even(2)
    assert not is_even(3)

def test_bit_count():
    assert bit_count(7) == 3