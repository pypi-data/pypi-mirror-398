from funfedi_parsing_test_cases.schema import validate_activity
from funfedi_parsing_test_cases.testing import default_env
from funfedi_parsing_test_cases.types import Case, TestCaseStatus


def update_with_validate_activity(case: Case) -> Case:
    activity = case.maker.to_send(default_env).activity

    validation_result = validate_activity(activity)

    if validation_result:
        case.status = TestCaseStatus.may_fail
        case.comments.append("Validation of activity against schema failed")
        case.comments.append(validation_result)

    return case


validators = [update_with_validate_activity]


def validate(case: Case) -> Case:
    for validator in validators:
        case = validator(case)
    return case
