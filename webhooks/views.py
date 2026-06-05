import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services.whatsapp_webhook_handler import handle_whatsapp_status_webhook

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    if request.method == "GET":
        return _verify_webhook(request)
    return _receive_webhook(request)


def _verify_webhook(request):
    """
    Handle WhatsApp webhook verification challenge.
    GET /webhooks/whatsapp/?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
    """
    mode = request.GET.get("hub.mode")
    verify_token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    expected_token = settings.WHATSAPP_VERIFY_TOKEN

    if mode == "subscribe" and verify_token == expected_token:
        logger.info("WhatsApp webhook verification successful.")
        return HttpResponse(challenge, content_type="text/plain", status=200)

    logger.warning(
        "WhatsApp webhook verification failed. mode=%s token_match=%s",
        mode, verify_token == expected_token,
    )
    return HttpResponseForbidden("Verification failed.")


def _receive_webhook(request):
    """
    Handle incoming WhatsApp webhook POST events.
    Always returns 200 to prevent Meta from retrying.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("Failed to parse webhook payload: %s", exc)
        # Still return 200 — Meta should not retry malformed payloads
        return HttpResponse("ok", status=200)

    try:
        updated = handle_whatsapp_status_webhook(payload)
        logger.debug("Webhook processed: %d recipient(s) updated.", updated)
    except Exception as exc:
        # Never crash — log and return 200
        logger.error("Unexpected error processing webhook: %s", exc, exc_info=True)

    return HttpResponse("ok", status=200)
