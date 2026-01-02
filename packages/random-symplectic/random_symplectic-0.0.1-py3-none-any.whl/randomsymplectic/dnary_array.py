from __future__ import annotations

from typing import Self, Any 
import warnings

from abc import ABCMeta, abstractmethod

import numpy as np
import math

from randomsymplectic.dnary_arithmetic import rint, dnary_inverse, int_to_dnary, dnary_to_int
from randomsymplectic.validation import validate_primes

def d_get(cls) -> int:
    if hasattr(cls, '_d'):
        return cls._d
    raise TypeError(
        'Tried to access the modulus d on an undefined class.' \
        'Use `DnaryArray.set_d(...)` to create a subclass with a ' \
        'specific value of d.')
def d_set(cls, value):
    raise AttributeError('You cannot change d')
def d_del(cls):
    raise AttributeError('You cannot delete d')
dprop = property(d_get, d_set, d_del, 'The modulus of the set of arrays.')

class DNaryMeta(ABCMeta):
    """A metaclass for d-nary arrays that handles property creation for the class modulus d as an immutable class property.
    """
    d=dprop
    
    def check_or_coerce_type(cls, u:Any) -> Self:
        """Coerces the input into the type of the current class.

        Args:
            u (Any): A symplectic array-like object to be coerced into the current class.

        Raises:
            TypeError: The object could not be typecast as the new type.

        Returns:
            Self: The input object cast into the new type.
        """
        if not isinstance(u, cls):
            print(f'Coercing type on {u} {type(u)} to {cls}')
            try:
                u = cls(u)
            except Exception as e:
                raise TypeError("Input must be array-like", e, u)
        return u
    

