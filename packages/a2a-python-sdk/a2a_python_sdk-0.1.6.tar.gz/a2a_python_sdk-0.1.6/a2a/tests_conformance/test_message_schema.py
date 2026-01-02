from a2a.schema.message import A2AMessage

def test_message_has_signature():
    msg = A2AMessage(
        sender_id="a",
        receiver_id="b",
        intent="test",
        payload={},
        signature="sig"
    )
    assert msg.signature
