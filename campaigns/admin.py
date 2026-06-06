from django.contrib import admin

from .models import Campaign, MessageLog, Recipient


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "template_name",
        "language_code",
        "status",
        "dry_run",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "dry_run", "language_code")
    search_fields = ("name", "template_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = (
        "row_number",
        "phone",
        "name",
        "status",
        "whatsapp_message_id",
        "campaign",
        "updated_at",
    )
    list_filter = ("status", "campaign")
    search_fields = ("phone", "name", "whatsapp_message_id")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("campaign", "row_number")


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = (
        "direction",
        "event_type",
        "status",
        "campaign",
        "recipient",
        "created_at",
    )
    list_filter = ("direction", "event_type", "status", "campaign")
    search_fields = ("event_type", "error_message")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
