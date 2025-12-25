import pytest

from .types import Environment

default_env = Environment(
    sending_actor_profile={
        "type": "Person",
        "id": "http://host.test/some/actor",
        "summary": "this is a stub",
    },
    receiving_actor="http://other.test/some/actor",
)


@pytest.fixture
def test_env():
    return default_env
