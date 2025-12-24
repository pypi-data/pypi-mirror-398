## Version 1.0.0

This release is the moving of the pytest hooks and test suits to this project from Centurion ERP.


### Breaking changes

- `centurion.tests.unit_class.ClassTestCases` split into two seperate test suites:

    - `pytest_simplified.suites.attributes.ClassAttributesTestCases` contains the class attributes test cases.

    - `pytest_simplified.suites.functions.ClassFunctionsTestCases` contains the class function test cases.

- `django.db import models.NOT_PROVIDED` replaced with `pytest_simplified.NOT_USED`.

- moved hook `pytest_pycollect_makeitem` to this module.
