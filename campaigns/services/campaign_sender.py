import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from django.db import transaction

from ..models import Campaign, CampaignStatus, MessageDirection, MessageLog, Recipient, RecipientStatus
from .whatsapp_client import WhatsAppAPIError, WhatsAppClient

logger = logging.getLogger(__name__)


@dataclass
class CampaignSendResult:
    total: int
    sent: int
    failed: int
    skipped: int


def _build_body_params(recipient: Recipient) -> list[str]:
    """
    Build ordered list of template body parameters.
    Order: name first, then all params values in insertion order.
    """
    params: list[str] = []
    if recipient.name:
        params.append(recipient.name)
    if recipient.params:
        params.extend(str(v) for v in recipient.params.values())
    return params


def _build_dry_run_response(recipient: Recipient) -> dict:
    return {
        "dry_run": True,
        "messaging_product": "whatsapp",
        "messages": [{"id": f"dry_run_{recipient.id}"}],
    }


def send_recipient_message(recipient: Recipient, dry_run: bool) -> dict:
    """
    Send a WhatsApp template message for a single recipient.

    Handles dry run mode in the service layer.
    Does NOT update the recipient or create logs — that is the caller's responsibility.

    Returns the response payload dict.
    Raises WhatsAppAPIError on real API failure.
    """
    if dry_run:
        return _build_dry_run_response(recipient)

    client = WhatsAppClient()
    body_params = _build_body_params(recipient)
    return client.send_template_message(
        to_phone=recipient.phone,
        template_name=recipient.campaign.template_name,
        language_code=recipient.campaign.language_code,
        body_params=body_params,
    )


def _get_message_id_from_response(response: dict) -> str | None:
    """Extract the WhatsApp message ID from a successful API response."""
    try:
        return response["messages"][0]["id"]
    except (KeyError, IndexError, TypeError):
        return None


def _process_recipient(recipient: Recipient, dry_run: bool, campaign: Campaign) -> bool:
    """
    Send message for one recipient, update its status, and create a MessageLog.

    Returns True if sent successfully, False if failed.
    """
    # Build request payload for logging (without token)
    request_payload = {
        "to": recipient.phone,
        "template_name": campaign.template_name,
        "language_code": campaign.language_code,
        "body_params": _build_body_params(recipient),
        "dry_run": dry_run,
    }

    # Mark as sending
    recipient.status = RecipientStatus.SENDING
    recipient.save(update_fields=["status", "updated_at"])

    try:
        response = send_recipient_message(recipient, dry_run)
    except WhatsAppAPIError as exc:
        # API failed — update recipient and log
        with transaction.atomic():
            recipient.status = RecipientStatus.FAILED
            recipient.error_message = str(exc)
            recipient.save(update_fields=["status", "error_message", "updated_at"])

            MessageLog.objects.create(
                campaign=campaign,
                recipient=recipient,
                direction=MessageDirection.OUTBOUND,
                event_type="send_template",
                status=RecipientStatus.FAILED,
                request_payload=request_payload,
                response_payload=exc.response_payload,
                error_message=str(exc),
            )

        logger.warning("Failed to send to %s: %s", recipient.phone, exc)
        return False

    # Success — update recipient and log
    message_id = _get_message_id_from_response(response)

    with transaction.atomic():
        recipient.status = RecipientStatus.SENT
        recipient.whatsapp_message_id = message_id
        recipient.sent_at = datetime.now(tz=timezone.utc)
        recipient.error_message = ""
        recipient.save(
            update_fields=[
                "status",
                "whatsapp_message_id",
                "sent_at",
                "error_message",
                "updated_at",
            ]
        )

        MessageLog.objects.create(
            campaign=campaign,
            recipient=recipient,
            direction=MessageDirection.OUTBOUND,
            event_type="send_template",
            status=RecipientStatus.SENT,
            request_payload=request_payload,
            response_payload=response,
        )

    return True


def send_campaign(campaign_id: int) -> CampaignSendResult:
    """
    Send WhatsApp messages to all valid (pending) recipients in a campaign.

    Skips invalid, duplicate, and already-sent recipients.
    Updates campaign status when done.

    Returns a CampaignSendResult summary.
    """
    campaign = Campaign.objects.get(id=campaign_id)
    dry_run = campaign.dry_run

    pending_recipients = Recipient.objects.filter(
        campaign=campaign,
        status=RecipientStatus.PENDING,
    )

    total = pending_recipients.count()
    sent = 0
    failed = 0
    skipped = 0

    if total == 0:
        return CampaignSendResult(total=0, sent=0, failed=0, skipped=0)

    # Mark campaign as sending
    campaign.status = CampaignStatus.SENDING
    campaign.save(update_fields=["status", "updated_at"])

    for recipient in pending_recipients:
        success = _process_recipient(recipient, dry_run, campaign)
        if success:
            sent += 1
        else:
            failed += 1

    # Update final campaign status
    if failed == 0:
        campaign.status = CampaignStatus.COMPLETED
    elif sent == 0:
        campaign.status = CampaignStatus.FAILED
    else:
        campaign.status = CampaignStatus.COMPLETED_WITH_ERRORS

    campaign.save(update_fields=["status", "updated_at"])

    logger.info(
        "Campaign %d send complete: %d sent, %d failed, %d skipped",
        campaign_id,
        sent,
        failed,
        skipped,
    )

    return CampaignSendResult(total=total, sent=sent, failed=failed, skipped=skipped)
