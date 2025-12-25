from .. import boundValue

def test_bounding_over_bound():
    # bound = 0.0001, rounding = ROUND_HALF_EVEN
    assert boundValue(value = 1.23456) == 1.2346

def test_bounding_under_bound():
    assert boundValue(value = 1.23) == 1.23