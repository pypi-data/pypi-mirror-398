from a2a.protocol.notifications import WebhookConfig


def test_webhook_config():
    webhook = WebhookConfig(
        url="https://example.com/events",
        events=["task_update", "artifact"],
    )

    assert "artifact" in webhook.events
