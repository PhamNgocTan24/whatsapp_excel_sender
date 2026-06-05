from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CampaignCreateForm
from .models import CampaignStatus
from .selectors import (
    get_all_campaigns,
    get_campaign_or_404,
    get_campaign_recipients,
    get_status_counts,
)
from .services.campaign_importer import import_campaign_recipients
from .services.campaign_sender import send_campaign


@login_required
def campaign_list(request):
    campaigns = get_all_campaigns()
    return render(request, "campaigns/campaign_list.html", {"campaigns": campaigns})


@login_required
def campaign_create(request):
    if request.method == "POST":
        form = CampaignCreateForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            campaign.status = CampaignStatus.DRAFT
            campaign.save()

            # Parse Excel and create recipients
            result = import_campaign_recipients(campaign)

            if result.error_message:
                messages.error(request, f"Import failed: {result.error_message}")
            else:
                messages.success(
                    request,
                    f'Campaign "{campaign.name}" imported: '
                    f'{result.valid} valid, {result.invalid} invalid, {result.duplicate} duplicate.'
                )

            return redirect("campaigns:preview", campaign_id=campaign.id)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        from django.conf import settings
        initial_dry_run = getattr(settings, "DEFAULT_DRY_RUN", True)
        form = CampaignCreateForm(initial={"dry_run": initial_dry_run, "language_code": "en_US"})

    return render(request, "campaigns/campaign_form.html", {"form": form})


@login_required
def campaign_preview(request, campaign_id):
    campaign = get_campaign_or_404(campaign_id)
    recipients = get_campaign_recipients(campaign)
    counts = get_status_counts(campaign)
    return render(request, "campaigns/campaign_preview.html", {
        "campaign": campaign,
        "recipients": recipients,
        "counts": counts,
    })


@login_required
def campaign_detail(request, campaign_id):
    campaign = get_campaign_or_404(campaign_id)
    recipients = get_campaign_recipients(campaign)
    counts = get_status_counts(campaign)
    return render(request, "campaigns/campaign_detail.html", {
        "campaign": campaign,
        "recipients": recipients,
        "counts": counts,
    })


@login_required
def campaign_send(request, campaign_id):
    if request.method != "POST":
        return redirect("campaigns:detail", campaign_id=campaign_id)

    campaign = get_campaign_or_404(campaign_id)
    result = send_campaign(campaign.id)

    if result.total == 0:
        messages.warning(request, "No valid recipients to send.")
    elif result.failed == 0:
        messages.success(
            request,
            f"{'Dry run' if campaign.dry_run else 'Send'} complete: "
            f"{result.sent} sent successfully."
        )
    else:
        messages.warning(
            request,
            f"Send complete: {result.sent} sent, {result.failed} failed."
        )

    return redirect("campaigns:detail", campaign_id=campaign_id)


@login_required
def campaign_export(request, campaign_id):
    # Export logic will be wired in Step 6
    campaign = get_campaign_or_404(campaign_id)
    messages.info(request, "Export not yet implemented.")
    return redirect("campaigns:detail", campaign_id=campaign_id)
