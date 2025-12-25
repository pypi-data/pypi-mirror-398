from funfedi_parsing_test_cases.types import Environment
from .activity import ActivityTestCase, ActivityTestCaseMaker


def test_to_send():
    env = Environment(
        sending_actor_profile={"id": "http://host.test/some/actor"},
        receiving_actor="http://other.test/some/actor",
    )

    maker = ActivityTestCaseMaker()

    result = maker.to_send(environment=env)

    assert isinstance(result, ActivityTestCase)
