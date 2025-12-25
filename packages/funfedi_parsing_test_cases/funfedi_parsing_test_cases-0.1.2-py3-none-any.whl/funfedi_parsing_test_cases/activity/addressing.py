from collections.abc import Callable

from funfedi_parsing_test_cases.suite import SubSuite
from funfedi_parsing_test_cases.cases.activity import default_activity_maker
from funfedi_parsing_test_cases.types import Environment, Case
from funfedi_parsing_test_cases.cases import ActivityTestCaseMaker


public_value = "https://www.w3.org/ns/activitystreams#Public"


def both(environment: Environment):
    return [environment.receiving_actor, public_value]


def maker_for_main_a(main: str, a):
    def maker(environment: Environment):
        return {main: a(environment)}

    return maker


def maker_for_ab_main_other(main: str, other: str, a, b):
    def maker(environment: Environment):
        return {main: a(environment), other: b}

    return maker


def make_example_makers() -> list[Callable[[Environment], dict]]:
    example_makers = []

    for main, other in [("to", "cc"), ("cc", "to")]:
        example_makers += [
            maker_for_main_a(main, both),
            maker_for_ab_main_other(main, other, both, None),
            maker_for_ab_main_other(main, other, both, []),
        ]
        example_makers += [
            maker_for_ab_main_other(main, other, a, b)
            for a in [lambda e: e.receiving_actor, lambda e: [e.receiving_actor]]
            for b in [public_value, [public_value]]
        ]

    return example_makers


def make_modifier(example_maker: Callable[[Environment], dict]):
    def modified(environment: Environment, obj: dict):
        data = default_activity_maker(environment, obj)
        del data["to"]
        del data["cc"]
        return {**example_maker(environment), **data}

    return modified


cases = [
    Case(
        name=f"Varying addressing {idx}",
        maker=ActivityTestCaseMaker(activity_maker=make_modifier(maker)),
    )
    for idx, maker in enumerate(make_example_makers())
]

addressing_suite = SubSuite("Variations of to and cc", "create_to_cc", tests=cases)
