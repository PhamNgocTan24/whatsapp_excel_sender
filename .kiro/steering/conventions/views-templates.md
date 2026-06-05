---
inclusion: manual
---

# Views & Templates Convention

## View Style

For MVP, prefer function-based views:
```python
@login_required
def campaign_list(request):
    ...
```

## Messages Framework

Use Django messages for user feedback:
```python
messages.success(request, "Campaign created successfully.")
messages.error(request, "Excel file is invalid.")
```

## Redirect After POST

Always redirect after successful POST (PRG pattern):
```
POST -> process -> redirect -> GET
```

## URL Naming

Use app namespaces:
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

## Template Convention

All pages extend `templates/base.html`.

UI: Bootstrap 5 via CDN. Keep it simple:
- Navbar, Container, Cards, Tables
- Badges for statuses, Buttons for actions

### Status Badge Styles

| Status | Bootstrap class |
|--------|----------------|
| pending | `bg-secondary` |
| invalid | `bg-warning text-dark` |
| duplicate | `bg-warning text-dark` |
| sending | `bg-info text-dark` |
| sent | `bg-primary` |
| delivered | `bg-success` |
| read | `bg-success` |
| failed | `bg-danger` |
