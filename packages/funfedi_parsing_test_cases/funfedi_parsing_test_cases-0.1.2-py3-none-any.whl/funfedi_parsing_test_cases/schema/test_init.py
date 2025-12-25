from . import load_schema


def test_load_schema():
    result = load_schema("activity_pub_activity")

    assert isinstance(result, dict)
