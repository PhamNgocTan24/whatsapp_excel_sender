# WhatsApp Excel Sender — MVP Requirements

## 1. Project overview

Build a small Django web application that allows an operator to upload an Excel file, preview recipients, validate data, send personalized WhatsApp template messages through the official WhatsApp Cloud API, and track the send result for each row.

This project is designed as a freelance-ready MVP matching jobs that ask for:

- Python automation
- Django backend
- Excel file processing
- WhatsApp automation/API integration
- Basic reporting/logging

The MVP must be simple enough to finish quickly, but clean enough to show to a client as a serious demo.

---

## 2. Main goal

The system should answer this client need:

> “I have an Excel file with customer phone numbers and message variables. I want to upload it, send WhatsApp messages automatically, and know which rows succeeded or failed.”

The MVP is **not** a full SaaS product. It is a focused internal tool.

---

## 3. User roles

### 3.1 Operator

The operator is the main user of the application.

The operator can:

- Log in to the app.
- Upload an Excel file.
- Create a campaign.
- Preview parsed recipients.
- Start sending messages.
- View sending status.
- Export result logs.

### 3.2 System

The system can:

- Parse Excel files.
- Validate recipient data.
- Send messages through WhatsApp Cloud API.
- Store message status.
- Receive webhook events from WhatsApp.
- Update message status based on webhook payloads.

---

## 4. MVP feature list

### Feature 1 — Authentication

#### Requirement

The app must have a basic authentication system.

#### MVP implementation

Use Django built-in authentication.

Required pages:

- Login
- Logout

For the MVP, registration is optional. A superuser or pre-created operator account is enough.

#### Acceptance criteria

- Unauthenticated users cannot access campaign pages.
- Authenticated users can access upload, preview, detail, and export pages.
- Logout works correctly.

---

### Feature 2 — Campaign creation

#### Requirement

The operator must be able to create a WhatsApp campaign by uploading an Excel file and entering message/template settings.

#### Required fields

Campaign form must include:

- `name`
- `template_name`
- `language_code`
- `excel_file`
- `dry_run`

#### Field details

| Field | Type | Required | Notes |
|---|---|---:|---|
| `name` | text | Yes | Human-readable campaign name |
| `template_name` | text | Yes | WhatsApp approved template name |
| `language_code` | text | Yes | Default: `en_US` |
| `excel_file` | file | Yes | Must be `.xlsx` |
| `dry_run` | boolean | No | If true, do not call WhatsApp API |

#### Acceptance criteria

- Operator can create a campaign from a web form.
- Only `.xlsx` files are accepted.
- Invalid file types show a clear validation error.
- Created campaign is stored in the database.
- Uploaded file is stored under a campaign upload directory.

---

### Feature 3 — Excel parsing

#### Requirement

The system must parse recipient data from the uploaded Excel file.

#### Required Excel format

The first row must be the header row.

Minimum required columns:

| Column | Required | Description |
|---|---:|---|
| `phone` | Yes | Recipient phone number in international format |
| `name` | No | Recipient name |

Optional dynamic columns:

Any other columns are treated as template variables.

Example:

| phone | name | order_id | appointment_date |
|---|---|---|---|
| 84901234567 | John | ORD001 | 2026-06-10 |
| 84987654321 | Anna | ORD002 | 2026-06-12 |

The system should convert dynamic values into a JSON object per recipient:

```json
{
  "order_id": "ORD001",
  "appointment_date": "2026-06-10"
}
```

#### Parsing behavior

- Read the first worksheet only.
- Use the first row as headers.
- Trim whitespace from header names.
- Normalize header names to lowercase snake_case.
- Ignore fully empty rows.
- Keep row number for error reporting.

#### Acceptance criteria

- Valid Excel files create `Recipient` records.
- Missing required `phone` column rejects the campaign import.
- Empty rows are skipped.
- Each recipient stores the original Excel row number.
- Dynamic columns are stored in `Recipient.params`.

---

### Feature 4 — Data validation

#### Requirement

The system must validate each recipient row before sending.

#### Validation rules

| Rule | Behavior |
|---|---|
| Missing phone | Mark recipient as `invalid` |
| Phone contains spaces | Remove spaces before storing |
| Phone starts with `+` | Remove `+` before storing |
| Phone contains non-digit characters after normalization | Mark as `invalid` |
| Duplicate phone in same campaign | Mark duplicate as `invalid` or `duplicate` |
| Missing template variables | Mark as `invalid` only if required variables are configured |

#### Phone normalization examples

| Input | Output |
|---|---|
| `+84901234567` | `84901234567` |
| `84 901 234 567` | `84901234567` |
| `(849)123` | invalid |

#### Acceptance criteria

- Invalid rows are not sent.
- Invalid reason is stored in `Recipient.error_message`.
- Valid rows are marked as `pending` after import.
- UI shows valid and invalid row counts.

---

### Feature 5 — Campaign preview

#### Requirement

