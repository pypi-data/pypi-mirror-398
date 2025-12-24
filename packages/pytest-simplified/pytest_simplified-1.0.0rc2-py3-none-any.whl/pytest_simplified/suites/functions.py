import inspect

import pytest



class ClassFunctionsTestCases:
    """Class Functions Test Suite

    This test suite contains all of the common tests for testing class
    functions.

    To use this test suite you must define a fixture called `test_class` that
    contains the class to test.

    ## Test Setup

    define a class attribute or property called `parameterized_class_attributes`
    that returns a dict of the following:

    ``` py
    '_audit_enabled': {
        'type': bool,    # TYpe the attribute should return
        'value': True,   # Value the attribute should return
        'function': True,    # is the attribute a function. Note: Value is not relevant to this suite.
        'arg_names': [ 'val_1', 'val_2' ]    # List of the arg names.
    }
    ```

    **Note:** if the field does not exist, for the sub-class use
    `pytest_simplified.NOT_USED` as the value. This in turn will cause the test to xfail.
    """

    @pytest.fixture( scope = 'class')
    def test_class(self):
        raise NotImplemented('You must define the test_class fixture for the tests to function.')



    @property
    def parameterized_class_attributes(self):
        return {}



    @pytest.mark.regression
    def test_class_function_arg_names(self,
        test_class,
        parameterized, param_key_class_attributes, param_field_name,
        param_function, param_arg_names
    ):
        """Test Function

        Ensure a function has the specified arg names
        """
    
        sig = inspect.signature( obj = getattr(test_class, param_field_name) )
        

        assert list(sig.parameters.keys()) == param_arg_names