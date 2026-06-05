---
inclusion: manual
---

# Naming & Git Convention

## File & Module Naming

Use lowercase snake_case:
```
excel_parser.py
phone_normalizer.py
campaign_sender.py
whatsapp_client.py
```

## Class Naming

Use PascalCase:
```python
class Campaign(models.Model): ...
class WhatsAppClient: ...
class CampaignCreateForm(forms.ModelForm): ...
```

## Function Naming

Use snake_case, action-oriented:
```python
def normalize_phone_number(value: str) -> str: ...
def parse_campaign_excel(campaign: Campaign) -> list[Recipient]: ...
def send_campaign(campaign_id: int) -> None: ...
```

## Constants

Use uppercase snake_case. For model choices, prefer `TextChoices`.

## Git Branch Naming

```
feature/campaign-upload
feature/excel-parser
feature/whatsapp-client
fix/phone-validation
```

## Commit Messages

```
feat: add campaign upload form
feat: parse recipients from excel file
feat: integrate whatsapp cloud api client
fix: handle duplicate phone numbers
chore: add environment example file
```
