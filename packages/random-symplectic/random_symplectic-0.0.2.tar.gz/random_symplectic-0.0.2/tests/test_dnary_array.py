import numpy as np
from randomsymplectic import DnaryArray


D5 = DnaryArray.set_d(5)
D3 = DnaryArray.set_d(3)

def test_invertible():
    assert D3.eye(2).is_invertible()
    assert not D3.zeros((2,2)).is_invertible()

def test_random_inverse():
    for _ in range(10):
        t=D3.random_array((12,12))
        s=D5.random_array((16,16))
        t_inv = t.mod_matrix_inv()
        s_inv = s.inv()
        if t_inv is not None:
            assert np.array_equal(t @ t_inv, D3.eye(12))
        if s_inv is not None:
            assert np.array_equal(s @ s_inv, D5.eye(16))


def test_composite_dnary():
    class D4(DnaryArray):_d=4
    D4([1,2,3,4])
    D4_two = DnaryArray.set_d(4)
    D4_two([1,2,3,4])

def test_dnary_logic():
    one = D3([1])
    two = D3([2])
    five = D3([5])

    assert (one + two).item()==0
    assert five.item()==two.item()
    assert (two+five).item()==one.item()

def test_standard_basis():
    u = D5([1,0,0,0])
    v = D5.basis_vector(0,4)
    assert np.array_equal(u,v)