import numpy as np
import sympy as sp
import math
# from math import gcd, log, ceil
from numbers import Real

from randomsymplectic.validation import validate_integers, validate_primes


def extra_ceil(n: Real) -> int:
    """
    Args:
        num (Real): The number to ceil

    Returns:
        Returns the smallest integer $N$ such that $N>n$.
    """
    result = math.ceil(n)
    if result==n:
        return int(result+1)
    return int(result)

def int_to_dnary(n: int, d: int, result_list_size: int|None=None) -> list[int]:
    r"""Decomposes a base 10 integer into a list of its $d$-nary digits.

    See also [`dnary_to_int`][randomsymplectic.dnary_arithmetic.dnary_to_int].

    Args:
        n (int): The base 10 integer to be factored into its $d$-nary digits.
        result_list_size (int | None, optional): The length of the
            list to return; if `None`, will use the minimum number
            of digits to result the input integer in $d$-nary.
            Defaults to `None`.

    Raises:
        ValueError: Invalid input parameters.

    Returns:
        A list of the $d$-nary digits of `n`
            The list has $L$ elements $l_i$ such that $$n=\sum_{i=0}^L l_i d^i.$$
    """
    validate_integers(n, d)
    if n<0:
        raise ValueError('Input integer must be non-negative', n)

    if n==0:
        required_size = 1
    else:
        required_size = extra_ceil(math.log(n, d))
    
    if result_list_size is None:
        result_list_size = required_size
    else:
        if not result_list_size >= required_size:
            raise ValueError(f'Input integer {n} requires more than {result_list_size} digits.')

    validate_integers(result_list_size)
    
    digits = [0 for _ in range(result_list_size)]

    for j in range(result_list_size):
        current_digit = rint(n%d)
        digits[j] = current_digit
        n -= current_digit
        n = n/d

    return digits

def dnary_to_int(digits: list[int], d: int) -> int:
    """
    Given a list of the $d$-nary digits of a number, return that
    number in base 10. 

    See also [`int_to_dnary`][randomsymplectic.dnary_arithmetic.int_to_dnary].

    Args:
        digits (list[int]): A list of the $d$-nary digits of a
            number.

    Returns:
        The number in base 10.
    """
    validate_integers(d, *digits)
    return sum(digits[i] * d**i for i in range(len(digits)))

def dnary_inverse(n: int, d: int) -> int|None:
    r"""
    Calculates the multiplicative inverse of `n` in $\mathbb{Z}_d$ if it exists.
    
    If $d$ is prime and $n>0$, the integer is guaranteed to exist.
    For general $d$, $n^{-1}$ exists if $\text{gcd}(n,d)=1$.

    Args:
        n (int): The integer to invert.
        d (int): The modulus to invert by.

    Returns:
        The integer $n^{-1}$ such that $n n^{-1} \text{ mod } d = 1$, 
            or `None` if such an integer does not exist.
    """
    
    try:
        return pow(n, -1, d)
    except ValueError:
        return None
    # except TypeError:
    #     if isinstance(input_integer, np.int_):
    #         return pow(int(input_integer), -1, d)
#     validate_integers(input_integer, d)
#     if sp.isprime(d) and input_integer!=0:
#         return input_integer**(d-2)%d

#     return euclid_algorithm(input_integer, d)

# def euclid_algorithm(input_integer:int, d:int) -> int:
#     validate_integers(input_integer, d)
#     if input_integer>d:
#         input_integer = input_integer%d
#     if not math.gcd(input_integer, d)==1:
#         return None
    
#     t, newt = 0, 1
#     r, newr = d, input_integer

#     while newr != 0:
#         quotient = r//newr
#         (t, newt) = (newt, t-quotient*newt) 
#         (r, newr) = (newr, r-quotient*newr)

#     if r > 1:
#         return None
#     if t < 0:
#         t = t + d

#     return t

def rint(i:Real)->int:
    """
    Args:
        i (Real)

    Returns:
        The input rounded to the nearest integer and cast as `int`. 
    """
    return int(np.rint(i))
