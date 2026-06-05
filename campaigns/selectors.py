from django.db.models import Count, Q

from .models import Campaign, Recipient, RecipientStatus


def get_all_campaigns():
    """Return all campaigns ordered by newest first."""
    return Campaign.objects.select_related("created_by").all()


def get_campaign_or_404(campaign_id: int) -> Campaign:
    from django.shortcuts import get_object_or_404
    return get_object_or_404(Campaign, id=campaign_id)


def get_campaign_recipients(campaign: Campaign):
    """Return all recipients for a campaign ordered by row number."""
    return Recipient.objects.filter(campaign=campaign).order_by("row_number")


def get_status_counts(campaign: Campaign) -> dict:
    """Return a dict of status → count for a campaign."""
    qs = (
        Recipient.objects.filter(campaign=campaign)
        .values("status")
        .annotate(count=Count("id"))
    )
    counts = {row["status"]: row["count"] for row in qs}

    # Ensure all statuses are represented
    for status in RecipientStatus.values:
        counts.setdefault(status, 0)

    counts["total"] = sum(counts[s] for s in RecipientStatus.values)
    counts["valid"] = counts.get(RecipientStatus.PENDING, 0)

    return counts