Before sending, the operator must see a preview of imported recipients.

#### Preview page must show

- Campaign name
- Template name
- Language code
- Total rows
- Valid rows
- Invalid rows
- Recipient table

Recipient table columns:

- Row number
- Phone
- Name
- Params preview
- Status
- Error message

#### Acceptance criteria

- Operator can review recipients before sending.
- Invalid rows are visibly marked.
- Start button is disabled if there are no valid recipients.

---

### Feature 6 — Send WhatsApp template messages

#### Requirement

The system must send WhatsApp template messages to valid recipients.

#### API approach

Use the official WhatsApp Cloud API.

The sender service should send template messages using:

- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `template_name`
- `language_code`
- recipient phone number
- template body parameters

#### Template parameters

For MVP, body parameters should be built from recipient data.

Recommended default parameter order:

1. `name`
2. all values from `params` in column order

Example payload concept:

```json
{
  "messaging_product": "whatsapp",
  "to": "84901234567",
  "type": "template",
  "template": {
    "name": "hello_world",
    "language": {
      "code": "en_US"
    },
    "components": [
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "John"},
          {"type": "text", "text": "ORD001"}
        ]
      }
    ]
  }
}
```

#### Send behavior

For each valid recipient:

1. Mark status as `sending`.
2. Call WhatsApp API.
3. If API returns success:
   - Store WhatsApp message ID.
   - Mark status as `sent`.
   - Store raw API response in log.
4. If API returns error:
   - Mark status as `failed`.
   - Store error message.
   - Store raw error response in log.

#### Acceptance criteria

- Valid recipients can be sent.
- Invalid recipients are skipped.
- API success stores WhatsApp message ID.
- API failure stores clear error information.
- UI shows updated statuses.

---

### Feature 7 — Dry run mode

#### Requirement

The app must support dry run mode for local demo and testing without calling WhatsApp API.

#### Behavior

If campaign `dry_run = true`:

- Do not call Meta API.
- Generate fake WhatsApp message ID.
- Mark valid recipients as `sent`.
- Create message logs with fake response payload.

Example fake response:

```json
{
  "dry_run": true,
  "messages": [
    {
      "id": "dry_run_123456"
    }
  ]
}
```

#### Acceptance criteria

- Developer can demo full flow without API credentials.
- Dry run logs are clearly marked.
- Dry run mode never makes real external API calls.

---

### Feature 8 — Message logs

#### Requirement

Every send attempt must create a log.

#### Log data

`MessageLog` should store:

- recipient
- direction: `outbound` or `webhook`
- event_type
- status
- request_payload
- response_payload
- error_message
- created_at

#### Acceptance criteria

- Every send attempt has a log record.
- Logs can be viewed from campaign detail page or Django admin.
- Failed sends include useful debugging information.

---

### Feature 9 — WhatsApp webhook verification

#### Requirement

The app must expose a webhook endpoint for WhatsApp webhook verification.

#### Endpoint

```txt
GET /webhooks/whatsapp/
```

#### Expected query params

- `hub.mode`
- `hub.verify_token`
- `hub.challenge`

#### Behavior

If `hub.verify_token` matches `WHATSAPP_VERIFY_TOKEN`, return `hub.challenge`.

If token does not match, return HTTP 403.

#### Acceptance criteria

- Meta webhook verification can succeed.
- Invalid verify token returns forbidden.

---

### Feature 10 — WhatsApp webhook status update

#### Requirement

The app must receive WhatsApp message status webhook events and update recipient status.

#### Endpoint

```txt
POST /webhooks/whatsapp/
```

#### Status mapping

| WhatsApp status | App recipient status |
|---|---|
| `sent` | `sent` |
| `delivered` | `delivered` |
| `read` | `read` |
| `failed` | `failed` |

#### Behavior

- Parse incoming JSON payload.
- Find recipient by WhatsApp message ID.
- Update recipient status.
- Create `MessageLog` with raw webhook payload.
- Return HTTP 200 quickly.

#### Acceptance criteria

- Valid webhook updates recipient status.
- Unknown message ID does not crash the app.
- Webhook payload is logged.
- Endpoint always returns a safe response.

---

### Feature 11 — Campaign detail page

#### Requirement

The campaign detail page must show campaign progress and recipient statuses.

#### Page must show

- Campaign name
- Campaign status
- Template name
- Language code
- Dry run flag
- Total recipients
- Pending count
- Sending count
- Sent count
- Delivered count
- Read count
- Failed count
- Invalid count
- Recipient table

#### Recipient table columns

- Row number
- Phone
- Name
- Status
- WhatsApp message ID
- Error message
- Last updated time

#### Acceptance criteria

- Operator can see current campaign state.
- Status counts are accurate.
- Failed rows are easy to inspect.

---

### Feature 12 — Export campaign result

#### Requirement

The operator must be able to export campaign results.

#### Format

MVP can use CSV. Excel export is optional.

Required columns:

