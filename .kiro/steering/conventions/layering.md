---
inclusion: manual
---

# Layering & Architecture Convention

## Layer Responsibilities

### Views
Views should only:
- Read request data.
- Validate forms.
- Call services/selectors.
- Return response or redirect.
- Add user-facing messages.

Views must NOT:
- Parse Excel directly.
- Call WhatsApp API directly.
- Contain complex business rules.
- Build large API payloads inline.

### Forms
Forms should handle:
- Required fields.
- File extension validation.
- Basic input validation.

Forms should NOT:
- Send messages.
- Parse the whole Excel file.
- Create recipients directly unless the service controls the flow.

### Services
Services contain business actions.

Examples:
- `parse_campaign_excel(campaign)`
- `send_campaign(campaign_id)`
- `send_recipient_message(recipient_id)`
- `handle_whatsapp_status_webhook(payload)`

Services are allowed to:
- Create/update models.
- Call external API clients.
- Create logs.
- Raise custom exceptions.

### Selectors
Selectors contain reusable read queries.

Examples:
- `get_campaign_summary(campaign)`
- `get_campaign_recipients(campaign)`
- `get_status_counts(campaign)`

Selectors should NOT mutate database state.

### API Clients
External API integration must live in client classes.

Location: `campaigns/services/whatsapp_client.py`

API client should:
- Build request payload.
- Send HTTP request.
- Handle timeout.
- Return parsed response.
- Raise clear exceptions.

API client should NOT:
- Update Django models directly.
- Know about campaign pages.
- Render UI.
