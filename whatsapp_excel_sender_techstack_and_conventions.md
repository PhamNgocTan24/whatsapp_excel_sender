# WhatsApp Excel Sender — Tech Stack and Coding Conventions

## 1. Purpose of this guide

This file is the implementation guide for AI/code generation.

Use it to keep the codebase consistent, simple, and maintainable while building the WhatsApp Excel Sender MVP.

The project should prioritize:

- Clear Django structure
- Simple service layer
- Safe handling of Excel uploads
- Clean WhatsApp API integration
- Easy local demo through dry run mode
- Code that a client can understand and maintain

---

## 2. Tech stack

### 2.1 Backend framework

Use:

```txt
Python 3.12+
Django 5.x or 6.x
```

Django is chosen because the target freelance job asks for Django and Python. It also provides built-in authentication, admin, forms, ORM, templates, and file upload handling.

### 2.2 Database

MVP default:

```txt
SQLite
```

Recommended production/demo upgrade:

```txt
PostgreSQL
```

Coding rule:

- Code must use Django ORM only.
- Do not write raw SQL unless absolutely necessary.
- Models must work with both SQLite and PostgreSQL.

### 2.3 Excel processing

Use:

```txt
openpyxl
```

Purpose:

- Read `.xlsx` files.
- Parse header row.
- Extract recipient rows.
- Optionally export `.xlsx` in version 2.

MVP export can use Python built-in `csv` module.

### 2.4 HTTP client

Use:

```txt
requests
```

Purpose:

- Call WhatsApp Cloud API.

Rules:

- Always set timeout.
- Never call external API directly from views.
- Wrap API calls in `WhatsAppClient` service.

### 2.5 Environment variables

Use:

```txt
python-dotenv or django-environ
```

Recommended for MVP:

```txt
python-dotenv
```

Required environment variables:

```env
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3

WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=local-verify-token
WHATSAPP_API_VERSION=v20.0

DEFAULT_DRY_RUN=True
```

Rules:

- Never hardcode secrets.
- Never commit `.env`.
- Include `.env.example`.

### 2.6 Frontend

Use Django templates.

Allowed:

```txt
Django Templates
Bootstrap 5 via CDN
```

Do not use React/Vue for MVP.

Reason:

- The MVP should be fast to build.
- Django templates are enough for upload, preview, and status pages.

### 2.7 Background jobs

MVP:

```txt
No Celery required
```

The send action can run synchronously for small Excel files.

Version 2:

```txt
Celery + Redis
```

Coding rule:

- Keep sending logic in a service function so it can later be moved into Celery without rewriting views.

### 2.8 Testing

Use:

```txt
pytest
pytest-django
```

Minimum test targets:

- Excel parser
- Phone normalization
- Recipient validation
- WhatsApp client dry run
- Webhook verification
- Webhook status update

### 2.9 Code quality tools

Use:

```txt
ruff
black
isort
```

Recommended commands:

```bash
ruff check .
black .
isort .
pytest
```

---

## 3. Project structure

Use this structure:

```txt
whatsapp_excel_sender/
│
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── campaigns/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── selectors.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── campaign_sender.py
│   │   ├── excel_parser.py
│   │   ├── phone_normalizer.py
│   │   └── whatsapp_client.py
│   ├── templates/
│   │   └── campaigns/
│   │       ├── campaign_detail.html
│   │       ├── campaign_form.html
│   │       ├── campaign_list.html
│   │       └── campaign_preview.html
│   └── tests/
│       ├── __init__.py
│       ├── test_excel_parser.py
│       ├── test_phone_normalizer.py
│       └── test_campaign_sender.py
│
├── webhooks/
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py
│   ├── views.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── whatsapp_webhook_handler.py
│   └── tests/
│       ├── __init__.py
│       └── test_whatsapp_webhook.py
│
└── templates/
    ├── base.html
    └── registration/
        └── login.html
```

---

## 4. Django app responsibilities

### 4.1 `campaigns` app

Responsible for:

- Campaign CRUD/list/detail
- Excel upload
- Excel parsing
- Recipient validation
- Sending WhatsApp messages
- Exporting results
- Campaign admin

### 4.2 `webhooks` app

Responsible for:

