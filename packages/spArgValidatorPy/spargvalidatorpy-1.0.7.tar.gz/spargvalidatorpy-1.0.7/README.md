# spArgValidatorPy

[![PyPI - Version](https://img.shields.io/pypi/v/spArgValidatorPy.svg)](https://pypi.org/project/spArgValidatorPy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/spArgValidatorPy.svg)](https://pypi.org/project/spArgValidatorPy)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


This package provides a Python module for validating function arguments. Depending on the outcome, it either raises an exception or returns the validated value.

If a numeric argument is provided as a string representation (e.g. "100" or "3.24"), it will be converted and returned as a valid int or float, unless validation is performed in strict mode. Numeric arguments can also be checked against minimum and/or maximum limits.

String arguments are considered valid if they can be converted to a string (e.g. 123 becomes "123"), unless validation is done in strict mode, which only accepts values of type str. By default, empty strings cause an exception, but this can be disabled by allowing a minimum length of 0.

All validation functions support an optional default argument. If provided, this value is returned instead of raising an exception when validation fails. This simplifies code by removing the need for a separate try–except block to set fallback values. The default must be passed as a keyword argument (default=value) and must match the expected type (str, int, or float).

For numeric validations, you can also enable the return_limits=True option to return the defined minimum or maximum value instead of raising an exception.

For more details, see the API reference below and the examples in examples/example01.py, which includes over 20 usage demonstrations.

Enjoy

&emsp;krokoreit  
&emsp;&emsp;&emsp;<img src="https://github.com/krokoreit/spArgValidatorPy/blob/main/assets/krokoreit-01.svg?raw=true" width="140"/>


## Installation

```console
pip install spArgValidatorPy
```


## Usage & API

### ArgValidator Class
Import module and instantiate an ArgValidator object:
```py
  from spArgValidatorPy import ArgValidator

  av = ArgValidator()
```

Argument validation is then as simple as
```py
  def my_function(str_arg, int_arg, float_arg):
      str_arg = av.get_validated_str("str_arg")
      int_arg = av.get_validated_int("int_arg")
      float_arg = av.get_validated_float("float_arg")
      ....
```
Note that the name of the argument is passed to the validation function and not the value.  
After successful validation (no exception raised), these variables can be safely used as str, int and float. For more complex validation with the use of strict mode, minimum or maximum values allowed or defaults, see the validation functions below.


</br>

### API

#### Methods<a id="methods"></a>
* [get_validated_int()](#get_validated_int-method)  
* [get_validated_float()](#get_validated_float-method)  
* [get_validated_str()](#get_validated_str-method)  
</br>
</br>


#### get_validated_int() Method<a id="get_validated_int-method"></a>
```py
  get_validated_int(var_name, min_value, max_value, strict, default=int_value, return_limits=boolean_value)
```
Arguments:
- var_name  
  The name of the argument being validated.
- min_value  
  Optional lower limit to validate var_name's value against.
- max_value  
  Optional upper limit to validate var_name's value against.
- strict  
  Optional boolean argument to allow only integers as var_name's value, when set to True. The default is validation in non-strict mode, which allows string representations of an integer (e.g. "220").
- default=int_value  
  Optional keyword argument for an integer default value. When set, it avoids an exception being raised in case var_name's value fails validation and this default value is returned instead. 
- return_limits=boolean_value  
  Optional keyword argument to avoid an exception being raised for values outside the limits. 
  When set to True and with either min_value or max_value being exceeded, this limit value is returned as validated value.

Returns the validated integer value or with the default or return_limits option used, one of these values instead of an exception raised.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>

</br>

#### get_validated_float() Method<a id="get_validated_float-method"></a>
```py
  get_validated_float(var_name, min_value, max_value, strict, default=float_value, return_limits=boolean_value)
```
Arguments:
- var_name  
  The name of the argument being validated.
- min_value  
  Optional lower limit to validate var_name's value against.
- max_value  
  Optional upper limit to validate var_name's value against.
- strict  
  Optional boolean argument to allow only a float as var_name's value, when set to True. The default is validation in non-strict mode, which allows string representations of a float (e.g. "1.99").
- default=float_value  
  Optional keyword argument for a float default value. When set, it avoids an exception being raised in case var_name's value fails validation and this default value is returned instead. 
- return_limits=boolean_value  
  Optional keyword argument to avoid an exception being raised for values outside the limits. 
  When set to True and with either min_value or max_value being exceeded, this limit value is returned as validated value.

Returns the validated float value or with the default or return_limits option used, one of these values instead of an exception raised.


<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>

</br>

#### get_validated_str() Method<a id="get_validated_str-method"></a>
```py
  get_validated_str(var_name, min_length, strict, default=str_value)
```
- var_name  
  The name of the argument being validated.
- min_length  
  The minimum length required for a valid string. By default thi sis set to 1, meaning that empty strings will throw an exception. This can be set to 0 to allow empty strings or to any other length, against which you want to validate.
- strict  
  Optional boolean argument to allow only a string as var_name's value, when set to True. The default is validation in non-strict mode, which allows any value, which can be converted into a string.
- default=str_value  
  Optional keyword argument for a string default value. When set, it avoids an exception being raised in case var_name's value fails validation and this default value is returned instead. 

Returns the validated string value or with the default option used, this value instead of an exception raised.

<div style="text-align: right"><a href="#methods">&#8679; back up to list of methods</a></div>

</br>

## License
MIT license  
Copyright &copy; 2025 by krokoreit
