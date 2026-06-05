from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class CampaignStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    READY = "ready", "Ready"
    SENDING = "sending", "Sending"
    COMPLETED = "completed", "Completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors", "Completed with Errors"
    FAILED = "failed", "Failed"


class RecipientStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    INVALID = "invalid", "Invalid"
    DUPLICATE = "duplicate", "Duplicate"
    SENDING = "sending", "Sending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    READ = "read", "Read"
    FAILED = "failed", "Failed"


class MessageDirection(models.TextChoices):
    OUTBOUND = "outbound", "Outbound"
    WEBHOOK = "webhook", "Webhook"


class Campaign(models.Model):
    name = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)
    language_code = models.CharField(max_length=20, default="en_US")
    excel_file = models.FileField(upload_to="campaigns/uploads/%Y/%m/")
    status = models.CharField(
        max_length=30,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
    )
    dry_run = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class Recipient(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    row_number = models.PositiveIntegerField()
    phone = models.CharField(max_length=30)
    name = models.CharField(max_length=255, blank=True, default="")
    params = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=RecipientStatus.choices,
        default=RecipientStatus.PENDING,
    )
    whatsapp_message_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["row_number"]

    def __str__(self) -> str:
        return f"Row {self.row_number} — {self.phone} ({self.status})"


class MessageLog(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="message_logs",
        null=True,
        blank=True,
    )
    recipient = models.ForeignKey(
        Recipient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_logs",
    )
    direction = models.CharField(
        max_length=10,
        choices=MessageDirection.choices,
        default=MessageDirection.OUTBOUND,
    )
    event_type = models.CharField(max_length=50, blank=True, default="")
    status = models.CharField(max_length=20, blank=True, default="")
    request_payload = models.JSONField(default=dict, blank=True, null=True)
    response_payload = models.JSONField(default=dict, blank=True, null=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        recipient_str = str(self.recipient) if self.recipient else "unknown"
        return f"{self.direction} / {self.event_type} — {recipient_str}"
