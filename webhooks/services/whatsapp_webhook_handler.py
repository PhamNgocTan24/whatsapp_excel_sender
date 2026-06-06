import logging

from django.db import transaction

from campaigns.models import MessageDirection, MessageLog, Recipient, RecipientStatus

logger = logging.getLogger(__name__)

# Map WhatsApp status strings to our RecipientStatus
WHATSAPP_STATUS_MAP = {
    "sent": RecipientStatus.SENT,
    "delivered": RecipientStatus.DELIVERED,
    "read": RecipientStatus.READ,
    "failed": RecipientStatus.FAILED,
}


def _extract_status_updates(payload: dict) -> list[dict]:
    """
    Extract status update entries from a WhatsApp webhook payload.

    Returns a list of dicts with keys: message_id, status, errors.
    """
    updates = []
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for status_obj in value.get("statuses", []):
                    message_id = status_obj.get("id")
                    status = status_obj.get("status")
                    errors = status_obj.get("errors", [])
                    if message_id and status:
                        updates.append(
                            {
                                "message_id": message_id,
                                "status": status,
                                "errors": errors,
                            }
                        )
    except Exception as exc:
        logger.warning("Error extracting status updates from webhook payload: %s", exc)

    return updates


def handle_whatsapp_status_webhook(payload: dict) -> int:
    """
    Process a WhatsApp status webhook payload.

    - Finds recipients by WhatsApp message ID.
    - Updates recipient status.
    - Creates a MessageLog for each update.
    - Ignores unknown message IDs safely.

    Returns the number of recipients updated.
    """
    updates = _extract_status_updates(payload)

    if not updates:
        logger.debug("Webhook payload contained no status updates: %s", payload)
        return 0

    updated_count = 0

    for update in updates:
        message_id = update["message_id"]
        wa_status = update["status"]
        errors = update["errors"]

        app_status = WHATSAPP_STATUS_MAP.get(wa_status)

        if app_status is None:
            logger.debug(
                "Unknown WhatsApp status '%s' for message %s — skipping.",
                wa_status,
                message_id,
            )
            continue

        # Find recipient by WhatsApp message ID
        try:
            recipient = Recipient.objects.select_related("campaign").get(whatsapp_message_id=message_id)
        except Recipient.DoesNotExist:
            logger.debug("No recipient found for whatsapp_message_id=%s — ignoring.", message_id)
            # Still log the event for debugging
            MessageLog.objects.create(
                campaign_id=None,
                recipient=None,
                direction=MessageDirection.WEBHOOK,
                event_type="status_update",
                status=wa_status,
                response_payload=payload,
                error_message=f"Unknown message_id: {message_id}",
            )
            continue
        except Exception as exc:
            logger.error("Error looking up recipient for message_id=%s: %s", message_id, exc)
            continue

        # Build error message from WhatsApp errors array if present
        error_message = ""
        if errors:
            error_message = "; ".join(e.get("message", str(e)) for e in errors if isinstance(e, dict))

        with transaction.atomic():
            recipient.status = app_status
            update_fields = ["status", "updated_at"]
            if error_message:
                recipient.error_message = error_message
                update_fields.append("error_message")
            recipient.save(update_fields=update_fields)

            MessageLog.objects.create(
                campaign=recipient.campaign,
                recipient=recipient,
                direction=MessageDirection.WEBHOOK,
                event_type="status_update",
                status=wa_status,
                response_payload=payload,
                error_message=error_message,
            )

        updated_count += 1
        logger.info(
            "Webhook: recipient %s updated to '%s' (message_id=%s)",
            recipient.phone,
            app_status,
            message_id,
        )

    return updated_count
