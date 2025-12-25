from spArgValidatorPy import ArgValidator

import pytest

av = ArgValidator()
value = None


# ++++++++++++++++++++++++++++++++++++++++++
#   functions with validation
# ++++++++++++++++++++++++++++++++++++++++++

def func_with_mandatory_arg(a, b):
    a = av.get_validated_str("a")
    b = av.get_validated_str("b")
    return a


def func_with_str(a):
    a = av.get_validated_str("a")
    return a

def func_with_str_default(a):
    a = av.get_validated_str("a", strict=True, default="Default String")
    return a

def func_with_str_len_10(a):
    a = av.get_validated_str("a", 10)
    return a

def func_with_str_strict(a):
    a = av.get_validated_str("a", strict=True)
    return a

def func_with_int(a):
    a = av.get_validated_int("a")
    return a

def func_with_int_default(a):
    a = av.get_validated_int("a", default=77000)
    return a

def func_with_int_strict(a):
    a = av.get_validated_int("a", strict=True)
    return a

def func_with_int_limited(a):
    a = av.get_validated_int("a", 6, 10)
    return a

def func_with_int_limited_and_return_limit(a):
    a = av.get_validated_int("a", 6, 10, return_limits=True)
    return a

def func_with_float(a):
    a = av.get_validated_float("a")
    return a

def func_with_float_default(a):
    a = av.get_validated_float("a", default=999.999)
    return a

def func_with_float_strict(a):
    a = av.get_validated_float("a", strict=True)
    return a

def func_with_float_limited(a):
    a = av.get_validated_float("a", 200.0, 202.0)
    return a

def func_with_float_limited_and_return_limit(a):
    a = av.get_validated_float("a", 200.0, 202.0, return_limits=True)
    return a


# ++++++++++++++++++++++++++++++++++++++++++


def test_01():
    with pytest.raises(Exception):
        func_with_mandatory_arg("only_a_supplied")

def test_02():
    value = "MyString"
    assert func_with_str(value) == value

def test_03():
    value = "MyString with length greater than 10 characters"
    assert func_with_str_len_10(value) == value

def test_04():
    with pytest.raises(ValueError):
        value = "MyString"
        func_with_str_len_10(value)

def test_05():
    assert func_with_str(256) == '256'

def test_06():
    with pytest.raises(TypeError):
        func_with_str_strict(256)

def test_07():
    assert func_with_str_default(256) == 'Default String'

def test_08():
    assert func_with_int(15) == 15

def test_09():
    with pytest.raises(ValueError):
        func_with_int_limited(15)

def test_10():
    assert func_with_int_limited_and_return_limit(15) == 10

def test_11():
    assert func_with_int('15') == 15

def test_12():
    with pytest.raises(TypeError):
        func_with_int_strict("15")

def test_13():
    with pytest.raises(TypeError):
        func_with_int("not_15")

def test_14():
    assert func_with_int_default("not_15") == 77000

def test_15():
    assert func_with_float(12.777) == 12.777

def test_16():
    with pytest.raises(ValueError):
        func_with_float_limited(12.777)

def test_17():
    assert func_with_float_limited_and_return_limit(415) == 202.0

def test_18():
    assert func_with_float('15.9') == 15.9

def test_19():
    with pytest.raises(TypeError):
        func_with_float_strict("15.9")

def test_20():
    with pytest.raises(TypeError):
        func_with_float("not_15.9")

def test_21():
    assert func_with_float_default('not_15.9') == 999.999



