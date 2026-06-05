from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def campaign_list(request):
    return render(request, "campaigns/campaign_list.html")


@login_required
def campaign_create(request):
    return render(request, "campaigns/campaign_form.html")


@login_required
def campaign_detail(request, campaign_id):
    return render(request, "campaigns/campaign_detail.html")


@login_required
def campaign_preview(request, campaign_id):
    return render(request, "campaigns/campaign_preview.html")


@login_required
def campaign_send(request, campaign_id):
    return render(request, "campaigns/campaign_detail.html")


@login_required
def campaign_export(request, campaign_id):
    from django.http import HttpResponse
    return HttpResponse("export placeholder")
