import inspect
import pytest
import unittest



def pytest_generate_tests(metafunc):

    arg_values:list = None

    fixture_parameters: list = []

    parameterized_test = False

    parameterized_key: str = None


    def get_type_name(value) -> str:

        type_name = None

        if(
            inspect.isclass(value)
            or (
                hasattr(value, "__class__")
                and type(value) not in [ bool, dict, int, str, type(None) ]
            )
        ):

            if isinstance(value, list) and value:

                type_name: str = [ get_type_name(item) for item in value ]

            else:

                type_name: str = str(getattr(value, '__name__', value.__class__.__name__)).lower()


        elif callable(value):

            type_name: str = str(value.__name__).lower()

        else:

            type_name: str = str(value).lower()


        if isinstance(type_name, str):

            type_name = type_name.replace(', ', '_')    # lists
            type_name = type_name.replace("'", '')      # lists
            type_name = type_name.replace('"', '')      # lists
            type_name = type_name.replace(' ', '_')     # lists | str


        return type_name



    if {'parameterized'} <= set(metafunc.fixturenames):

        for mark in metafunc.definition.own_markers:    # Skip tests markd to skip

            if mark.name == 'skip':
                return None

        for mark in getattr(metafunc.cls, 'pytestmark', []):    # Skip test suite markd to skip

            if mark.name == 'skip':
                return None

        all_fixture_parameters = metafunc.fixturenames

        fixture_parameters += ['parameterized']

        for i in range(0, len(metafunc.fixturenames)):

            if (
                str(all_fixture_parameters[i]).startswith('param_')
                and not str(all_fixture_parameters[i]).startswith('param_key_')
            ):

                fixture_parameters += [ all_fixture_parameters[i] ]


            elif str(all_fixture_parameters[i]).startswith('param_key_'):

                parameterized_key = str( all_fixture_parameters[i] ).replace('param_key_', '')

                if len(fixture_parameters) == 1:

                    fixture_parameters += [ all_fixture_parameters[i] ]

                else:

                    fixture_parameters[1] = all_fixture_parameters[i]


        parameterized_test = len(fixture_parameters) > 0


    if parameterized_test:

        values = {}


        cls = getattr(metafunc, "cls", None)

        if cls:

            for base in reversed(cls.__mro__):

                base_values = getattr(base, 'parameterized_' + parameterized_key, None)

                if isinstance(base_values, property):

                    base_values = getattr(base(), 'parameterized_' + parameterized_key, None)

                if not isinstance(base_values, dict):

                    continue

                if len(values) == 0 and len(base_values) > 0:

                    values.update(base_values)

                    continue

                for key, value in values.items():

                    if(
                        type(value) is not dict
                        or key not in base_values
                    ):

                        continue

                    if key not in values:

                        values.update({
                            key: base_values[key]
                        })

                    else:

                        values[key].update( base_values[key] )


                for key, value in base_values.items():

                    if key not in values:

                        values.update({
                            key: base_values[key]
                        })


        if values:

            ids = []

            arg_values:list = []

            for item in values.items():

                ids_name = item[0]

                item_values:tuple = ()

                length = len(item)

                is_key_value: bool = True

                if type(item[1]) is not dict:

                    continue


                item_values += ( None, None, item[0])

                for key in fixture_parameters:

                    if key in [ fixture_parameters[0], fixture_parameters[1], fixture_parameters[2], ]:
                        # these values are already defined in `item_values`
                        # fixture_parameters[0] = parameterized.
                        # fixture_parameters[1] = param_key
                        # fixture_parameters[2] = the dict name

                        continue

                    if(
                        str(key).startswith('param_')
                        and not str(key).startswith('param_key_')
                    ):

                        key = str(key).replace('param_', '')

                        if (
                            type(item[1]) is not dict
                            or item[1].get(key, 'key-does_not-exist') == 'key-does_not-exist'
                        ):

                            item_values = ()

                            continue


                        if key in item[1]:

                            item_values += ( item[1][key], )
                            value = get_type_name(
                                value = item[1][key]
                            )

                            ids_name += f'_{value}'


                if(
                    len(item_values) > 0
                    and len(fixture_parameters) == len(item_values)
                ):

                    arg_values += [ item_values ]

                    ids += [ ids_name, ]


            if len(arg_values) > 0:

                # Get the test method
                test_func = getattr(metafunc.cls, metafunc.definition.name, None)

                # Remove previous xfail mark if present
                if test_func and hasattr(test_func, 'pytestmark'):
                    test_func.pytestmark = [
                        mark for mark in test_func.pytestmark if mark.name != 'xfail'
                    ]

                metafunc.parametrize(
                    argnames = [
                        *fixture_parameters
                    ],
                    argvalues = arg_values,
                    ids = ids,
                )

            else:

                pytest.mark.xfail(
                    reason = 'No Parameters for parameterized test'
                )(
                    getattr(metafunc.cls, metafunc.definition.name)
                )


        else:

            pytest.mark.xfail(
                reason = 'No Parameters for parameterized test'
            )(
                getattr(metafunc.cls, metafunc.definition.name)
            )



def pytest_pycollect_makeitem(collector, name, obj):
    """PyTest Test Creation

    Create PyTest Test Classes if the classname ends in `PyTest`
    and is not inheriting from django,test.TestCase.
    """

    if (
        isinstance(obj, type)
        and name.endswith("PyTest")
        and not issubclass(obj, unittest.TestCase)    # Don't pickup any django unittest.TestCase
    ):
        return pytest.Class.from_parent(parent=collector, name=name)
