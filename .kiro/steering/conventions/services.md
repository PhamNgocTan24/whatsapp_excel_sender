---
inclusion: manual
---

# Services & Business Logic Convention

## Service Function Style

A service function should have one clear job:
```python
def send_campaign(campaign_id: int) -> CampaignSendResult:
    ...
```

## Return Objects

For non-trivial services, use dataclasses for return values:
```python
from dataclasses import dataclass

@dataclass
class CampaignSendResult:
    total: int
    sent: int
    failed: int
    skipped: int
```

## Transactions

Use `transaction.atomic()` when multiple related DB writes must succeed together.

Do NOT keep a database transaction open while making external HTTP calls.

Wrong:
```python
with transaction.atomic():
    response = requests.post(...)
    recipient.status = "sent"
    recipient.save()
```

Better:
```python
recipient.status = RecipientStatus.SENDING
recipient.save(update_fields=["status", "updated_at"])

response = whatsapp_client.send_template_message(...)

with transaction.atomic():
    recipient.status = RecipientStatus.SENT
    recipient.save(update_fields=["status", "whatsapp_message_id", "sent_at", "updated_at"])
    MessageLog.objects.create(...)
```

## Background Jobs

MVP: No Celery. Send action runs synchronously.

Coding rule: Keep sending logic in a service function so it can later be moved into Celery without rewriting views.
