import json
from pathlib import Path

from jsonschema import ValidationError, validate


__all__ = ["validate_activity"]


def load_schema(name: str) -> dict:
    filename = Path(__file__).parent / f"{name}.schema.json"
    with open(filename) as fp:
        return json.load(fp)


activity_pub_schema = load_schema("activity_pub_activity")


def validate_activity(activity) -> str | None:
    try:
        validate(activity, activity_pub_schema)
        return None
    except ValidationError as e:
        return str(e)
