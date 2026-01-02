import sympy as sp
from numbers import Integral

def validate_primes(*args):
    """Validates that all inputs are prime numbers and raises an exception if not.
    """
    for x in args:
        if not sp.isprime(x):
            raise ValueError("Input must be prime", x)

def validate_integers(*args):
    """Validates that all inputs are integer type and raises an exception if not.
    """
    for x in args:
        if not isinstance(x, Integral):
            raise TypeError("Input must be an integer", x)
        


        