- WhatsApp webhook verification
- WhatsApp webhook event receiving
- Updating recipient status from webhook payloads
- Logging webhook events

---

## 5. Layering convention

Keep code in clear layers.

### 5.1 Views

Views should only:

- Read request data.
- Validate forms.
- Call services/selectors.
- Return response or redirect.
- Add user-facing messages.

Views must not:

- Parse Excel directly.
- Call WhatsApp API directly.
- Contain complex business rules.
- Build large API payloads inline.

### 5.2 Forms

Forms should handle:

- Required fields.
- File extension validation.
- Basic input validation.

Forms should not:

- Send messages.
- Parse the whole Excel file.
- Create recipients directly unless the service controls the flow.

### 5.3 Services

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

### 5.4 Selectors

Selectors contain reusable read queries.

Examples:

- `get_campaign_summary(campaign)`
- `get_campaign_recipients(campaign)`
- `get_status_counts(campaign)`

Selectors should not mutate database state.

### 5.5 API clients

External API integration must live in client classes.

Example:

```txt
campaigns/services/whatsapp_client.py
```

API client should:

- Build request payload.
- Send HTTP request.
- Handle timeout.
- Return parsed response.
- Raise clear exceptions.

API client should not:

- Update Django models directly.
- Know about campaign pages.
- Render UI.

---

## 6. Naming conventions

### 6.1 Files and modules

Use lowercase snake_case.

Good:

```txt
excel_parser.py
phone_normalizer.py
campaign_sender.py
whatsapp_client.py
```

Bad:

```txt
ExcelParser.py
phoneNormalizer.py
campaign-sender.py
```

### 6.2 Classes

Use PascalCase.

Examples:

```python
class Campaign(models.Model):
    pass

class WhatsAppClient:
    pass

class CampaignCreateForm(forms.ModelForm):
    pass
```

### 6.3 Functions

Use snake_case and action-oriented names.

Examples:

```python
def normalize_phone_number(value: str) -> str:
    ...


def parse_campaign_excel(campaign: Campaign) -> list[Recipient]:
    ...


def send_campaign(campaign_id: int) -> None:
    ...
```

### 6.4 Constants

Use uppercase snake_case.

Examples:

```python
STATUS_PENDING = "pending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"
```

For model choices, prefer `TextChoices`.

Example:

```python
class RecipientStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    INVALID = "invalid", "Invalid"
    SENDING = "sending", "Sending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    READ = "read", "Read"
    FAILED = "failed", "Failed"
```

---

## 7. Model conventions

### 7.1 Base fields

Every main model should include:

```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

Exception:

`MessageLog` can use only `created_at` because logs should be append-only.

### 7.2 `__str__`

Every model should define a useful `__str__`.

Example:

```python
def __str__(self) -> str:
    return f"{self.name} ({self.status})"
```

### 7.3 Status fields

Use `models.TextChoices`, not random strings.

### 7.4 JSON fields

Use `models.JSONField(default=dict)`.

Never use mutable default `{}`.

Good:

```python
params = models.JSONField(default=dict, blank=True)
```

Bad:

```python
params = models.JSONField(default={})
```

### 7.5 Query optimization

Use `select_related` for foreign keys in list/detail pages.

Example:

```python
Recipient.objects.select_related("campaign").filter(campaign=campaign)
```

---

## 8. Service conventions

### 8.1 Service function style

A service function should have one clear job.

Good:

```python
def send_campaign(campaign_id: int) -> CampaignSendResult:
    ...
```

Bad:

```python
def process_everything(request):
    ...
```

### 8.2 Return objects

For non-trivial services, use dataclasses for return values.

Example:

```python
from dataclasses import dataclass

@dataclass
class CampaignSendResult:
    total: int
    sent: int
    failed: int
    skipped: int
```

### 8.3 Transactions

Use `transaction.atomic()` when multiple related DB writes must succeed together.

Examples:

- Creating recipients after campaign upload.
- Updating recipient status and creating message log.

Do not keep a database transaction open while making external HTTP calls.

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

---

## 9. Excel parser conventions

### 9.1 Parser input/output

The Excel parser should not directly save database records.

It should return parsed row objects.

Example:

```python
@dataclass
class ParsedRecipientRow:
    row_number: int
    phone: str
    name: str
    params: dict
    errors: list[str]
