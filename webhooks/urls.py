from django.urls import path

from . import views

app_name = "webhooks"

urlpatterns = [
    path("whatsapp/", views.whatsapp_webhook, name="whatsapp"),
]
