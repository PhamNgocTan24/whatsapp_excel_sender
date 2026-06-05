---
inclusion: manual
---

# Environment & Security Convention

## Environment Variables

Use `python-dotenv`. Required `.env` values:

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

## Security Requirements

- Store WhatsApp access token only in environment variables.
- Validate file extension and file size before parsing.
- Do not expose raw access token in UI, logs, or export files.
- Webhook verify token compared with env var.
- Require login for campaign pages.
- CSRF protection must remain enabled.

## Dependencies

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
