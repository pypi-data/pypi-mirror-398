import json
from .addressing import make_example_makers

from funfedi_parsing_test_cases.testing import *  # noqa


def test_all_different(test_env):
    makers = make_example_makers()
    result = [x(test_env) for x in makers]
    result_dumped = [json.dumps(x, sort_keys=True) for x in result]

    for x in sorted(result_dumped):
        print(x)

    assert len(result_dumped) == len(set(result_dumped))
