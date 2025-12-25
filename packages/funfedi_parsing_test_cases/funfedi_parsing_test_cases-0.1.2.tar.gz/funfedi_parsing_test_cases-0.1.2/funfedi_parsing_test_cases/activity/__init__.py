from ..suite import SubSuite
from funfedi_parsing_test_cases.types import Environment, Case
from funfedi_parsing_test_cases.cases import ActivityTestCaseMaker
from funfedi_parsing_test_cases.cases.activity import default_activity_maker


from .create import create_suite
from .addressing import addressing_suite

__all__ = [
    "announce_suite",
    "create_suite",
    "addressing_suite",
    "activity_context_suite",
]


def with_announce():
    def modified(environment: Environment, obj: dict):
        create = default_activity_maker(environment, obj)
        announce = default_activity_maker(environment, create)
        announce["type"] = "Announce"
        return announce

    return modified


announce_cases = [
    Case(
        name="Announce(Create(Note))",
        maker=ActivityTestCaseMaker(activity_maker=with_announce()),
    )
]
announce_suite = SubSuite(
    short_name="announce_create",
    title="Announce(Create) according to FEP-1b12",
    tests=announce_cases,
)


def with_context_example(context):
    def modified(environment: Environment, obj: dict):
        data = default_activity_maker(environment, obj)
        data["@context"] = context
        return data

    return modified


ap_context_url = "https://www.w3.org/ns/activitystreams"
hashtag_dict = {"Hashtag": "as:Hashtag"}
other_context_url = "https://w3id.org/security/data-integrity/v2"

activity_context_cases = [
    Case(
        name=context_name,
        maker=ActivityTestCaseMaker(
            activity_maker=with_context_example(context_example)
        ),
    )
    for context_name, context_example in {
        "list of AP context": [ap_context_url],
        "AP context": ap_context_url,
        "list of AP context and dictionary": [ap_context_url, hashtag_dict],
        "list of dictionary and AP context": [hashtag_dict, ap_context_url],
        "list of AP context and other url": [ap_context_url, other_context_url],
        "list of other url and AP context": [other_context_url, ap_context_url],
    }.items()
]

activity_context_suite = SubSuite(
    short_name="activity_context",
    title="Varying the value of the @context property",
    tests=activity_context_cases,
)
