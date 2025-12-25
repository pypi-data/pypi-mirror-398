from funfedi_parsing_test_cases.activity.create import recommended_cases
from .validators import update_with_validate_activity


def test_update_test_case():
    default_case = recommended_cases[0]
    previous_status = default_case.status

    result = update_with_validate_activity(default_case)

    assert result.status == previous_status
