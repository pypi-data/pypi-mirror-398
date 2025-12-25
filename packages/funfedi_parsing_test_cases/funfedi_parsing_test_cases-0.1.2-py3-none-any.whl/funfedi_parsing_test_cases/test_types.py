import pytest
from .types import Environment


def test_id_maker():
    env = Environment(
        sending_actor_profile={"id": "http://host.test/some/actor"},
        receiving_actor="http://other.test/some/actor",
    )

    result = env.id_maker()

    assert result.startswith("http://host.test/objects/")


def test_sending_actor():
    actor_id = "http://host.test/some/actor"
    env = Environment(
        sending_actor_profile={"id": actor_id},
        receiving_actor="http://other.test/some/actor",
    )
    assert env.sending_actor == actor_id


def test_sending_actor_failure():
    env = Environment(
        sending_actor_profile={},
        receiving_actor="http://other.test/some/actor",
    )
    with pytest.raises(Exception):
        env.sending_actor
