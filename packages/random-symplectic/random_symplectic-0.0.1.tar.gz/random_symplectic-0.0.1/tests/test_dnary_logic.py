from randomsymplectic.dnary_arithmetic import dnary_inverse, dnary_to_int, int_to_dnary

def test_dnary_inverse():
    inv = dnary_inverse(5, d=3)
    assert (inv*5)%3==1

def test_dnary_notinvertible():
    assert dnary_inverse(0, d=3) is None
    assert dnary_inverse(2, d=4) is None