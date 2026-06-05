---
inclusion: manual
---

# Testing Convention

## Framework

Use `pytest` + `pytest-django`.

## Test Naming

Files: `test_excel_parser.py`, `test_phone_normalizer.py`, `test_campaign_sender.py`

Functions:
```python
def test_normalize_phone_removes_plus_and_spaces():
    ...
```

## Mocking

Mock external WhatsApp API calls. Never call real Meta API in tests.

## Minimum Required Tests

- Upload parser accepts valid xlsx
- Parser rejects missing phone column
- Phone normalizer removes plus sign and spaces
- Phone normalizer rejects non-digit values
- Dry run does not call WhatsApp API
- Successful send updates recipient status to sent
- Failed send updates recipient status to failed
- Webhook verification accepts correct token
- Webhook verification rejects wrong token
- Webhook status update changes recipient status
