from unittest.mock import patch

import pytest

from campaigns.models import Campaign, CampaignStatus, MessageLog, Recipient, RecipientStatus
from campaigns.services.campaign_sender import _build_body_params, send_campaign
from campaigns.services.whatsapp_client import WhatsAppAPIError

# --- Fixtures ---


@pytest.fixture
def operator(django_user_model):
    return django_user_model.objects.create_user(username="testop", password="pass")


@pytest.fixture
def campaign(operator, tmp_path):
    # Create a dummy file so FileField doesn't complain
    dummy = tmp_path / "test.xlsx"
    dummy.write_bytes(b"")
    c = Campaign.objects.create(
        name="Test Campaign",
        template_name="hello_world",
        language_code="en_US",
        excel_file=str(dummy),
        dry_run=True,
        created_by=operator,
        status=CampaignStatus.READY,
    )
    return c


@pytest.fixture
def pending_recipient(campaign):
    return Recipient.objects.create(
        campaign=campaign,
        row_number=2,
        phone="84901234567",
        name="Alice",
        params={"order_id": "ORD001"},
        status=RecipientStatus.PENDING,
    )


# --- Body params tests ---


def test_build_body_params_with_name_and_params(pending_recipient):
    params = _build_body_params(pending_recipient)
    assert params[0] == "Alice"
    assert "ORD001" in params


def test_build_body_params_no_name(campaign):
    recipient = Recipient(
        campaign=campaign,
        row_number=3,
        phone="84900000001",
        name="",
        params={"order_id": "ORD002"},
    )
    params = _build_body_params(recipient)
    assert "ORD002" in params
    assert "Alice" not in params


# --- Dry run tests ---


@pytest.mark.django_db
def test_dry_run_does_not_call_whatsapp_api(campaign, pending_recipient):
    with patch("campaigns.services.campaign_sender.WhatsAppClient") as MockClient:
        result = send_campaign(campaign.id)
        MockClient.assert_not_called()

    assert result.sent == 1
    assert result.failed == 0


@pytest.mark.django_db
def test_dry_run_marks_recipient_as_sent(campaign, pending_recipient):
    send_campaign(campaign.id)
    pending_recipient.refresh_from_db()
    assert pending_recipient.status == RecipientStatus.SENT


@pytest.mark.django_db
def test_dry_run_stores_message_id(campaign, pending_recipient):
    send_campaign(campaign.id)
    pending_recipient.refresh_from_db()
    assert pending_recipient.whatsapp_message_id == f"dry_run_{pending_recipient.id}"


@pytest.mark.django_db
def test_dry_run_creates_message_log(campaign, pending_recipient):
    send_campaign(campaign.id)
    logs = MessageLog.objects.filter(campaign=campaign)
    assert logs.count() == 1
    assert logs.first().event_type == "send_template"
    assert logs.first().status == RecipientStatus.SENT


@pytest.mark.django_db
def test_dry_run_updates_campaign_status_to_completed(campaign, pending_recipient):
    send_campaign(campaign.id)
    campaign.refresh_from_db()
    assert campaign.status == CampaignStatus.COMPLETED


# --- Invalid recipients are skipped ---


@pytest.mark.django_db
def test_invalid_recipients_are_skipped(campaign):
    Recipient.objects.create(
        campaign=campaign,
        row_number=2,
        phone="",
        name="Bad",
        status=RecipientStatus.INVALID,
    )
    result = send_campaign(campaign.id)
    assert result.total == 0
    assert result.sent == 0
    assert MessageLog.objects.filter(campaign=campaign).count() == 0


# --- Real API send ---


@pytest.mark.django_db
def test_successful_real_send_marks_recipient_sent(campaign, pending_recipient):
    campaign.dry_run = False
    campaign.save()

    fake_response = {"messages": [{"id": "wamid.abc123"}]}

    with patch("campaigns.services.campaign_sender.WhatsAppClient") as MockClient:
        MockClient.return_value.send_template_message.return_value = fake_response
        result = send_campaign(campaign.id)

    pending_recipient.refresh_from_db()
    assert pending_recipient.status == RecipientStatus.SENT
    assert pending_recipient.whatsapp_message_id == "wamid.abc123"
    assert result.sent == 1


@pytest.mark.django_db
def test_failed_real_send_marks_recipient_failed(campaign, pending_recipient):
    campaign.dry_run = False
    campaign.save()

    with patch("campaigns.services.campaign_sender.WhatsAppClient") as MockClient:
        MockClient.return_value.send_template_message.side_effect = WhatsAppAPIError(
            "Auth failed", response_payload={"error": {"message": "Auth failed"}}
        )
        result = send_campaign(campaign.id)

    pending_recipient.refresh_from_db()
    assert pending_recipient.status == RecipientStatus.FAILED
    assert "Auth failed" in pending_recipient.error_message
    assert result.failed == 1


@pytest.mark.django_db
def test_failed_send_creates_error_log(campaign, pending_recipient):
    campaign.dry_run = False
    campaign.save()

    with patch("campaigns.services.campaign_sender.WhatsAppClient") as MockClient:
        MockClient.return_value.send_template_message.side_effect = WhatsAppAPIError("Timeout", response_payload=None)
        send_campaign(campaign.id)

    log = MessageLog.objects.filter(campaign=campaign).first()
    assert log is not None
    assert log.status == RecipientStatus.FAILED
    assert "Timeout" in log.error_message


@pytest.mark.django_db
def test_campaign_status_completed_with_errors_on_partial_failure(campaign):
    Recipient.objects.create(
        campaign=campaign,
        row_number=2,
        phone="84901234567",
        name="Alice",
        status=RecipientStatus.PENDING,
    )
    Recipient.objects.create(
        campaign=campaign,
        row_number=3,
        phone="84900000002",
        name="Bob",
        status=RecipientStatus.PENDING,
    )

    campaign.dry_run = False
    campaign.save()

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"messages": [{"id": "wamid.ok"}]}
        raise WhatsAppAPIError("Failed")

    with patch("campaigns.services.campaign_sender.WhatsAppClient") as MockClient:
        MockClient.return_value.send_template_message.side_effect = side_effect
        result = send_campaign(campaign.id)

    campaign.refresh_from_db()
    assert campaign.status == CampaignStatus.COMPLETED_WITH_ERRORS
    assert result.sent == 1
    assert result.failed == 1