```

### 9.2 Header normalization

Normalize headers with this behavior:

- Strip whitespace.
- Lowercase.
- Replace spaces with underscores.
- Remove unsupported characters if needed.

Example:

```txt
"Phone Number" -> "phone_number"
" appointment date " -> "appointment_date"
```

For MVP, required phone column should be exactly:

```txt
phone
```

Optional version 2 can support aliases like:

```txt
phone_number
mobile
whatsapp
```

### 9.3 Empty values

Convert empty Excel cells to empty string or `None` consistently.

Recommended:

- `phone`: empty string if missing
- `name`: empty string if missing
- `params`: keep empty string values so operator can see missing data

---

## 10. WhatsApp API conventions

### 10.1 Client class

Create a dedicated client:

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

### 10.2 API URL

Build URL from env vars:

```python
https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages
```

### 10.3 Timeout

Always set timeout:

```python
requests.post(url, json=payload, headers=headers, timeout=20)
```

### 10.4 Error handling

Create a custom exception:

```python
class WhatsAppAPIError(Exception):
    def __init__(self, message: str, response_payload: dict | None = None):
        self.response_payload = response_payload
        super().__init__(message)
```

### 10.5 Secrets

Never log:

- access token
- full Authorization header

Safe to log:

- request payload without token
- response payload
- HTTP status code

---

## 11. Dry run conventions

Dry run mode must be implemented in the service layer, not by changing views.

Recommended function:

```python
def send_recipient_message(recipient: Recipient, dry_run: bool) -> dict:
    if dry_run:
        return build_dry_run_response(recipient)
    return whatsapp_client.send_template_message(...)
```

Dry run message ID format:

```txt
dry_run_<recipient_id>
```

Rules:

- Dry run should create logs.
- Dry run should update recipient status like a successful send.
- Dry run should never call `requests.post`.

---

## 12. Webhook conventions

### 12.1 Verification endpoint

For GET requests:

- Read `hub.mode`.
- Read `hub.verify_token`.
- Read `hub.challenge`.
- Compare verify token with `WHATSAPP_VERIFY_TOKEN`.
- Return challenge if valid.
- Return 403 if invalid.

### 12.2 POST endpoint

For POST requests:

- Parse JSON safely.
- Pass payload to webhook handler service.
- Return 200 quickly.

View should not contain payload traversal logic.

Use:

```txt
webhooks/services/whatsapp_webhook_handler.py
```

### 12.3 Unknown payloads

Unknown or unsupported webhook payloads should be logged but should not crash.

---

## 13. View conventions

### 13.1 Function-based views or class-based views

For MVP, prefer function-based views because they are simpler for AI/code generation.

Allowed:

```python
@login_required
def campaign_list(request):
    ...
```

### 13.2 Messages framework

Use Django messages for user feedback.

Examples:

```python
messages.success(request, "Campaign created successfully.")
messages.error(request, "Excel file is invalid.")
```

### 13.3 Redirect after POST

Always redirect after successful POST.

This avoids duplicate form submissions.

Pattern:

```txt
POST -> process -> redirect -> GET
```

---

## 14. Template conventions

### 14.1 Base template

All pages should extend:

```txt
templates/base.html
```

### 14.2 UI style

Use Bootstrap 5.

Keep UI simple:

- Navbar
- Container
- Cards
- Tables
- Badges for statuses
- Buttons for actions

### 14.3 Status badge convention

Recommended badge styles:

| Status | Bootstrap class |
|---|---|
| pending | `bg-secondary` |
| invalid | `bg-warning text-dark` |
| duplicate | `bg-warning text-dark` |
| sending | `bg-info text-dark` |
| sent | `bg-primary` |
| delivered | `bg-success` |
| read | `bg-success` |
| failed | `bg-danger` |

---

## 15. URL naming conventions

Use app namespaces.

Campaign URLs:

```python
app_name = "campaigns"

