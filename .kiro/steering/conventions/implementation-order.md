---
inclusion: manual
---

# Implementation Order

Build in this order:

## Step 1 — Project Setup
- Create Django project (`config/`).
- Create `campaigns` app.
- Create `webhooks` app.
- Add templates and static setup.
- Configure `.env` loading.

## Step 2 — Models and Admin
- Add `Campaign`, `Recipient`, `MessageLog` models.
- Register models in admin.
- Create migrations.

## Step 3 — Campaign Upload
- Add campaign form.
- Add upload view.
- Add campaign list and create pages.

## Step 4 — Excel Parser
- Add `excel_parser.py` and `phone_normalizer.py`.
- Parse uploaded file, create recipients.
- Show preview page.

## Step 5 — Sending Service
- Add `whatsapp_client.py` and dry run mode.
- Add `campaign_sender.py`.
- Add send button/action.
- Update recipient statuses, create message logs.

## Step 6 — Campaign Detail and Export
- Add campaign detail page with status counts.
- Add CSV export.

## Step 7 — Webhook
- Add webhook verification.
- Add webhook POST handler.
- Update recipient status from message ID.
- Log webhook payload.

## Step 8 — Tests and README
- Add unit tests.
- Add README with setup & demo instructions.
- Add sample Excel file.
