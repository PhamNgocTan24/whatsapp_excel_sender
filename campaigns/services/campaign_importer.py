from dataclasses import dataclass

from django.db import transaction

from ..models import Campaign, CampaignStatus, Recipient, RecipientStatus
from .excel_parser import ExcelParseError, parse_excel_file


@dataclass
class ImportResult:
    total: int
    valid: int
    invalid: int
    duplicate: int
    error_message: str = ""


def import_campaign_recipients(campaign: Campaign) -> ImportResult:
    """
    Parse the campaign's Excel file and create Recipient records.

    - Deletes any previously imported recipients for this campaign first.
    - Marks campaign status as READY on success, FAILED on parse error.

    Returns an ImportResult summary.
    """
    try:
        parsed_rows = parse_excel_file(campaign.excel_file.path)
    except ExcelParseError as exc:
        campaign.status = CampaignStatus.FAILED
        campaign.save(update_fields=["status", "updated_at"])
        return ImportResult(total=0, valid=0, invalid=0, duplicate=0, error_message=str(exc))

    if not parsed_rows:
        campaign.status = CampaignStatus.FAILED
        campaign.save(update_fields=["status", "updated_at"])
        return ImportResult(
            total=0,
            valid=0,
            invalid=0,
            duplicate=0,
            error_message="No data rows found in the Excel file.",
        )

    recipients_to_create: list[Recipient] = []
    valid_count = 0
    invalid_count = 0
    duplicate_count = 0

    for row in parsed_rows:
        if not row.is_valid:
            # Distinguish duplicate from other invalid
            is_duplicate = any("Duplicate" in e or "duplicate" in e for e in row.errors)
            if is_duplicate:
                status = RecipientStatus.DUPLICATE
                duplicate_count += 1
            else:
                status = RecipientStatus.INVALID
                invalid_count += 1
        else:
            status = RecipientStatus.PENDING
            valid_count += 1

        recipients_to_create.append(
            Recipient(
                campaign=campaign,
                row_number=row.row_number,
                phone=row.phone,
                name=row.name,
                params=row.params,
                status=status,
                error_message="; ".join(row.errors) if row.errors else "",
            )
        )

    with transaction.atomic():
        # Clear previous import if any
        Recipient.objects.filter(campaign=campaign).delete()

        Recipient.objects.bulk_create(recipients_to_create)

        campaign.status = CampaignStatus.READY
        campaign.save(update_fields=["status", "updated_at"])

    return ImportResult(
        total=len(parsed_rows),
        valid=valid_count,
        invalid=invalid_count,
        duplicate=duplicate_count,
    )
