# Random Symplectic
Python library for generating uniformly random d-nary symplectic matrices for prime $d$. These matrices form a representation of the $n$-qudit Clifford  group and can be decomposed into elementary 1- and 2-qudit gates (Hostens, 2005). Uniform sampling from the Clifford group is a critical subroutine to randomized benchmarking (Magesan, 2012).

The algorithm implements a mapping from the integers to $\text{Sp}(2n, \mathbb{Z}_d)$, reducing sampling from the symplectic group to sampling an integer, and is an extension of the qubit-based method presented by Koenig and Smolin (2014). A manuscript detailing the algorithm is forthcoming.



## Installation
To install the package for Python 3.8+, do
```
pip install random-symplectic
```


## Getting Started
The package implements the `DnaryArray` class, a subclass of `numpy`'s `ndarray` for arrays over the integers mod $d$. Users can specify $d$ using the classmethod `DnaryArray.set_d`, which will return a subclass of `DnaryArray` specialized to the given modulus.
```python
>>> from randomsymplectic import DnaryArray
>>> D3 = DnaryArray.set_d(3)
>>> D3([1, 2, 3, 4])
DnaryArray(d=3)([1, 2, 0, 1])
```

In particular, a specialized subclass exposes a plethora of useful methods for doing symplectic algebra over the group of d-nary arrays, as well as generating symplectic matrices.

### Random Symplectic Matrices

`DnaryArray` has two classmethods for generating uniformly random symplecitc matrices: `DnaryArray.random_symplectic` and `DnaryArray.from_index`. The former operates by generating random d-nary vectors of lengths building up to the size of the matrix to be generated. The latter deterministically generates each of those vectors from the provided index.

```python
>>> from randomsymplectic import DnaryArray
>>> D3 = DnaryArray.set_d(3)
>>> D3.from_index(0, n=1)
DnaryArray(d=3)([[1, 0],
                 [0, 1]])
>>> D3.from_index(12152, 3)
DnaryArray(d=3)([[1, 0, 1, 2, 1, 1],
                 [0, 1, 0, 2, 1, 2],
                 [2, 0, 0, 1, 1, 0],
                 [0, 0, 2, 0, 1, 0],
                 [0, 0, 0, 0, 1, 0],
                 [2, 0, 2, 0, 2, 0]])
```

## References
1. E. Hostens, J. Dehaene, and B. De Moor, Stabilizer states and Clifford operations for systems of arbitrary dimensions and modular arithmetic, [Phys. Rev. A 71, 042315 (2005)](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.71.042315), [arXiv:quant-ph/0408190](https://arxiv.org/abs/quant-ph/0408190).
2. E. Magesan, J. M. Gambetta, and J. Emerson, Characterizing quantum gates via randomized benchmarking, [Phys. Rev. A 85, 042311 (2012)](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.85.042311), [arXiv:1109.6887v2](https://arxiv.org/abs/1109.6887v2).
3. R. Koenig and J. A. Smolin, How to efficiently select an arbitrary Clifford group element, [Journal of Mathematical Physics 55, 122202 (2014)](https://doi.org/10.1063/1.4903507), [arXiv:1406.2170](https://arxiv.org/abs/1406.2170).