urlpatterns = [
    path("", views.campaign_list, name="list"),
    path("new/", views.campaign_create, name="create"),
    path("<int:campaign_id>/", views.campaign_detail, name="detail"),
    path("<int:campaign_id>/preview/", views.campaign_preview, name="preview"),
    path("<int:campaign_id>/send/", views.campaign_send, name="send"),
    path("<int:campaign_id>/export/", views.campaign_export, name="export"),
]
```

Template usage:

```django
{% url 'campaigns:detail' campaign.id %}
```

---

## 16. Testing conventions

### 16.1 Test naming

Test files:

```txt
test_excel_parser.py
test_phone_normalizer.py
test_campaign_sender.py
test_whatsapp_webhook.py
```

Test functions:

```python
def test_normalize_phone_removes_plus_and_spaces():
    ...
```

### 16.2 What to mock

Mock external WhatsApp API calls.

Do not call real Meta API in tests.

### 16.3 Minimum tests

Required minimum tests:

```txt
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
```

---

## 17. Git conventions

### 17.1 Branch naming

Use:

```txt
feature/campaign-upload
feature/excel-parser
feature/whatsapp-client
feature/webhook-handler
fix/phone-validation
```

### 17.2 Commit messages

Use clear commit messages:

```txt
feat: add campaign upload form
feat: parse recipients from excel file
feat: integrate whatsapp cloud api client
fix: handle duplicate phone numbers
chore: add environment example file
```

---

## 18. README requirements

README must include:

- Project overview
- Features
- Tech stack
- Local setup
- Environment variables
- How to create superuser
- How to run migrations
- How to run server
- How to upload sample Excel
- How dry run mode works
- How to configure WhatsApp Cloud API
- How webhook setup works
- Demo flow

---

## 19. Sample `requirements.txt`

Use this as the first version:

```txt
Django>=5.0,<7.0
openpyxl>=3.1.0
requests>=2.31.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-django>=4.8.0
ruff>=0.6.0
black>=24.0.0
isort>=5.13.0
```

If PostgreSQL is added:

```txt
psycopg[binary]>=3.2.0
```

---

## 20. Implementation order for AI/code generation

Build in this order:

### Step 1 — Project setup

- Create Django project.
- Create `campaigns` app.
- Create `webhooks` app.
- Add templates and static setup.
- Configure `.env` loading.

### Step 2 — Models and admin

- Add `Campaign` model.
- Add `Recipient` model.
- Add `MessageLog` model.
- Register models in admin.
- Create migrations.

### Step 3 — Campaign upload

- Add campaign form.
- Add upload view.
- Add campaign list page.
- Add campaign create page.

### Step 4 — Excel parser

- Add `excel_parser.py`.
- Add `phone_normalizer.py`.
- Parse uploaded file.
- Create recipients.
- Show preview page.

### Step 5 — Sending service

- Add `whatsapp_client.py`.
- Add dry run mode.
- Add `campaign_sender.py`.
- Add send button/action.
- Update recipient statuses.
- Create message logs.

### Step 6 — Campaign detail and export

- Add campaign detail page.
- Add status counts.
- Add CSV export.

### Step 7 — Webhook

- Add webhook verification.
- Add webhook POST handler.
- Update recipient status from message ID.
- Log webhook payload.

### Step 8 — Tests and README

- Add unit tests.
- Add README.
- Add sample Excel file.
- Add demo instructions.

---

## 21. Hard rules for AI code generation

Follow these rules strictly:

1. Do not put all logic in views.
2. Do not call WhatsApp API from views.
3. Do not hardcode credentials.
4. Do not skip dry run mode.
5. Do not skip recipient status logging.
6. Do not ignore invalid Excel rows silently.
7. Do not crash on malformed webhook payloads.
8. Do not use React/Vue for MVP.
9. Do not introduce Celery in MVP.
10. Do not over-engineer with microservices.
11. Keep code readable over clever.
12. Every external API call must have timeout.
13. Every send attempt must create a log.
14. Invalid recipients must not be sent.
15. Use service layer for business logic.

---

## 22. Reference docs for implementation

Use these official docs while implementing:

- Django file uploads: https://docs.djangoproject.com/en/6.0/topics/http/file-uploads/
- Django uploaded files: https://docs.djangoproject.com/en/6.0/ref/files/uploads/
- Django coding style: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/
- openpyxl documentation: https://openpyxl.readthedocs.io/
- WhatsApp Cloud API get started: https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started
- WhatsApp webhooks overview: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview/
