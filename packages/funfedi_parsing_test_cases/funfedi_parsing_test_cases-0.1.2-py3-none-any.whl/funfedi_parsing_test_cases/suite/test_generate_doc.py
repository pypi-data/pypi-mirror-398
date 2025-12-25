from funfedi_parsing_test_cases.activity import activity_context_suite
from .generate_doc import dict_to_lines, sub_suite_to_lines


def test_sub_suite_to_lines():
    result = sub_suite_to_lines(activity_context_suite)

    assert isinstance(result, list)
    assert result[0].startswith("# ")


def test_dict_to_lines():
    result = dict_to_lines({})

    assert (
        "\n".join(result)
        == """```json
{}
```"""
    )
