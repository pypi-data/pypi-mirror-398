import pytest
import numpy as np

from randomsymplectic import DnaryArray


SP2 = DnaryArray.set_d(2)
SP3 = DnaryArray.set_d(3)
SP5 = DnaryArray.set_d(5)
SP13 = DnaryArray.set_d(13)

def test_attributes_persist():
    u = SP5([1,0,0,0])
    v = SP5([1,0,0,0])
    result = v ^ u
    assert result.d==5
    assert result.n==2
    assert result.nn==4

    assert u.is_vector
    assert not u.is_matrix
    assert v.is_vector
    assert not v.is_matrix
    assert v.Lambda.is_matrix
    assert not v.Lambda.is_vector

def test_odd_dimension():
    size3 = SP3([1,2,3])

    with pytest.raises(ValueError):
        size3.Lambda

    with pytest.raises(ValueError):
        size3.inner_product_with(size3)

def test_even_dimension():
    size2 = SP3([1,2])
    assert np.array_equal(size2.Lambda, [[0,2],[1,0]])
    


def test_inner_product():
    u = SP3([1,0,0,0])
    result = u | [0,0,1,0]

    neg1 = SP3([-1])

    assert result == neg1.item()

    with pytest.raises(ValueError):
        u | [1,2,3,4,5,6]

    assert SP5([2, 1, 0, 3, 4, 1]).is_symplectic_pair_with(SP5([3, 0, 1, 3, 0, 2]))

def test_symplectic_pairs():
    u = SP3([1,0,0,0])
    v = SP3([0,0,1,0])
    assert SP3.is_symplectic_pair(u, v)

def test_symplectic_matrix():
    assert SP5.LambdaN(5).is_symplectic_matrix()
    assert SP5([[4, 2, 0, 0, 0, 3],
                [2, 4, 1, 0, 4, 1],
                [2, 0, 0, 2, 1, 2],
                [1, 4, 0, 3, 2, 2],
                [2, 2, 3, 1, 0, 0],
                [3, 0, 3, 4, 4, 4]],
                ).is_symplectic_matrix()

def test_embedding():
    assert SP5([[4, 2, 0, 0, 0, 3],
                [2, 4, 1, 0, 4, 1],
                [2, 0, 0, 2, 1, 2],
                [1, 4, 0, 3, 2, 2],
                [2, 2, 3, 1, 0, 0],
                [3, 0, 3, 4, 4, 4]],
                ).embed_symplectic().is_symplectic_matrix()
    
    t = SP13.random_array((6,6))
    embed = t.embed_symplectic()

    assert embed.n==4
    assert embed.d==13
    assert embed.nn==8

def test_transvection():
    u = SP3([1,0,0,0])
    v = SP3([1,2,3,4])

    T = SP3.Transvection(v, c=5)
    result = T(u)
    
    assert isinstance(result, SP3)

def test_transvection_finding():
    u = SP5([1,2,3,4])
    v = SP5([2,3,4,5])

    t1, t2 = SP3.Transvection.find_transvection(u, v)
    assert np.array_equal(t2(t1(u)), v)




def test_random_symplectic():
    for i in range(50):
        for n in [1,2,3,4]:
            assert SP5.random_symplectic(n).is_symplectic_matrix()

def test_index_symplectic():
    assert SP3.from_index(100000, n=3).is_symplectic_matrix()

    assert np.array_equal(
        SP5.from_index(100000, n=3),
        SP5([[2, 0, 3, 4, 3, 0],
             [1, 1, 4, 1, 0, 0],
             [0, 0, 1, 0, 0, 0],
             [0, 0, 1, 3, 2, 0],
             [0, 0, 0, 0, 1, 0],
             [2, 0, 3, 0, 3, 1]]),
    )
    
