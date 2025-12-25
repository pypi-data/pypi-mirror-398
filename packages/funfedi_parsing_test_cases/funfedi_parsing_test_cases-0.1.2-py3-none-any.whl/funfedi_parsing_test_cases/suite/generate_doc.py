import json
from pathlib import Path
from funfedi_parsing_test_cases.testing import default_env
from funfedi_parsing_test_cases.types import Case

from . import SubSuite


def activity_and_object(case: Case) -> tuple[dict, dict]:
    return case.maker.activity_and_object(default_env)


def subtitle_for_idx_and_name(idx, name) -> list[str]:
    return ["", f"## Example {idx + 1}: {name}", ""]


def dict_to_lines(data: dict) -> list[str]:
    json_lines = json.dumps(data, indent=2).split("\n")
    return ["```json"] + json_lines + ["```"]


def lines_as_admonition_content(lines: list[str]) -> list[str]:
    prefix = " " * 4
    return [""] + [prefix + x for x in lines] + [""]


def dict_as_admonition_content(data: dict) -> list[str]:
    prefix = " " * 4
    return [""] + [prefix + x for x in dict_to_lines(data)] + [""]


def sub_suite_to_lines(sub_suite: SubSuite) -> list[str]:
    lines = []

    lines.append(f"# {sub_suite.title}")

    for idx, test in enumerate(sub_suite.tests):
        activity, obj = activity_and_object(test)
        lines += subtitle_for_idx_and_name(idx, test.name)

        if len(test.comments) > 0:
            comments = sum(
                (["```"] + x.split("\n") + ["```"] for x in test.comments), []
            )
            lines += ['??? Note "Comments"']
            lines += lines_as_admonition_content(comments)

        lines += ['??? Example "Activity"']
        lines += dict_as_admonition_content(activity)

        lines += ['??? Example "Object"']
        lines += dict_as_admonition_content(obj)

    return lines + [""]


def write_docs_for_sub_suites(sub_suites: list[SubSuite]):
    Path("docs/suites").mkdir(exist_ok=True, parents=True)
    for sub_suite in sub_suites:
        with open(f"docs/suites/{sub_suite.short_name}.md", "w") as fp:
            fp.write("\n".join(sub_suite_to_lines(sub_suite)))
