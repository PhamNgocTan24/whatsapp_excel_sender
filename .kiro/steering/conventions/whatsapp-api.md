---
inclusion: manual
---

# WhatsApp API & Dry Run Convention

## Client Class

```python
class WhatsAppClient:
    def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str,
        body_params: list[str],
    ) -> dict:
        ...
```

## API URL

Build from env vars:
```
https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages
```

## Timeout

Always set timeout:
```python
requests.post(url, json=payload, headers=headers, timeout=20)
```

## Error Handling

Custom exception:
```python
class WhatsAppAPIError(Exception):
    def __init__(self, message: str, response_payload: dict | None = None):
        self.response_payload = response_payload
        super().__init__(message)
```

## Secrets

Never log: access token, full Authorization header.
Safe to log: request payload without token, response payload, HTTP status code.

## Template Parameters

For MVP, body parameters built from recipient data.
Default parameter order:
1. `name`
2. All values from `params` in column order

## Dry Run Mode

Implemented in the service layer, NOT by changing views:
```python
def send_recipient_message(recipient: Recipient, dry_run: bool) -> dict:
    if dry_run:
        return build_dry_run_response(recipient)
    return whatsapp_client.send_template_message(...)
```

Dry run message ID format: `dry_run_<recipient_id>`

Rules:
- Dry run creates logs.
- Dry run updates recipient status like a successful send.
- Dry run NEVER calls `requests.post`.
