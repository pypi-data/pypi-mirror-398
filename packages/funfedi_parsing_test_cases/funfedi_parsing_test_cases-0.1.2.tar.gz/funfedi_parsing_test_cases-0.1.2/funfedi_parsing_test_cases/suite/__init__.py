from dataclasses import dataclass
from funfedi_parsing_test_cases.types import Case

from .validators import validate

__all__ = ["Suite"]


@dataclass
class SubSuite:
    title: str
    short_name: str
    tests: list[Case]


class Suite:
    tests: dict[str, list[Case]]
    test_map: dict[str, dict[str, Case]]
    titles: dict[str, str]
    sub_suites: list[SubSuite]

    def __init__(self, tests: list[SubSuite]):
        self.sub_suites = tests
        self.tests = {
            sub_suite.short_name: [validate(x) for x in sub_suite.tests]
            for sub_suite in tests
        }
        self.titles = {sub_suite.short_name: sub_suite.title for sub_suite in tests}
        self.test_map = {
            name: {test_case.name: test_case for test_case in cases}
            for name, cases in self.tests.items()
        }

    def retrieve(self, name, test_name) -> Case:
        return self.test_map[name][test_name]

    @property
    def names(self):
        name_map = [
            [(name, case.name) for case in cases] for name, cases in self.tests.items()
        ]

        return sum(name_map, [])
