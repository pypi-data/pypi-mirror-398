from dataclasses import dataclass, field
from enum import StrEnum, auto
import secrets
from typing import Any
from urllib.parse import urljoin


@dataclass
class Environment:
    sending_actor_profile: dict
    receiving_actor: str

    @property
    def sending_actor(self):
        result = self.sending_actor_profile.get("id")
        if not isinstance(result, str):
            raise Exception("the sending_actor_profile needs to have an id")
        return result

    def id_maker(self, prefix="objects"):
        return urljoin(self.sending_actor, f"/{prefix}/{secrets.token_urlsafe(12)}")


class TestCaseStatus(StrEnum):
    recommended = auto()
    unknown = auto()
    may_fail = auto()
    should_fail = auto()


@dataclass
class Case:
    name: str
    maker: Any
    status: TestCaseStatus = TestCaseStatus.unknown
    comments: list[str] = field(default_factory=list)
