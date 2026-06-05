---
inclusion: manual
---

# Models & Database Convention

## Base Fields

Every main model should include:
```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

Exception: `MessageLog` uses only `created_at` (append-only).

## `__str__`

Every model must define a useful `__str__`:
```python
def __str__(self) -> str:
    return f"{self.name} ({self.status})"
```

## Status Fields

Use `models.TextChoices`, not random strings:
```python
class RecipientStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    INVALID = "invalid", "Invalid"
    DUPLICATE = "duplicate", "Duplicate"
    SENDING = "sending", "Sending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    READ = "read", "Read"
    FAILED = "failed", "Failed"
```

## JSON Fields

Use `models.JSONField(default=dict, blank=True)`.

Never use mutable default `{}`:
```python
# Good
params = models.JSONField(default=dict, blank=True)

# Bad
params = models.JSONField(default={})
```

## Query Optimization

Use `select_related` for foreign keys in list/detail pages:
```python
Recipient.objects.select_related("campaign").filter(campaign=campaign)
```

## Database Rules

- Use Django ORM only. No raw SQL unless absolutely necessary.
- Models must work with both SQLite and PostgreSQL.