- row_number
- phone
- name
- status
- whatsapp_message_id
- error_message
- params
- created_at
- updated_at

#### Acceptance criteria

- Export button downloads campaign result.
- Export includes all recipients.
- Export includes failed and invalid rows.

---

## 5. Database models

### 5.1 Campaign

Fields:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID or BigAutoField | Primary key |
| `name` | CharField | Required |
| `template_name` | CharField | Required |
| `language_code` | CharField | Default `en_US` |
| `excel_file` | FileField | Uploaded Excel file |
| `status` | CharField | `draft`, `ready`, `sending`, `completed`, `completed_with_errors`, `failed` |
| `dry_run` | BooleanField | Default true for local demo |
| `created_by` | ForeignKey User | Optional but recommended |
| `created_at` | DateTimeField | Auto now add |
| `updated_at` | DateTimeField | Auto now |

### 5.2 Recipient

Fields:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID or BigAutoField | Primary key |
| `campaign` | ForeignKey Campaign | Required |
| `row_number` | PositiveIntegerField | Excel row number |
| `phone` | CharField | Normalized phone |
| `name` | CharField | Optional |
| `params` | JSONField | Dynamic Excel columns |
| `status` | CharField | See status list below |
| `whatsapp_message_id` | CharField | Nullable |
| `error_message` | TextField | Optional |
| `created_at` | DateTimeField | Auto now add |
| `updated_at` | DateTimeField | Auto now |
| `sent_at` | DateTimeField | Nullable |

Recipient statuses:

- `pending`
- `invalid`
- `duplicate`
- `sending`
- `sent`
- `delivered`
- `read`
- `failed`

### 5.3 MessageLog

Fields:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID or BigAutoField | Primary key |
| `campaign` | ForeignKey Campaign | Required |
| `recipient` | ForeignKey Recipient | Nullable for unknown webhook |
| `direction` | CharField | `outbound`, `webhook` |
| `event_type` | CharField | Example: `send_template`, `status_update` |
| `status` | CharField | Optional status |
| `request_payload` | JSONField | Nullable |
| `response_payload` | JSONField | Nullable |
| `error_message` | TextField | Optional |
| `created_at` | DateTimeField | Auto now add |

---

## 6. Required pages and routes

### Web pages

| Method | Path | Description |
|---|---|---|
| GET | `/` | Redirect to campaign list |
| GET | `/campaigns/` | List campaigns |
| GET/POST | `/campaigns/new/` | Create campaign and upload Excel |
| GET | `/campaigns/<id>/preview/` | Preview imported recipients |
| POST | `/campaigns/<id>/send/` | Start sending campaign |
| GET | `/campaigns/<id>/` | Campaign detail and status |
| GET | `/campaigns/<id>/export/` | Export result CSV |
| GET/POST | `/webhooks/whatsapp/` | WhatsApp webhook verify/status update |

### Admin

Django admin should support:

- Campaign list/search/filter
- Recipient list/search/filter
- MessageLog list/search/filter

---

## 7. Environment variables

Required `.env` values:

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

---

## 8. Error handling requirements

The app must handle these cases gracefully:

- Missing Excel file
- Wrong file extension
- Corrupted Excel file
- Missing required `phone` column
- Empty Excel file
- API timeout
- API authentication error
- API validation error
- Webhook payload with unknown message ID
- Duplicate recipient phone numbers

Never crash the page with a raw traceback in normal user flow.

---

## 9. Security requirements

- Store WhatsApp access token only in environment variables.
- Never commit `.env` to Git.
- Validate file extension and file size before parsing.
- Do not expose raw access token in UI, logs, or export files.
- Webhook verification token must be compared with environment variable.
- Require login for campaign pages.
- CSRF protection must remain enabled for normal web forms.

---

## 10. Non-goals for MVP

Do not build these in MVP unless explicitly requested later:

- Multi-tenant SaaS billing
- Full user/team management
- Advanced dashboard charts
- Message template builder
- WhatsApp template approval management
- Complex scheduling
- Celery/Redis queue
- Role-based access control
- Payment integration
- AI-generated messages

---

## 11. Optional version 2 features

After MVP works, these can be added:

- Celery + Redis background sending
- Retry failed messages
- Rate limiting
- Campaign scheduling
- PostgreSQL production setup
- Docker Compose
- Better dashboard UI
- Excel export using openpyxl
- Template parameter mapping UI
- Multiple WhatsApp phone numbers

---

## 12. Done definition

The MVP is considered done when:

- A developer can run the app locally.
- An operator can log in.
- An operator can upload a valid Excel file.
- The app parses and validates recipients.
- The app shows a preview page.
- The app can run in dry run mode.
- The app can send real WhatsApp template messages when credentials are configured.
- Send results are stored per recipient.
- Webhook verification endpoint works.
- Webhook status update endpoint can update recipient status.
- Operator can export campaign result.
- README explains setup, environment variables, and demo flow.
