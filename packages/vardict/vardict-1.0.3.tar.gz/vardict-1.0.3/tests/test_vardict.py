import pytest

if __name__ == "__main__":  # to make the tests run without the pytest cli
    import os, sys  # three lines to use the local package and chdir
    os.chdir(os.path.dirname(__file__))
    sys.path.insert(0, os.path.dirname(__file__) + "/../")

import vardict

def test_normal():
    one = 1
    two = 2
    numbers12 = {"one": 1, "two": 2}
    numbers3 = {"three": 3}

    assert vardict(one) == {"one": 1}
    assert vardict(one, two, three=3) == {"one": 1, "two": 2, "three": 3}
    assert vardict(numbers12, three=3) == {"numbers12": {"one": 1, "two": 2}, "three": 3}
    assert vardict(numbers12, numbers3) == {"numbers12": {"one": 1, "two": 2}, "numbers3": {"three": 3}}
    assert vardict(three=3) == {"three": 3}

def test_errors():
    one = 1
    two = 2

    with pytest.raises(NameError):
        vardict(four, two, three=3)
    with pytest.raises(ValueError):
        vardict(one+two, three=3)
    with pytest.raises(ValueError):
        vardict("1", three=3)
    with pytest.raises(ValueError):
        vardict(one, two, one=1, three=3)


if __name__ == "__main__":
    pytest.main(["-vv", "-s", "-x", __file__])