class DnaryArray(np.ndarray, metaclass=DNaryMeta):
    r"""
    A subclass of `numpy.ndarray` for arrays over the integers
    mod $d$. Users can specify $d$ using the classmethod
    [`DnaryArray.set_d`][randomsymplectic.DnaryArray.set_d],
    which will return a subclass of `DnaryArray` specialized
    to the given modulus. Instances of that subclass behave as
    normal `numpy` arrays, but all outputs will be computed
    using arithmetic in $\mathbb{Z}_d$.
    
    Instances can be created from any array-like data
    acceptable by `np.array(...)`.

    Within a given d-nary class, 
    [symplectic](https://en.wikipedia.org/wiki/Symplectic_matrix)
    algebra on matrices and vectors over 
    $\mathbb{Z}_d$, the modulo-$d$ integers, can be performed:

    - Validation of symplectic matrices
        ([`.is_symplectic_matrix()`][randomsymplectic.DnaryArray.is_symplectic_matrix])
    - Symplectic vector inner products
        (`u | v` or [`u.inner_product_with(v)`][randomsymplectic.DnaryArray.inner_product])
    - Uniform sampling over the group of symplectic arrays of a given size 
        ([`.random_symplectic(n)`][randomsymplectic.DnaryArray.random_symplectic])
    - Accessing the defining symplectic array $\Lambda_n$ 
        (either [`A.Lambda`][randomsymplectic.DnaryArray.Lambda] 
        matching the invoking array's dimension, or the classmethod
        [`.LambdaN(n)`][randomsymplectic.DnaryArray.LambdaN] for a given $n$)
    
    Note:
        For a given $n>0$, the symplectic group $\text{Sp}(2n, \mathbb{Z}_d)$
        is the group of $2n\times2n$ matrices $A$ such that
        $$ A^T \Lambda_n A=\mathbb{I}_{2n},$$
        where
        $$\Lambda_n=\begin{bmatrix}0 & -\mathbb{I}_n \\ \mathbb{I}_n & 0 \end{bmatrix} \text{ mod } d$$
        and $\mathbb{I}_n$ is the $n\times n$ identity matrix.

        The matrix $\Lambda_n$ may be defined differently in other contexts.
        The definition used here follows
        [arXiv:quant-ph/0408190](https://arxiv.org/abs/quant-ph/0408190).
        See [here](https://en.wikipedia.org/wiki/Symplectic_matrix#The_matrix_%CE%A9)
        for other definitions.

        Similarly, the symplectic inner product $\langle v, w\rangle$
        between length-$2n$ vectors $v,w$ is
        defined as
        $$ \langle v, w\rangle = v^T\Lambda_n w.$$

        If $\langle v, w\rangle=-1 \text{ mod } d$, we say 
        $(v,w)$ is a symplectic pair.

        An equivalent definition for a symplectic matrix
        is the requirement that, for each $0\leq i< n$, the 
        matrix's $i$th and $(i+n)$th columns form a symplectic pair.

    Examples:
    ```
    >>> D3 = DnaryArray.set_d(3)
    >>> D3([1, 2, 3, 4])
    DnaryArray(d=3)([1, 2, 0, 1])

    >>> D3.eye(4)
    D3([[1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]])

    >>> D3.eye(4)-2
    D3([[2, 1, 1, 1],
        [1, 2, 1, 1],
        [1, 1, 2, 1],
        [1, 1, 1, 2]])

    >>> (D3.eye(4)-2).inverse()
    D3([[2, 1, 1, 1],
        [1, 2, 1, 1],
        [1, 1, 2, 1],
        [1, 1, 1, 2]])

    >>> import numpy as np
    >>> np.linalg.matrix_power(D3.eye(4)-2, 2)
    D3([[1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]])
    
    >>> MyD6Array = DnaryArray.set_d(6)
    >>> (2 * MyD6Array.eye(2)) @ [2,3]
    MyD6Array([4, 0])
    ```
    """
    
    d: int = dprop
    _class_instances = {}
    
    def __new__(cls, data: Any, *args, **kwargs) -> Self:
        if not isinstance(cls.d, int):
            raise TypeError('Cannot instantiate base class without a definition for d.')
        d = cls.d
        array = np.array(data, dtype=int) % d

        obj = array.view(cls)
        return obj
    
    def __array_finalize__(self, obj):
        if obj is None: return
        if not issubclass(self.dtype.type, np.integer):
            raise ValueError('Would result in array with non-integer values', self)
        
        if self.ndim==1:
            # nn = len(self)
            pass
        elif self.ndim==2:
            l, w = self.shape
            if not l==w:
                raise ValueError('Would result in array or vector of incorrect size', self)
            # nn = l
        else: raise ValueError('Would result in array or vector of incorrect size', self)
    
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        # print(f"In __array_ufunc__ with self {self} and inputs {inputs}")
        ds = set([input.d for input in inputs if isinstance(input, type(self))])
        inputs_ = []
        ds = set()
        for input_ in inputs:
            if isinstance(input_, type(self)):
                inputs_.append(input_.view(np.ndarray))
                ds.add(input_.d)
            else:
                inputs_.append(input_)

        if len(ds)>1:
            raise TypeError('Cannot compute with arrays with different moduli:', ds)
        d = ds.pop()
        result = super().__array_ufunc__(ufunc, method, *inputs_, **kwargs)
        if result is NotImplemented:
            return NotImplemented 
        
        if result.ndim==0:
            return result.item() % d
         
        result_obj = np.asarray(result % d).view(type(self))
        
        # result_obj.d = d
        return result_obj


    @property
    def is_matrix(self) -> bool:
        """
        Returns:
            Whether this is a 2D array.
        """
        return self.ndim==2
    
    @property
    def is_vector(self) -> bool:
        """
        Returns:
            Whether this is a 1D array.
        """
        return self.ndim==1
    
    @classmethod
    def dnary_inverse(cls, n: int) -> int:
        r"""
        Alias for [`dnary_inverse(n, cls.d)`][randomsymplectic.dnary_arithmetic.dnary_inverse].
        Calculates the multiplicative inverse of `n` in $\mathbb{Z}_d$ if it exists.

        If $d$ is prime and $n>0$, the integer is guaranteed to exist.
        For general $d$, $n^{-1}$ exists if $\text{gcd}(n,d)=1$.

        Args:
            n (int): The integer to invert.

        Returns:
            The integer $n^{-1}$ such that $n n^{-1} \text{ mod } d = 1$, 
                or `None` if such an integer does not exist.
                
        """
        return dnary_inverse(n, cls.d)
    
    @classmethod
    def int_to_dnary(cls, n:int, result_list_size:int|None=None) -> list[int]:
        r"""Alias for [`int_to_dnary(n, cls.d)`][randomsymplectic.dnary_arithmetic.int_to_dnary].
        
        Decomposes a base 10 integer into a list of its $d$-nary digits.

        See also [randomsymplectic.DnaryArray.dnary_to_int].

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
        return int_to_dnary(n, cls.d, result_list_size)
    
    @classmethod
    def dnary_to_int(cls, digits) -> int:
        """Alias for [`int_to_dnary(n, cls.d)`][randomsymplectic.dnary_arithmetic.dnary_to_int].
        Given a list of the $d$-nary digits of a number, return that
        number in base 10. 

        See also [randomsymplectic.DnaryArray.int_to_dnary].

        Args:
            digits (list[int]): A list of the $d$-nary digits of a
                number.

        Returns:
            The number in base 10.
        """
        return dnary_to_int(digits, cls.d)
    
    def is_nonzero(self) -> bool:
        """
        Returns:
            Whether the array has any nonzero values in it.
        """
        return bool(self.any())
    
    def is_zero(self) -> bool:
        """
        Returns:
            Whether the array is all zero.
        """
        return not self.is_nonzero()

    @classmethod
    def random_array(cls, shape:tuple[int], allow_zero=True) -> Self:
        """Returns an array of the given shape with uniform
        random integers mod $d$, including the all-zero array
        unless specified otherwise.

        Args:
            shape (tuple[int]): The shape of the array.
            allow_zero (bool, optional): Whether to allow the zero 
                matrix. Defaults to `True`.

        Returns:
            A uniform random $d$-nary array.
        """
        if allow_zero:
            return cls(np.random.randint(0, cls.d, shape))
        for _ in range(1000):
            a = cls.random_array(shape, allow_zero=True)
            if a.is_nonzero():
                return a
        raise RuntimeError('Could not create a non-zero random matrix.')
    
    @classmethod
    def eye(cls, n: int) -> Self:
        """
        Returns:
            The `(n, n)` identity matrix with integer type.
        """
        return cls(np.identity(n, dtype='int32'))
    
    @classmethod
    def zeros(cls, shape:int|tuple[int]) -> Self:
        """Returns an all-zero array of the given shape.

        Args:
            shape (int|tuple[int]): The shape of the desired array.

        Returns:
            The zero array of the given shape.
        """
        return cls(np.zeros(shape, dtype='int32'))
    
    @classmethod
    def basis_vector(cls, i: int, n: int) -> Self:
        """Generates the $i$th standard basis vector of
        length $n$. This is the vector of all zeros except
        the $i$th component equal to $1$.

        Args:
            i (int): The component of the basis vector.
            n (int): The length of the vector

        Returns:
            The $i$th standard basis vector.

        Examples:
        ```
        >>> class D3(DnaryArray): d=3
        >>> D3.basis_vector(1, 5)
        D3([0, 1, 0, 0, 0])
        ```
        """
        e_i = cls.zeros(n)
        e_i[i]=1
        return e_i
    
    def determinant(self) -> int:
        """
        Returns:
            The determinant of the array modulo d.
        """
        return rint(np.linalg.det(self)) % self.d
    
    def det(self) -> int:
        """Alias for [`.determinant`][randomsymplectic.DnaryArray.determinant].

        Returns:
            The determinant of the array modulo $d$.
        """
        return self.determinant()
    
    def is_invertible(self) -> bool:
        r"""Determines if an array is invertible by checking if
        its determinant is invertible in $\mathbb{Z}_d$.

        Returns:
            Whether the array is invertible.
        """
        return self.dnary_inverse(self.det()) is not None
    
    def mod_matrix_inv(self, validate=True, suppress_warnings=True) -> Self|None:
        r"""Calculates the matrix inverse in $\mathbb{Z}_d$-arithmetic
        using
        $$A^{-1}=\frac{1}{|A|}\text{Adj}(A),$$
        where $\text{Adj}(A)$ is the
        [matrix adjugate](https://en.wikipedia.org/wiki/Adjugate_matrix)
        of $A$ and $|A|$ is the determinant.

        Args:
            validate (bool, optional): Whether to validate the
                result through multiplication. Defaults to True.
            suppress_warnings (bool, optional): If False,
                warnings will be raise if the array is not
                invertible. Defaults to True.

        Raises:
            RuntimeError: If the inversion fails for an invertible
                array. Theoretically this should never happen.

        Returns:
            The array's inverse, or `None` if the array
                is not invertible.
        """
        
        det = self.determinant()

        if not(det_inv:=self.dnary_inverse(det)):
            if not suppress_warnings: 
                warnings.warn("Tried to invert non-invertible matrix", RuntimeWarning, stacklevel=2, source=self)
            return None
        
        inverse = det_inv * self._mod_matrix_adjugate()

        if validate:
            if not np.array_equal(inverse @ self, self.eye(len(self))):
                raise RuntimeError("Matrix inversion failed with non-zero invertible determinant.", self, inverse, det)
        
        return inverse

    def inv(self, **kwargs) -> Self|None:
        """Alias for [`mod_matrix_inv`][randomsymplectic.DnaryArray.mod_matrix_inv].

        Returns:
            The array's inverse, or `None` if
                the array is not invertible.
        """
        return self.mod_matrix_inv(**kwargs)
    
    def inverse(self, **kwargs) -> Self|None:
        """Alias for [`mod_matrix_inv`][randomsymplectic.DnaryArray.mod_matrix_inv].

        Returns:
            The array's inverse, or `None` if the
                array is not invertible.
        """
        return self.mod_matrix_inv(**kwargs)
    
    def _mod_matrix_adjugate(self) -> np.ndarray:
        l, w = self.shape
        Adj = self.zeros(self.shape)
        for i in range(l):
            for j in range(w):
                Adj[i,j] = self._matrix_cofactor(j,i) ## note the transpose here. Adj_{i,j} = C_{j,i}

        return Adj

    def _matrix_cofactor(self, row: int, col: int) -> int:
        """The elements of the cofactor matrix are
        $C_{i,j} = (-1)^{i+j} M_{i,j}$, where M is
        the matrix of minors of A.
        """
        return (-1)**(row+col) * self._matrix_minor(row,col)

    def _matrix_minor(self, row: int, col: int) -> int:
        """
        The elements of the minor matrix $M_{i,j}$
        are the determinants of $A$ with rows $i,j$ deleted.
        """
        
        l, w = self.shape

        if not (l==w and l>1):
            raise ValueError("Invalid matrix", self)
        
        B = self._matrix_delete_rowcol(row,col)

        return rint(np.linalg.det(B))
                
    def _matrix_delete_rowcol(self, row: int, col: int) -> np.ndarray:
        """Delete the given row and column and return the reduced array.
        """
        B = self.view(np.ndarray)
        B=np.delete(B,row,0)
        B=np.delete(B,col,1)
        return B

    @classmethod
    def set_d(cls, d:int) -> type[DnaryArray]:
        """Classmethod for creating a child class with a specific d.

        Args:
            d (int): The modulus of the class to create.

        Returns:
            _type_: _description_
        """
        if d not in cls._class_instances:
            cls._class_instances[d] = type(f'{cls.__name__}(d={d})', (cls, ), {'_d':d})

        return cls._class_instances[d]
        

    @property
    def n(self) -> int:
        r"""
        Half of the array size. Will raise an exception for odd-sized arrays.
        
        Defines the defining symplectic array $\Lambda_n$. See the 
        [`.Lambda`][randomsymplectic.DnaryArray.Lambda] property
        and the [`.LambdaN`][randomsymplectic.DnaryArray.LambdaN] method. 

        Raises:
            ValueError: Not accessible for odd-sized arrays.

        Returns:
            Half of the array size.
        """
        if self.nn%2==0:
            return self.nn//2
        raise ValueError('Cannot perform symplectic operations with odd-sized array:', self)

    @property
    def nn(self) -> int:
        """
        Returns:
            The symplectic array size $2n$.
        """
        return len(self)
    
    @classmethod
    def LambdaN(cls, n: int) -> Self:
        r"""Returns the defining symplectic array $\Lambda_n$ for any given $n$ 
        using the class modulus $d$.

        See [`DnaryArray`][randomsymplectic.DnaryArray].

        Args:
            n (int): $\Lambda_n$ is a $2n\times 2n$ array.

        Returns:
            The $d$-nary (2n, 2n) array that defines the symplectic group and symplectic inner product.
        """
        U = np.zeros((2*n,2*n),dtype='int32')
        for i in range(n):
            U[i + n,i]=1
        return cls((U - U.T))
    
    @property
    def Lambda(self) -> Self:
        r"""
        Returns:
            The defining symplectic array matching the invoking
                object's dimension ($2n\times 2n$).
                
                See [`.LambdaN`][randomsymplectic.DnaryArray.LambdaN].
        """
        return self.LambdaN(self.n)

    def is_symplectic_pair_with(self, other: Self) -> bool:
        r"""If the calling object is a vector (i.e. 1D array),
        determine whether it forms a symplectic pair with another
        vector.

        See the [`.is_symplectic_pair`][randomsymplectic.DnaryArray.is_symplectic_pair]
        classmethod.

        Raises an exception if the calling object is not a vector.

        Args:
            other (Self): The other vector.

        Raises:
            TypeError: Both the calling object and the input 
                must be 1d arrays.

        Returns:
            Whether the two vectors form a
                symplectic pair.
        """
        if not self.is_vector and other.is_vector:
            raise TypeError('Can only compute symplectic pairs between vectors', self, other)
        return self.__class__.is_symplectic_pair(self, other)
    
    def is_symplectic_matrix(self) -> bool:
        """
        Returns:
            Whether the calling array is a symplectic matrix.
        """
        result = np.array_equal(
            self.Lambda,
            (self.T @ self.Lambda @ self),
        )
        return result
    

    def inner_product_with(self, other: Self) -> int:
        r"""Compute the symplectic inner product
        of the calling vector with the other vector.

        See the [`.inner_product`][randomsymplectic.DnaryArray.inner_product]
        classmethod.

        Args:
            other (Self): The other vector.

        Returns:
            The symplectic inner product of the calling
                vector with the other vector.

        Tip:
            Python's pipe operator `|` is overloaded with this method, so you can
            call `v1.inner_product_with(v2)` as `v1 | v2`.

        Examples:
        ```
        >>> D3 = DnaryArray.set_d(3)
        >>> v1 = D3([1, 0, 0, 0])
        >>> v2 = D3([0, 0, 1, 0])
        >>> v1 | v2
        2
        ```
        """
        return self.__class__.inner_product(self, other)
    
    def __or__(self, other) -> int:
        return self.inner_product_with(other)
    
    def embed_symplectic(self) -> Self:  
        r"""Embeds a $2n\times 2n$ array into a
        $(2n+1)\times(2n+1)$ array via the symplecticity-preserving
        block embedding
        $$
        \begin{bmatrix}
            M_{11} & M_{12}\\
            M_{21} & M_{22}
        \end{bmatrix}
        \mapsto
        \begin{bmatrix}
            1 & 0 & 0 & 0\\
            0& M_{11} & 0 & M_{12}\\
            0 & 0 & 1 & 0\\
            0 & M_{21} & 0 & M_{22}
        \end{bmatrix},
        $$
        which inserts identity rows/columns at indices
        $0$ and $n$ (Python indexing) and fills the gaps with zeros.

        Returns:
            The embedded array.
        """
        if not self.is_matrix:
            raise ValueError("Can only perform symplectic embedding for square arrays.")
        n, nn = self.n, self.nn
        e0 = self.basis_vector(0, nn+2).view(np.ndarray)
        e1 = self.basis_vector(n+1, nn+2).view(np.ndarray)

        zs = np.zeros((1,nn),dtype='int32')
        Q = self.view(np.ndarray)
        Q = np.insert(Q, 0, zs, axis=0)
        Q = np.insert(Q, n+1, zs, axis=0)
        Q = np.insert(Q, 0, e0, axis=1)
        Q = np.insert(Q, n+1, e1, axis=1)
        return type(self)(Q)
    
    @classmethod
    def inner_product(cls, v1: Self|np.ndarray, v2: Self|np.ndarray) -> int:
        r"""Computes the symplectic inner product of the
        given vectors.

        The symplectic inner product $\langle v, w\rangle$
        between length-$2n$ vectors $v,w$ is
        defined as
        $$ \langle v, w\rangle = v^T\Lambda_n w.$$ 

        Args:
            v1 (Self|np.ndarray): The first vector. Will be coerced into the type of the calling class.
            v2 (Self|np.ndarray): The second vector. Will be coerced into the type of the calling class.

        Raises:
            ValueError: Input arrays are not one-dimensional.
            ValueError: Input arrays are not the same size.

        Returns:
            The symplectic inner product of `v1` and `v2`.

        Tip:
            If you've already created a vector `v`, you can call
            `v.inner_product_with(w)` method to compute
            $\langle v,w\rangle$.

        Note:
            The modulus $d$ is defined by the calling class.
            Thus, `v1` and `v2` can be any array-like data, but they
            will be coerced into the type of the calling class
            (by coercing components to integers and modding by $d$).
        """
        v1 = cls.check_or_coerce_type(v1)
        v2 = cls.check_or_coerce_type(v2) 

        if not (v1.ndim==1 and v2.ndim==1):
            raise ValueError(f"Inputs must be 1-d vectors", v1, v2)
        
        try:
            result = v1 @ v1.Lambda @ v2
            # assert isinstance(result, int)
            return result
        except ValueError as e:
            raise ValueError(f"Vectors must have the same dimensions", v1, v2, e)

    @classmethod
    def is_symplectic_pair(cls, v1: Self, v2: Self) -> bool:
        r"""Determine whether a pair of vectors 
        form a symplectic pair.

        Two vectors $v, w$ form a symplectic pair if
        $$\langle v, w\rangle = -1 \text{ mod } d.$$

        See also [`.is_symplectic_pair_with`][randomsymplectic.DnaryArray.is_symplectic_pair_with].

        Args:
            v1 (Self): The first vector.
            v2 (Self): The second vector.

        Returns:
            Whether the vectors form a symplectic pair.
        """
        return cls.inner_product(v1, v2)==(-1 % cls.d)
        
    @classmethod
    def symplectic_group_size(cls, n: int) -> int:
        r"""Returns the size of the symplectic group for a given $n$.
        That number is $$\prod_{i=1}^n d^{2i-1}(d^{2i}-1).$$ 

        Args:
            n (int): Half the size of the symplectic matrix,
                or the number of qubits in the equivalent Clifford group.

        Returns:
            The number of different $2n\times 2n$ symplectic
                matrices over $\mathbb{Z}_d$. 
        """
        d = cls.d
        return math.prod((d**(2*j-1)) * (d**(2*j)-1) for j in range(1, n+1))

    @classmethod
    def random_symplectic(cls, n: int) -> Self:
        """Generate a uniformly random element of the symplectic group.

        Args:
            n (int): Half the size of the symplectic matrix to be generated, or the number of qubits in the equivalent Clifford group.

        Returns:
            Self: A uniform random $d$-nary symplectic matrix.
        """

        nn = 2*n
        e1 = cls.basis_vector(0, nn)
        en = cls.basis_vector(n, nn)

        v = cls.random_array(nn, allow_zero=False)

        t1, t2 = cls.Transvection.find_transvection(e1, v)

        assert np.array_equal(t1(t2(e1)), v), (v, t1, t2)

        b = cls.random_array(nn, allow_zero=True)
        b[n]=0
        u0 = t1(t2(b))

        assert u0|v == 0


        T_prime = cls.Transvection(u0, c=1)

        # w = T_prime(t1(t2(en)))

        if n==1:
            Q=cls.eye(2)
        else:
            Q=cls.random_symplectic(n-1).embed_symplectic()
        
        return T_prime(t1(t2(Q)))

    @classmethod
    def from_index(cls, index:int, n:int) -> Self:
        """Generate an element of the symplectic group from
        that element's index. 

        Args:
            index (int): An integer from 0 (inclusive) to the
                size of the symplectic group (exclusive). See
                [`.symplectic_group_size`][randomsymplectic.DnaryArray.symplectic_group_size].
            n (int): Half the size of the symplectic matrix to be generated,
                or the number of qubits in the equivalent Clifford group.

        Returns:
            Self: The symplectic matrix corresponding to the input index.
        """
        assert index in range(cls.symplectic_group_size(n))

        d = cls.d
        nn = 2*n
        e1 = cls.basis_vector(0, nn)
        en = cls.basis_vector(n, nn)
        
        v1_count = d**(2*n) - 1 ## the number of choices for v1
        v2_count = d**(2*n-1)   ## the number of choices for v2
        v1_v2_count = v1_count * v2_count ## the number of choices for (v1, v2)
        new_index, remainder = divmod(index, v1_v2_count)   ## div out the number of choices for (v1, v2)
                                                            ## remainder determines (v1, v2)
                                                            ## new_index will determine the next pair of vectors.

        v1_index = remainder % v1_count + 1
        v2_index = remainder//v1_count

        v1 = cls(cls.int_to_dnary((v1_index), result_list_size=nn))
        b = cls.int_to_dnary(v2_index, result_list_size=nn-1)
        b.insert(n, 0)
        b = cls(b)

        t1, t2 = cls.Transvection.find_transvection(e1, v1)

        assert np.array_equal(t1(t2(e1)), v1), (v1, t1, t2)

        u0 = t1(t2(b))
        assert u0|v1 == 0, (n, v1, b, u0)

        T_prime = cls.Transvection(u0, c=1)
        # v2 = T_prime(t1(t2(en)))

        if n==1:
            Q=cls.eye(2)
        else:
            Q=cls.from_index(new_index, n-1).embed_symplectic()
    
        return T_prime(t1(t2(Q)))
    
    class Transvection:
        r"""A class representing transvections, a class of linear transformations on vectors.
        Transvections are defined by a vector $\vec u$ and a constant $c$, and act as
        $v\mapsto T_{u, c}(v)=v + c\langle v, u\rangle u$. All arithmetic is mod d.
        Transvections applied to matrices apply the above transformation column-wise.

        Args:
            u (DnaryArray): The vector to transvect by.
            c (int): The constant of the transvection.
        """
        def __init__(self, u: DnaryArray, c:int):
            self.u = u
            self.c = c

        def __call__(self, vector_or_matrix: DnaryArray) -> DnaryArray:
            """Apply the transvection to a vector or matrix of the same type as the transvection's vector.

            Args:
                vector_or_matrix (DnaryArray): A vector or matrix of the same type as the Transvection's vector.

            Returns:
                DnaryArray: The transvection applied to the vector or matrix.
            """
            if vector_or_matrix.is_matrix:
                return self.transvect_matrix_columns(vector_or_matrix)
            
            assert vector_or_matrix.is_vector

            return vector_or_matrix + self.c*(vector_or_matrix | self.u)*self.u
        
        def __repr__(self):
            return f'({self.u.__repr__()}, {self.c.__repr__()})'
        
        def transvect_vector(self, v: DnaryArray) -> DnaryArray:
            """Apply the transvection to a vector of the same type as the transvection's vector.

            Args:
                v (DnaryArray): A vector of the same type as the Transvection's vector.

            Returns:
                DnaryArray: The transvection applied to the vector.
            """
            return v + self.c*(v | self.u)*self.u
        
        def transvect_matrix_columns(self, A: DnaryArray) -> DnaryArray:
            """Apply the transvection to a matrix of the same type as the transvection's vector.

            Args:
                A (DnaryArray): A matrix of the same type as the Transvection's vector.

            Returns:
                DnaryArray: The transvection applied to the matrix.
            """
            rows,cols = A.shape
            # ans = np.zeros((rows, cols), dtype='int')
            ans = np.zeros_like(A)
            for i in range(cols):
                ans[:,i] = self(A[:,i])
            return ans
        
        @classmethod
        def _easy_transvection(cls, u: DnaryArray, v: DnaryArray) -> Self:
            r"""Find a transvection from $u$ to $v$ in the simple case where $\langle u, v\rangle \neq 0$.

            Args:
                u (DnaryArray): Vector you are transvecting *from*.
                v (DnaryArray): Vector you are transvecting *to*.

            Raises:
                RuntimeError: A transvection from u to v does not exist.

            Returns:
                Self: A transvection T such that T(u)==v.
            """
            ## returns w, c such that v = Z_{w,c}(u)
            k = u | v
            if k==0:
                raise RuntimeError('No single transvection between vectors exists', u, v)
            w = v-u
            c = u.dnary_inverse(k)
            return cls(w, c)

        @classmethod
        def find_transvection(cls, u: DnaryArray, v: DnaryArray) -> tuple[Self, Self]:
            """Returns a tuple of transvections $T_1, T_2$ such that $T_2(T_1(u))=v$.

            Args:
                u (DnaryArray): Vector you are transvecting *from*.
                v (DnaryArray): Vector you are transvecting *to*.

            Returns:
                (Transvection, Transvection): A tuple (T1, T2) such that T2(T1(u))==v
            """
            nn=u.nn
            assert nn==v.nn
            n = u.n
            assert type(u) is type(v)
            SP_D = type(u)

            h1, h2 = SP_D(np.zeros(nn, dtype='int32')), SP_D(np.zeros(nn, dtype='int32'))
            c1, c2 = 0,0
            k = u | v
            
            if np.array_equal(u, v):
                return cls(h1, c1), cls(h2, c2)
            
            if k != 0:
                T1 = cls._easy_transvection(u, v)
                return T1, cls(h2, c2)
            
            
            z = np.zeros(nn, dtype='int32')
            u_found = 0
            v_found = 0
            for i in range(n):
                pair1 = (u[i], u[n+i])
                pair2 = (v[i], v[n+i])
                zero = (0,0)
                
                if (pair1 != zero) and (pair2 != zero):
                    if pair1[0] and pair2[0]:
                        z = z + SP_D.basis_vector(i+n, nn)
                    elif pair1[1] and pair2[1]:
                        z = z + SP_D.basis_vector(n, nn)
                    else:
                        z = z + SP_D.basis_vector(i, nn) + SP_D.basis_vector(n+i, nn)
                    assert u | z != 0, (u, v, z)
                    assert z | v != 0, (u, v, z)
                    T2 = cls._easy_transvection(u, z)
                    # assert np.array_equal(transvect(x,h2,c2,d),z)
                    assert np.array_equal(T2(u), z)
                    T1 = cls._easy_transvection(z, v)
                    # assert np.array_equal(transvect(z,h1,c1,d),y)
                    assert np.array_equal(T1(z), v)
                    return T1, T2
                
                if u_found == 0 and pair1 != zero:
                    u_found = i
                if v_found == 0 and pair2 != zero:
                    v_found = i
                    
            if u[u_found] != 0:
                z = z + SP_D.basis_vector(u_found+n, nn)
            else:
                assert u[u_found+n] != 0
                z = z + SP_D.basis_vector(u_found, nn)
            if v[v_found] != 0:
                z = z + SP_D.basis_vector(v_found+n, nn)
            else:
                assert v[v_found+n] != 0
                z = z + SP_D.basis_vector(v_found,nn)
                
            assert u|z != 0, (u, z)
            assert z|v != 0, (z, v)
            T2 = cls._easy_transvection(u, z)
            assert np.array_equal(T2(u),z)
            T1 = cls._easy_transvection(z,v)
            assert np.array_equal(T1(z),v)
            return T1, T2


    
