# WhatsApp Excel Sender — AI Coding Guide

## Project Overview

Django MVP web app: upload Excel → parse recipients → send WhatsApp template messages → track status.

## Tech Stack Summary

- Python 3.12+ / Django 5.x–6.x
- SQLite (MVP), PostgreSQL (production)
- openpyxl, requests, python-dotenv
- Django Templates + Bootstrap 5 CDN
- pytest, ruff, black, isort
- No Celery, no React/Vue for MVP

## Project Structure

```
whatsapp_excel_sender/
├── manage.py
├── config/          → Django project settings, urls, wsgi, asgi
├── campaigns/       → Campaign CRUD, Excel upload/parse, send, export
│   ├── services/    → excel_parser, phone_normalizer, whatsapp_client, campaign_sender
│   ├── selectors.py → Read-only queries
│   ├── forms.py
│   ├── views.py
│   ├── models.py
│   └── templates/campaigns/
├── webhooks/        → WhatsApp webhook verify & status update
│   ├── services/    → whatsapp_webhook_handler
│   └── views.py
└── templates/       → base.html, registration/login.html
```

## Convention Files (refer as needed)

| Topic | File |
|-------|------|
| Layering & Architecture | #[[file:.kiro/steering/conventions/layering.md]] |
| Models & Database | #[[file:.kiro/steering/conventions/models.md]] |
| Services & Business Logic | #[[file:.kiro/steering/conventions/services.md]] |
| Views & Templates | #[[file:.kiro/steering/conventions/views-templates.md]] |
| Excel Parser | #[[file:.kiro/steering/conventions/excel-parser.md]] |
| WhatsApp API & Dry Run | #[[file:.kiro/steering/conventions/whatsapp-api.md]] |
| Webhook | #[[file:.kiro/steering/conventions/webhook.md]] |
| Testing | #[[file:.kiro/steering/conventions/testing.md]] |
| Naming & Git | #[[file:.kiro/steering/conventions/naming-git.md]] |
| Environment & Security | #[[file:.kiro/steering/conventions/environment-security.md]] |
| Implementation Order | #[[file:.kiro/steering/conventions/implementation-order.md]] |
| Hard Rules | #[[file:.kiro/steering/conventions/hard-rules.md]] |

## Hard Rules (always active)

1. Do not put business logic in views.
2. Do not call WhatsApp API from views.
3. Do not hardcode credentials.
4. Do not skip dry run mode.
5. Every send attempt must create a MessageLog.
6. Invalid recipients must not be sent.
7. Every external API call must have timeout.
8. Use service layer for business logic.
