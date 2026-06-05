---
inclusion: manual
---

# Webhook Convention

## Verification Endpoint (GET)

- Read `hub.mode`, `hub.verify_token`, `hub.challenge`.
- Compare verify token with `WHATSAPP_VERIFY_TOKEN` env var.
- Return challenge if valid.
- Return 403 if invalid.

## POST Endpoint

- Parse JSON safely.
- Pass payload to webhook handler service.
- Return 200 quickly.

View should NOT contain payload traversal logic.

Handler location: `webhooks/services/whatsapp_webhook_handler.py`

## Status Mapping

| WhatsApp status | App recipient status |
|-----------------|---------------------|
| `sent` | `sent` |
| `delivered` | `delivered` |
| `read` | `read` |
| `failed` | `failed` |

## Unknown Payloads

Unknown or unsupported webhook payloads should be logged but should NOT crash.

## Behavior

- Parse incoming JSON payload.
- Find recipient by WhatsApp message ID.
- Update recipient status.
- Create `MessageLog` with raw webhook payload.
- Return HTTP 200 quickly.
