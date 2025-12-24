---
title: pytest-simplified
description: A PyTest plugin to simplify testing classes.
date: 2025-12-21
template: project.html
about: https://github.com/nofusscomputing/pytest_simplified
---

PyTest-Simplified is intended to serve as a base test suite(s) that contains the commmon test cases that are/would be used for testing python classes. This plugin has been written so that the common test cases for classes can be run by simply defining a dictionary.


## Features

- Attribute Test Suite

- Function Test Suite

- Parameterized Test Suite Creation


## Writing Tests

As this plugins name suggests, when writing tests they are to be class based. As part of the pytest test suite convention, classes must be suffixed with `Test` for the tests to be generated. With Pytest-Simplified, this is not the case as tests **must** be suffixed with `PyTest` innstead of `Test`. This is by design and tells this plugin, that the test suite requires processing.

!!! info
    If any of your test suites inherit from `unittest.TestCase` pytest-simplified will ignore the class and those test cases wont be generated.

Test suites within this plugin require that within your test classes, attribute `parameterized_class_attributes` is defined. It is intended that when you write your class based tests, the test suites would be defined in the same pattern that your test classes are. That is if you have `class_one` that inherits `base`, your test suites would be `class_one_test` that inherits from `base_test`. 


### Attribute Test Suite

Test suite `pytest_simplified.suites.ClassesTestCases` contains the following tests:

- `test_class_attribute_exists`

    Confirms that the defined attribute exists within the class being tested.

- `test_class_attribute_type`

    Confirms that the defined attribute is of the defined python type.

- `test_class_attribute_value`

    Confirms that the defined attribute is the specified value.

Dictionary `parameterized_class_attributes` must be defined as follows.

``` py

'_audit_enabled': {    # Attribute name
    'type': bool,      # Type the attribute should return
    'value': True,     # Value the attribute should return
}

```


## Functions Test Suite

Test suite `pytest_simplified.suites.ClassFunctionsTestCases` contains the following tests:

- `test_class_function_arg_names`

    Confirms that the defined function has the specified arguments.

``` py

'_audit_enabled': {                      # Functions name
    'function': True,                    # is the attribute a function. Note: Value is not relevant to this suite.
    'arg_names': [ 'val_1', 'val_2' ]    # List of the arg names.
}

```


## Fixtures

The following test fixtures are required to be defined for each test suite:

- `pytest_simplified.suites.ClassesTestCases.test_class`

    - `test_class` that class being tested. this should be scoped `class`

- `pytest_simplified.suites.ClassFunctionsTestCases.test_class`

    - `test_class` that class being tested. this should be scoped `class`


## Parameterizing Tests

To be able to paramertize any test case, the test must be setup to use PyTest. Within the test class the test data is required to be stored in a dictionary prefixed with string `paramaterized_<data_name>`. Variable `<data_name>` is the data key that you will specify within the test method.

Our test setup allows for class inheritance which means you can within each class of the inheritance chain, add the `paramaterized_<data_name>` attribute. If you do this, starting from the lowest base class, each class that specifies the `paramaterized_<data_name>` attribute will be merged. The merge is an overwrite of the classes previous base class, meaning that the classes higher in the chain will overwrite the value of the lower class in the inheritance chain. You can not however remove a key from attribute `paramaterized_<data_name>`.

The test method must be called with parameters:

- 'parameterized'

    Tells the test generator that this test case is a parameterized test.

- `param_key_<data_name>`

    Tells the test setup the suffix to use to find the test data. The value of variable `data_name` can be any value you wish as long as it only contains chars `a-z` and/or `_` (underscore). This value is also used in class parameter `paramaterized_<data_name>`.

