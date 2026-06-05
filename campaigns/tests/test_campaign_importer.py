import os
import tempfile
from unittest.mock import patch, PropertyMock

import openpyxl
import pytest

from campaigns.models import Campaign, CampaignStatus, Recipient, RecipientStatus
from campaigns.services.campaign_importer import import_campaign_recipients


def _make_xlsx(rows: list[list]) -> str:
    """Write rows to a temp .xlsx and return its absolute path."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    tmp.close()
    return tmp.name


@pytest.fixture
def operator(django_user_model):
    return django_user_model.objects.create_user(username="importop", password="pass")


@pytest.fixture
def make_campaign(operator, tmp_path):
    """
    Factory fixture: call with xlsx rows → returns (campaign, xlsx_path).
    The fixture patches excel_file.path to bypass Django's MEDIA_ROOT restriction.
    """
    campaigns_created = []

    def _factory(rows):
        path = _make_xlsx(rows)
        c = Campaign.objects.create(
            name="Import Test",
            template_name="hello_world",
            language_code="en_US",
            excel_file="dummy.xlsx",   # placeholder — path is patched below
            dry_run=True,
            created_by=operator,
            status=CampaignStatus.DRAFT,
        )
        campaigns_created.append((c, path))
        return c, path

    yield _factory

    for _, path in campaigns_created:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def _run_import(campaign, path):
    """Run import with excel_file.path patched to the real temp file."""
    with patch.object(
        type(campaign.excel_file), "path", new_callable=PropertyMock, return_value=path
    ):
        return import_campaign_recipients(campaign)


# --- Tests ---

@pytest.mark.django_db
def test_import_creates_recipients(make_campaign):
    campaign, path = make_campaign([
        ["phone", "name", "order_id"],
        ["84901234567", "Alice", "ORD001"],
        ["84987654321", "Bob", "ORD002"],
    ])
    result = _run_import(campaign, path)
    assert result.total == 2
    assert result.valid == 2
    assert result.invalid == 0
    assert Recipient.objects.filter(campaign=campaign).count() == 2


@pytest.mark.django_db
def test_import_marks_campaign_ready(make_campaign):
    campaign, path = make_campaign([
        ["phone", "name"],
        ["84901234567", "Alice"],
    ])
    _run_import(campaign, path)
    campaign.refresh_from_db()
    assert campaign.status == CampaignStatus.READY


@pytest.mark.django_db
def test_import_marks_invalid_rows(make_campaign):
    campaign, path = make_campaign([
        ["phone", "name"],
        ["84901234567", "Alice"],
        ["", "No Phone"],
        ["(bad)phone", "Bad"],
    ])
    result = _run_import(campaign, path)
    assert result.valid == 1
    assert result.invalid == 2


@pytest.mark.django_db
def test_import_marks_duplicate_rows(make_campaign):
    campaign, path = make_campaign([
        ["phone", "name"],
        ["84901234567", "Alice"],
        ["84901234567", "Alice Again"],
    ])
    result = _run_import(campaign, path)
    assert result.valid == 1
    assert result.duplicate == 1


@pytest.mark.django_db
def test_import_stores_params(make_campaign):
    campaign, path = make_campaign([
        ["phone", "name", "order_id", "date"],
        ["84901234567", "Alice", "ORD001", "2026-06-10"],
    ])
    _run_import(campaign, path)
    recipient = Recipient.objects.get(campaign=campaign)
    assert recipient.params == {"order_id": "ORD001", "date": "2026-06-10"}


@pytest.mark.django_db
def test_import_clears_previous_recipients(make_campaign):
    campaign, path1 = make_campaign([
        ["phone", "name"],
        ["84901234567", "Alice"],
    ])
    _run_import(campaign, path1)
    assert Recipient.objects.filter(campaign=campaign).count() == 1

    # Re-import with different data
    path2 = _make_xlsx([
        ["phone", "name"],
        ["84900000001", "NewAlice"],
        ["84900000002", "NewBob"],
    ])
    try:
        _run_import(campaign, path2)
    finally:
        os.unlink(path2)

    assert Recipient.objects.filter(campaign=campaign).count() == 2
    assert not Recipient.objects.filter(campaign=campaign, phone="84901234567").exists()


@pytest.mark.django_db
def test_import_fails_gracefully_on_missing_phone_column(make_campaign):
    campaign, path = make_campaign([
        ["name", "order_id"],
        ["Alice", "ORD001"],
    ])
    result = _run_import(campaign, path)
    assert result.error_message != ""
    campaign.refresh_from_db()
    assert campaign.status == CampaignStatus.FAILED


@pytest.mark.django_db
def test_import_fails_gracefully_on_empty_file(make_campaign):
    campaign, path = make_campaign([])
    result = _run_import(campaign, path)
    assert result.error_message != ""
    campaign.refresh_from_db()
    assert campaign.status == CampaignStatus.FAILED
