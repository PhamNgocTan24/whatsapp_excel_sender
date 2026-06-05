# WhatsApp Excel Sender

A Django web application that lets an operator upload an Excel file, preview recipients, send personalized WhatsApp template messages via the official WhatsApp Cloud API, and track delivery status per row.

---

## Features

- Upload `.xlsx` file with customer phone numbers and message variables
- Auto-parse and validate recipients (phone normalization, duplicate detection)
- Preview recipients before sending with valid/invalid/duplicate counts
- Send WhatsApp template messages via Meta Cloud API
- Dry run mode — full flow demo without real API calls
- Real-time status tracking: pending → sent → delivered → read → failed
- WhatsApp webhook verification and status update handling
- Export campaign results to CSV
- Django admin for full data inspection

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, Django 6.x |
| Database | SQLite (dev), PostgreSQL (prod) |
| Excel | openpyxl |
| HTTP client | requests |
| Frontend | Django Templates + Bootstrap 5 CDN |
| Testing | pytest, pytest-django |
| Code quality | ruff, black, isort |

---

## Local Setup

### 1. Clone the repository

```bash
git clone git@github.com:PhamNgocTan24/whatsapp_excel_sender.git
cd whatsapp_excel_sender
```

### 2. Install uv (if not installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 3. Create virtual environment and install dependencies

```bash
uv sync
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values (see [Environment Variables](#environment-variables) below).

### 5. Run migrations

```bash
uv run python manage.py migrate
```

### 6. Create a superuser

```bash
uv run python manage.py createsuperuser
```

Or create one non-interactively:

```bash
uv run python manage.py createsuperuser --username admin --email admin@example.com --noinput
uv run python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u = U.objects.get(username='admin')
u.set_password('admin123')
u.save()
"
```

### 7. Start the development server

```bash
uv run python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3

# WhatsApp Cloud API credentials
WHATSAPP_ACCESS_TOKEN=        # From Meta Developer Console
WHATSAPP_PHONE_NUMBER_ID=     # From Meta Developer Console
WHATSAPP_VERIFY_TOKEN=local-verify-token   # Any secret string you choose
WHATSAPP_API_VERSION=v20.0

# Set to True for demo/dev without real API calls
DEFAULT_DRY_RUN=True
```

---

## Demo Flow (Dry Run)

1. Log in at http://127.0.0.1:8000/accounts/login/
2. Go to **Campaigns → New Campaign**
3. Fill in:
   - **Campaign Name**: anything
   - **Template Name**: `hello_world`
   - **Language Code**: `en_US`
   - **Excel File**: upload `sample_recipients.xlsx` (included in project root)
   - **Dry Run**: ✅ checked
4. Click **Upload & Preview** — see parsed recipients with valid/invalid/duplicate breakdown
5. Click **Run Dry Send** — all valid recipients get status `Sent` with a `dry_run_X` message ID
6. Click **Export CSV** to download the result
7. Check **Django Admin** at `/admin` for full data inspection

---

## Excel File Format

First row must be headers. Required column: `phone`.

| phone | name | order_id | appointment_date |
|-------|------|----------|-----------------|
| 84901234567 | Nguyen Van A | ORD001 | 2026-06-10 |
| +84987654321 | Tran Thi B | ORD002 | 2026-06-12 |

**Phone normalization rules:**
- `+84901234567` → `84901234567` ✅
- `84 901 234 567` → `84901234567` ✅
- `(849)abc123` → invalid ❌

All columns beyond `phone` and `name` become template body parameters.

---

## WhatsApp Cloud API Setup

1. Go to https://developers.facebook.com/apps
2. Create App → Business → add **WhatsApp** product
3. In **WhatsApp → API Setup**:
   - Copy **Temporary Access Token** → `WHATSAPP_ACCESS_TOKEN`
   - Copy **Phone Number ID** → `WHATSAPP_PHONE_NUMBER_ID`
   - Add your test phone number to the whitelist
4. Set `DEFAULT_DRY_RUN=False` in `.env`
5. Use template name `hello_world` (pre-approved by Meta, no params needed)

---

## Webhook Setup

The app exposes a webhook endpoint at `/webhooks/whatsapp/`.

### Verification

Meta will send a GET request to verify your endpoint:

```
GET /webhooks/whatsapp/?hub.mode=subscribe&hub.verify_token=<your_token>&hub.challenge=<challenge>
```

The app compares `hub.verify_token` with `WHATSAPP_VERIFY_TOKEN` in your `.env`.

To test locally with ngrok:

```bash
ngrok http 8000
```

Then configure in Meta Developer Console:
- **Callback URL**: `https://<your-ngrok-id>.ngrok.io/webhooks/whatsapp/`
- **Verify Token**: value from `WHATSAPP_VERIFY_TOKEN` in `.env`

### Status Updates

When a message is delivered, read, or fails, Meta sends a POST to the same endpoint. The app automatically updates the recipient status.

To test manually with curl:

```bash
# Test verification
curl "http://127.0.0.1:8000/webhooks/whatsapp/?hub.mode=subscribe&hub.verify_token=local-verify-token&hub.challenge=test123"

# Simulate a delivered status update (replace dry_run_1 with a real whatsapp_message_id)
curl -X POST http://127.0.0.1:8000/webhooks/whatsapp/ \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "123",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "statuses": [{
            "id": "dry_run_1",
            "status": "delivered",
            "timestamp": "1234567890",
            "recipient_id": "84901234567"
          }]
        },
        "field": "messages"
      }]
    }]
  }'
```

---

## Running Tests

```bash
uv run pytest
```

With verbose output:

```bash
uv run pytest -v
```

Run a specific test file:

```bash
uv run pytest campaigns/tests/test_excel_parser.py -v
```

---

## Code Quality

```bash
uv run ruff check .
uv run black .
uv run isort .
```

---

## Project Structure

```
whatsapp_excel_sender/
├── config/                  → Django settings, urls, wsgi
├── campaigns/               → Main app
│   ├── models.py            → Campaign, Recipient, MessageLog
│   ├── forms.py             → CampaignCreateForm
│   ├── views.py             → Function-based views
│   ├── selectors.py         → Read-only DB queries
│   ├── services/
│   │   ├── phone_normalizer.py   → Phone validation & normalization
│   │   ├── excel_parser.py       → Parse .xlsx to ParsedRecipientRow
│   │   ├── campaign_importer.py  → Save parsed rows to DB
│   │   ├── campaign_sender.py    → Send messages, dry run logic
│   │   ├── campaign_exporter.py  → CSV export
│   │   └── whatsapp_client.py    → WhatsApp Cloud API client
│   └── tests/
├── webhooks/                → Webhook app
│   ├── views.py             → GET verify + POST receive
│   └── services/
│       └── whatsapp_webhook_handler.py  → Parse & apply status updates
├── templates/               → base.html, login.html
├── sample_recipients.xlsx   → Sample file for demo
├── .env.example             → Environment variable template
└── README.md
```
