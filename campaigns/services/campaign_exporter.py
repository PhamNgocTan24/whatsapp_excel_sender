import csv
import io
import json

from ..models import Campaign, Recipient


# Required columns per spec
EXPORT_COLUMNS = [
    "row_number",
    "phone",
    "name",
    "status",
    "whatsapp_message_id",
    "error_message",
    "params",
    "created_at",
    "updated_at",
]


def export_campaign_csv(campaign: Campaign) -> str:
    """
    Export all recipients of a campaign to CSV string.

    Returns the CSV content as a UTF-8 string.
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()

    recipients = Recipient.objects.filter(campaign=campaign).order_by("row_number")

    for recipient in recipients:
        writer.writerow({
            "row_number": recipient.row_number,
            "phone": recipient.phone,
            "name": recipient.name,
            "status": recipient.status,
            "whatsapp_message_id": recipient.whatsapp_message_id or "",
            "error_message": recipient.error_message,
            "params": json.dumps(recipient.params, ensure_ascii=False) if recipient.params else "",
            "created_at": recipient.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": recipient.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return output.getvalue()
