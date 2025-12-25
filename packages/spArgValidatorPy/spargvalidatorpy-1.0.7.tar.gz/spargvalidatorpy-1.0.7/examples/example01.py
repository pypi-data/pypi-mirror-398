#   example01.py
#
#   file to demonstrate the use of spArgValidatorPy
#
#
import sys

from spArgValidatorPy import ArgValidator

print("running Python executable from path", sys.executable)

av = ArgValidator()

# helper functions
r_number = 0
value = None
def set_value_and_explanation(new_value, explanation):
    global r_number
    global value

    value = new_value
    if isinstance(new_value, str):
        value_text = "'" + new_value + "'"
    else:
        value_text = str(new_value)
    r_number += 1
    print("Number", r_number, ":", explanation + ", using value", value_text)


def print_result(name, result):
    if isinstance(result, str):
        vRes = "'" + result + "'"
    else:
        vRes = str(result)
    print("  ->", name, "has type", type(result), "with a value of", vRes)


# an class to demonstrate object methods
class ExampleObj():
    def fail(self, a):
        a = av.get_validated_int("a")
        print_result("a", a)



# ++++++++++++++++++++++++++++++++++++++++++
#   functions with validation
# ++++++++++++++++++++++++++++++++++++++++++

def func_with_mandatory_arg(a, b):
    a = av.get_validated_str("a")
    b = av.get_validated_str("b")
    print_result("a", a)


def func_with_str(a):
    a = av.get_validated_str("a")
    print_result("a", a)

def func_with_str_default(a):
    a = av.get_validated_str("a", strict=True, default="Default String")
    print_result("a", a)

def func_with_str_len_10(a):
    a = av.get_validated_str("a", 10)
    print_result("a", a)

def func_with_str_strict(a):
    a = av.get_validated_str("a", strict=True)
    print_result("a", a)

def func_with_int(a):
    a = av.get_validated_int("a")
    print_result("a", a)

def func_with_int_default(a):
    a = av.get_validated_int("a", default=77000)
    print_result("a", a)

def func_with_int_strict(a):
    a = av.get_validated_int("a", strict=True)
    print_result("a", a)

def func_with_int_limited(a):
    a = av.get_validated_int("a", 6, 10)
    print_result("a", a)

def func_with_int_limited_and_return_limit(a):
    a = av.get_validated_int("a", 6, 10, return_limits=True)
    print_result("a", a)

def func_with_float(a):
    a = av.get_validated_float("a")
    print_result("a", a)

def func_with_float_default(a):
    a = av.get_validated_float("a", default=999.999)
    print_result("a", a)

def func_with_float_strict(a):
    a = av.get_validated_float("a", strict=True)
    print_result("a", a)

def func_with_float_limited(a):
    a = av.get_validated_float("a", 200.0, 202.0)
    print_result("a", a)

def func_with_float_limited_and_return_limit(a):
    a = av.get_validated_float("a", 200.0, 202.0, return_limits=True)
    print_result("a", a)


# ++++++++++++++++++++++++++++++++++++++++++


# ------------------------------------------
set_value_and_explanation("only_a_supplied", "mandatory argument missing")
try:
    func_with_mandatory_arg(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation("MyString", "regular string")
func_with_str(value)

# ------------------------------------------
set_value_and_explanation("MyString with length greater than 10 characters", "regular string with minimum length of 10 required")
func_with_str_len_10(value)

# ------------------------------------------
set_value_and_explanation("MyString", "regular string with minimum length of 10 required failing")
try:
    func_with_str_len_10(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation(256, "string from int")
func_with_str(value)

# ------------------------------------------
set_value_and_explanation(256, "string from int failing in strict mode")
try:
    func_with_str_strict(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation(256, "string from int failing in strict mode with default value returned")
func_with_str_default(value)



# ------------------------------------------
set_value_and_explanation(15, "regular integer")
func_with_int(value)

# ------------------------------------------
set_value_and_explanation(15, "regular integer exceeding limit")
try:
    func_with_int_limited(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation(15, "regular integer limited by max_value and return_limits=True")
func_with_int_limited_and_return_limit(value)

# ------------------------------------------
set_value_and_explanation("15", "integer string representation")
func_with_int(value)

# ------------------------------------------
set_value_and_explanation("15", "integer string representation failing in strict mode")
try:
    func_with_int_strict(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation("not_15", "integer string representation failing")
try:
    func_with_int(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation("not_15", "integer failing with default returned")
func_with_int_default(value)



# ------------------------------------------
set_value_and_explanation(12.777, "regular float")
func_with_float(value)

# ------------------------------------------
set_value_and_explanation(12.777, "regular float exceeding limit")
try:
    func_with_float_limited(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation(415, "regular float limited by max_value and return_limits=True")
func_with_float_limited_and_return_limit(value)

# ------------------------------------------
set_value_and_explanation("15.9", "float string representation")
func_with_float(value)

# ------------------------------------------
set_value_and_explanation("15.9", "float string representation failing in strict mode")
try:
    func_with_float_strict(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation("not_15.9", "float string representation failing")
try:
    func_with_float(value)
except Exception as e:
    print("  -> Error:", str(e))

# ------------------------------------------
set_value_and_explanation("not_15.9", "float failing with default returned")
func_with_float_default(value)



obj = ExampleObj()
# ------------------------------------------
set_value_and_explanation(678, "integer in object method")
obj.fail(value)

# ------------------------------------------
set_value_and_explanation("20888", "integer string representation in object method")
obj.fail(value)

# ------------------------------------------
set_value_and_explanation("not an int", "integer in object method failing")
try:
    obj.fail(value)
except Exception as e:
    print("  -> Error:", str(e))




