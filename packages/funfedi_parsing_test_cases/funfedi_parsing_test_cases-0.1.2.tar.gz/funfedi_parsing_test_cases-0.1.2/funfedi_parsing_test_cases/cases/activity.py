from collections.abc import Callable
from dataclasses import dataclass

from funfedi_parsing_test_cases.types import Environment

from bovine.utils import now_isoformat


class InvalidTestCaseException(Exception): ...


def default_object_maker(environment: Environment) -> dict:
    return {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
        ],
        "attributedTo": environment.sending_actor,
        "content": "text",
        "id": environment.id_maker(),
        "published": now_isoformat(),
        "to": [
            "https://www.w3.org/ns/activitystreams#Public",
            environment.receiving_actor,
        ],
        "cc": [],
        "tag": [{"type": "Mention", "href": environment.receiving_actor}],
        "type": "Note",
    }


def default_activity_maker(environment: Environment, obj: dict) -> dict:
    return {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
        ],
        "actor": environment.sending_actor,
        "id": environment.id_maker("activities"),
        "object": obj,
        "published": now_isoformat(),
        "to": [
            "https://www.w3.org/ns/activitystreams#Public",
            environment.receiving_actor,
        ],
        "cc": [],
        "type": "Create",
    }


@dataclass
class ActivityTestCase:
    activity: dict
    object_id: str


@dataclass
class ActivityTestCaseMaker:
    object_maker: Callable[[Environment], dict] = default_object_maker
    activity_maker: Callable[[Environment, dict], dict] = default_activity_maker

    def activity_and_object(self, environment: Environment) -> tuple[dict, dict]:
        obj = self.object_maker(environment)
        activity = self.activity_maker(environment, obj)
        return activity, obj

    def to_send(self, environment: Environment) -> ActivityTestCase:
        #
        # Might want to return object_id instead of activity, as it is what is used
        # to lookup later
        #
        # Also activity might be a lie as one might have an activity in an activity
        #
        activity, obj = self.activity_and_object(environment)

        object_id = obj.get("id")
        if not isinstance(object_id, str):
            raise InvalidTestCaseException(
                "Only test cases where the object has an id are supported"
            )

        return ActivityTestCase(activity, object_id)
