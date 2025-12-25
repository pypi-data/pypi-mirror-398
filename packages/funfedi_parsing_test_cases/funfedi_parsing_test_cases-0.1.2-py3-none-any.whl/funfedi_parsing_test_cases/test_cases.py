import pytest


from .cases import ActivityTestCase
from . import activity_suite
from .testing import *  # noqa


@pytest.mark.parametrize("name,case_name", activity_suite.names)
def test_activity_suite(test_env, name, case_name):
    case = activity_suite.retrieve(name, case_name)
    result = case.maker.to_send(test_env)
    assert isinstance(result, ActivityTestCase)