- `param_<name>`

    Tells the test setup that this is data to be passed from the test. When test generation is run, these attributes will contain the test data. It's of paramount importance, that the dict You can have as many of these attributes you wish, as long as `<name>` is unique and `<name>` is always prefixed with `param_`. If you specify more than to parameters with the `param_` prefix, the value after the `param_` prefix, must match the dictionary key for the data you wish to be assigned to that parameter. what ever name you give the first `param_` key, will always receive the key name from the `parameterized_test_data` attribute in the test class.

    The value of `<name>` for each and in the order specified is suffixed to the test case name

``` py

class MyTestClassTestCases:


    parameterized_test_data: dict = {
        'key_1': {
            'expected': 'key_1'
        },
        'key_2': {
            'random': 'key_2'
        },
    }


class MyTestClassPyTest(
    MyTestClassTestCases
):

    parameterized_test_data: dict = {
        'key_2': {
            'random': 'value'
        }
        'key_3': {
            'expected': 'key_3',
            'is_type': bool
        }
    }


    parameterized_second_dict: dict = {
        'key_1': {
            'expected': 'key_1'
        },
    }

    def test_my_test_case_one(self, parameterized, param_key_test_data, param_value, param_expected):

        assert param_value == param_expected


    def test_my_test_case_two(self, parameterized, param_key_test_data, param_value, param_random):

        assert param_value == param_random


    def test_my_test_case_three(self, parameterized, param_key_test_data, param_value, param_is_type):

        my_test_dict = self.adict

        assert type(my_test_dict[param_value]) is param_is_type


    def test_my_test_case_four(self, parameterized, param_key_second_dict, param_arbitrary_name, param_expected):

        my_test_dict = self.a_dict_that_is_defined_in_the_test_class

        assert my_test_dict[param_arbitrary_name] == param_expected

```

In this example:

- The test class in this case is `MyTestClassPyTest` which inherits from `MyTestClassTestCases`. there are two parameterized variables: `test_data` and `second_dict`. Although, the concrete class attribute `parameterized_test_data` overrides the base classes variable of the same name, the test setup logic does merge `MyTestClassPyTest.parameterized_test_data` with `MyTestClassTestCases.parameterized_test_data`. So in this case the value dictionary `MyTestClassPyTest.parameterized_test_data[key_2][random]`, `value` will overwrite dictionary of the same name in the base class. In the same token, as dictionary `MyTestClassTestCases.parameterized_test_data[key_3]` does not exist, it will be added to the dictionary during merge so it exists in `MyTestClassPyTest.parameterized_test_data`

- test suite `MyTestClassPyTest` will create a total of five parmeterized test cases for the following reasons:

    - `test_my_test_case_one` will create two parameterized test cases.

        - will use data in attribute `test_data` prefixed with `parameterized_` as this is the attribute prefixed with `param_key_`.

        - `MyTestClassPyTest.parameterized_test_data['key_1']` is a dictionary, which contains key `expected` which is also one of the attributes specified with prefix `param_`

        - `MyTestClassPyTest.parameterized_test_data['key_3']` is a dictionary, which contains key `expected` which is also one of the attributes specified with prefix `param_`

    - `test_my_test_case_two` will create one parameterized test case.

        - will use data in attribute `test_data` prefixed with `parameterized_` as this is the attribute prefixed with `param_key_`.

        - `MyTestClassPyTest.parameterized_test_data['key_2']` is a dictionary, which contains key `random` which is also one of the attributes specified with prefix `param_`

    - `test_my_test_case_three` will create one parameterized test case.

        - will use data in attribute `test_data` prefixed with `parameterized_` as this is the attribute prefixed with `param_key_`.

        - `MyTestClassPyTest.parameterized_test_data['key_3']` is a dictionary, which contains key `is_type` which is also one of the attributes specified with prefix `param_`

    - `test_my_test_case_four` will create one parameterized test case.

        - will use data in attribute `second_dict` prefixed with `parameterized_` as this is the attribute prefixed with `param_key_`.

        - `MyTestClassPyTest.parameterized_second_dict['key_1']` is a dictionary, which contains key `expected` which is also one of the attributes specified with prefix `param_`
