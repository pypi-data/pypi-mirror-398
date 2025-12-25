from unittest.mock import MagicMock
from funfedi_parsing_test_cases.types import Case
from . import SubSuite, Suite


def test_suite():
    fake_maker = MagicMock()
    fake_maker.to_send.return_value = MagicMock(activity={})
    sub_suite = SubSuite(title="one", short_name="one", tests=[Case("one", fake_maker)])

    suite = Suite([sub_suite])

    assert suite.names == [("one", "one")]
    assert isinstance(suite.retrieve("one", "one"), Case)
