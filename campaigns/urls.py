from django.urls import path

from . import views

app_name = "campaigns"

urlpatterns = [
    path("", views.campaign_list, name="list"),
    path("new/", views.campaign_create, name="create"),
    path("<int:campaign_id>/", views.campaign_detail, name="detail"),
    path("<int:campaign_id>/preview/", views.campaign_preview, name="preview"),
    path("<int:campaign_id>/send/", views.campaign_send, name="send"),
    path("<int:campaign_id>/export/", views.campaign_export, name="export"),
]
