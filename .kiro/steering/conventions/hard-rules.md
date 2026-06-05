---
inclusion: manual
---

# Hard Rules for AI Code Generation

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

## Reference Docs

- Django file uploads: https://docs.djangoproject.com/en/6.0/topics/http/file-uploads/
- Django uploaded files: https://docs.djangoproject.com/en/6.0/ref/files/uploads/
- Django coding style: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/
- openpyxl: https://openpyxl.readthedocs.io/
- WhatsApp Cloud API: https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started
- WhatsApp webhooks: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview/
