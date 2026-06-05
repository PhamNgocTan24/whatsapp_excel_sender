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
            messages.success(request, f'Campaign "{campaign.name}" created. Review recipients below.')
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

    # Sending logic will be wired in Step 5
    messages.info(request, "Sending not yet implemented.")
    return redirect("campaigns:detail", campaign_id=campaign_id)


@login_required
def campaign_export(request, campaign_id):
    # Export logic will be wired in Step 6
    campaign = get_campaign_or_404(campaign_id)
    messages.info(request, "Export not yet implemented.")
    return redirect("campaigns:detail", campaign_id=campaign_id)
