from funfedi_parsing_test_cases.suite import SubSuite
from funfedi_parsing_test_cases.types import Environment, Case, TestCaseStatus
from funfedi_parsing_test_cases.cases import ActivityTestCaseMaker
from funfedi_parsing_test_cases.cases.activity import default_activity_maker


def without_key(key: str):
    def modified(environment: Environment, obj: dict):
        data = default_activity_maker(environment, obj)
        del data[key]
        return data

    return modified


def with_key_null(key: str):
    def modified(environment: Environment, obj: dict):
        data = default_activity_maker(environment, obj)
        data[key] = None
        return data

    return modified


def with_key_as_list(key: str):
    def modified(environment: Environment, obj: dict):
        data = default_activity_maker(environment, obj)
        data[key] = [data[key]]
        return data

    return modified


def embed_actor(environment: Environment, obj: dict):
    data = default_activity_maker(environment, obj)
    data["actor"] = environment.sending_actor_profile
    return data


recommended_cases = [
    Case(
        name="default", maker=ActivityTestCaseMaker(), status=TestCaseStatus.recommended
    ),
    Case(
        name="without published",
        maker=ActivityTestCaseMaker(activity_maker=without_key("published")),
        status=TestCaseStatus.recommended,
    ),
]


embedded_actor_case = Case(
    name="embedded_actor",
    maker=ActivityTestCaseMaker(activity_maker=embed_actor),
)


key_null_cases = [
    Case(
        name=f"null {key}",
        maker=ActivityTestCaseMaker(activity_maker=with_key_null(key)),
    )
    for key in ["@context", "actor", "id", "published", "to", "cc", "type"]
]

without_key_cases = [
    Case(
        name=f"without {key}",
        maker=ActivityTestCaseMaker(activity_maker=without_key(key)),
    )
    for key in ["@context", "actor", "id", "to", "cc", "type"]
]

as_list_key_cases = [
    Case(
        name=f"as list {key}",
        maker=ActivityTestCaseMaker(activity_maker=with_key_as_list(key)),
    )
    for key in ["actor", "published", "object", "type"]
]

create_cases = (
    recommended_cases
    + key_null_cases
    + without_key_cases
    + as_list_key_cases
    + [embedded_actor_case]
)


create_suite = SubSuite(
    short_name="create_activity",
    title="Varying the properties of the Create Activity",
    tests=create_cases,
)
