import pytest

from randomsymplectic import DnaryArray


def test_needs_d_for_instantiation():
    with pytest.raises(TypeError):
        t = DnaryArray([0])

def test_needs_d_for_access():
    with pytest.raises(TypeError):
        DnaryArray.d

def test_can_create_child():
    class Child(DnaryArray):
        ...

def test_child_needs_d():
    class Child(DnaryArray):
        ...
    with pytest.raises(TypeError):
        Child([0])

def test_second_child_needs_d():
    class Child(DnaryArray):
        ...
    class Child2(Child):
        ...
    with pytest.raises(TypeError):
        Child2([0])

def test_cannot_reassign_classvar():
    class Child(DnaryArray):
        _d=5
    with pytest.raises(AttributeError):
        Child.d=10

def test_cannot_reassign_instance_var():
    class Child(DnaryArray):
        _d=5
    t=Child([0])
    with pytest.raises(AttributeError):
        t.d=10
    
def test_dnary_identical_instances():
    D3 = DnaryArray.set_d(3)
    other_D3 = DnaryArray.set_d(3)
    assert D3 is other_D3

