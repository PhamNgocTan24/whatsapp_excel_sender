import json

import pytest
from django.test import Client
from django.urls import reverse

from campaigns.models import Campaign, CampaignStatus, MessageLog, Recipient, RecipientStatus

# --- Fixtures ---


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def operator(django_user_model):
    return django_user_model.objects.create_user(username="webhookop", password="pass")


@pytest.fixture
def campaign(operator, tmp_path):
    dummy = tmp_path / "test.xlsx"
    dummy.write_bytes(b"")
    return Campaign.objects.create(
        name="Webhook Test Campaign",
        template_name="hello_world",
        language_code="en_US",
        excel_file=str(dummy),
        dry_run=True,
        created_by=operator,
        status=CampaignStatus.READY,
    )


@pytest.fixture
def sent_recipient(campaign):
    return Recipient.objects.create(
        campaign=campaign,
        row_number=2,
        phone="84901234567",
        name="Alice",
        status=RecipientStatus.SENT,
        whatsapp_message_id="wamid.test123",
    )


def _make_status_payload(message_id: str, status: str, errors: list = None) -> dict:
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "statuses": [
                                {
                                    "id": message_id,
                                    "status": status,
                                    "timestamp": "1234567890",
                                    "recipient_id": "84901234567",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    if errors:
        payload["entry"][0]["changes"][0]["value"]["statuses"][0]["errors"] = errors
    return payload


# ---- Verification tests ----


@pytest.mark.django_db
def test_webhook_verification_accepts_correct_token(client, settings):
    settings.WHATSAPP_VERIFY_TOKEN = "test-token"
    response = client.get(
        reverse("webhooks:whatsapp"),
        {
            "hub.mode": "subscribe",
            "hub.verify_token": "test-token",
            "hub.challenge": "challenge_abc",
        },
    )
    assert response.status_code == 200
    assert response.content == b"challenge_abc"


@pytest.mark.django_db
def test_webhook_verification_rejects_wrong_token(client, settings):
    settings.WHATSAPP_VERIFY_TOKEN = "test-token"
    response = client.get(
        reverse("webhooks:whatsapp"),
        {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "challenge_abc",
        },
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_webhook_verification_rejects_wrong_mode(client, settings):
    settings.WHATSAPP_VERIFY_TOKEN = "test-token"
    response = client.get(
        reverse("webhooks:whatsapp"),
        {
            "hub.mode": "unsubscribe",
            "hub.verify_token": "test-token",
            "hub.challenge": "challenge_abc",
        },
    )
    assert response.status_code == 403


# ---- Status update tests ----


@pytest.mark.django_db
def test_webhook_delivered_updates_recipient_status(client, sent_recipient):
    payload = _make_status_payload("wamid.test123", "delivered")
    response = client.post(
        reverse("webhooks:whatsapp"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    sent_recipient.refresh_from_db()
    assert sent_recipient.status == RecipientStatus.DELIVERED


@pytest.mark.django_db
def test_webhook_read_updates_recipient_status(client, sent_recipient):
    payload = _make_status_payload("wamid.test123", "read")
    response = client.post(
        reverse("webhooks:whatsapp"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    sent_recipient.refresh_from_db()
    assert sent_recipient.status == RecipientStatus.READ


@pytest.mark.django_db
def test_webhook_failed_updates_recipient_status(client, sent_recipient):
    payload = _make_status_payload("wamid.test123", "failed", errors=[{"message": "Number not registered"}])
    response = client.post(
        reverse("webhooks:whatsapp"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    sent_recipient.refresh_from_db()
    assert sent_recipient.status == RecipientStatus.FAILED
    assert "Number not registered" in sent_recipient.error_message


@pytest.mark.django_db
def test_webhook_creates_message_log(client, sent_recipient):
    payload = _make_status_payload("wamid.test123", "delivered")
    client.post(
        reverse("webhooks:whatsapp"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    log = MessageLog.objects.filter(
        recipient=sent_recipient,
        event_type="status_update",
    ).first()
    assert log is not None
    assert log.status == "delivered"


@pytest.mark.django_db
def test_webhook_unknown_message_id_returns_200(client):
    """Unknown message IDs must not crash — return 200."""
    payload = _make_status_payload("wamid.unknown999", "delivered")
    response = client.post(
        reverse("webhooks:whatsapp"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_webhook_malformed_json_returns_200(client):
    """Malformed payload must not crash — return 200."""
    response = client.post(
        reverse("webhooks:whatsapp"),
        data="not json {{{",
        content_type="application/json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_webhook_empty_payload_returns_200(client):
    response = client.post(
        reverse("webhooks:whatsapp"),
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_webhook_unknown_status_is_ignored(client, sent_recipient):
    """Unknown WhatsApp statuses should be ignored, not crash."""
    payload = _make_status_payload("wamid.test123", "some_future_status")
    response = client.post(
        reverse("webhooks:whatsapp"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    sent_recipient.refresh_from_db()
    # Status should remain unchanged
    assert sent_recipient.status == RecipientStatus.SENT
