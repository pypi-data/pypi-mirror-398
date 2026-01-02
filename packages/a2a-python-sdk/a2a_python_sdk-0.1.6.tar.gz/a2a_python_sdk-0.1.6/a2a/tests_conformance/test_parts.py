from a2a.schema.parts import TextPart, JsonPart


def test_text_part():
    part = TextPart(text="hello")
    assert part.type == "text"


def test_json_part():
    part = JsonPart(data={"a": 1})
    assert part.type == "json"
