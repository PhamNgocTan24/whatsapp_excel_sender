import os
import tempfile

import openpyxl
import pytest

from campaigns.services.excel_parser import ExcelParseError, parse_excel_file


def _make_xlsx(rows: list[list]) -> str:
    """Create a temp .xlsx file with given rows, return file path."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    tmp.close()
    return tmp.name


# --- Valid cases ---


def test_valid_file_returns_rows():
    path = _make_xlsx(
        [
            ["phone", "name", "order_id"],
            ["84901234567", "Alice", "ORD001"],
            ["84987654321", "Bob", "ORD002"],
        ]
    )
    try:
        rows = parse_excel_file(path)
        assert len(rows) == 2
        assert rows[0].phone == "84901234567"
        assert rows[0].name == "Alice"
        assert rows[0].params == {"order_id": "ORD001"}
        assert rows[0].is_valid is True
    finally:
        os.unlink(path)


def test_phone_with_plus_is_normalized():
    path = _make_xlsx(
        [
            ["phone", "name"],
            ["+84901234567", "Alice"],
        ]
    )
    try:
        rows = parse_excel_file(path)
        assert rows[0].phone == "84901234567"
        assert rows[0].is_valid is True
    finally:
        os.unlink(path)


def test_phone_with_spaces_is_normalized():
    path = _make_xlsx(
        [
            ["phone", "name"],
            ["84 901 234 567", "Alice"],
        ]
    )
    try:
        rows = parse_excel_file(path)
        assert rows[0].phone == "84901234567"
        assert rows[0].is_valid is True
    finally:
        os.unlink(path)


def test_empty_rows_are_skipped():
    path = _make_xlsx(
        [
            ["phone", "name"],
            ["84901234567", "Alice"],
            [None, None],
            ["", ""],
            ["84987654321", "Bob"],
        ]
    )
    try:
        rows = parse_excel_file(path)
        assert len(rows) == 2
    finally:
        os.unlink(path)


def test_row_number_matches_excel_row():
    path = _make_xlsx(
        [
            ["phone", "name"],
            ["84901234567", "Alice"],  # Excel row 2
            ["84987654321", "Bob"],  # Excel row 3
        ]
    )
    try:
        rows = parse_excel_file(path)
        assert rows[0].row_number == 2
        assert rows[1].row_number == 3
    finally:
        os.unlink(path)


def test_headers_are_normalized():
    """Headers like 'Phone Number' normalize to 'phone_number', not 'phone' — should raise."""
    path = _make_xlsx(
        [
            ["Phone Number", " Appointment Date "],
            ["84901234567", "2026-06-10"],
        ]
    )
    try:
        with pytest.raises(ExcelParseError, match="phone"):
            parse_excel_file(path)
    finally:
        os.unlink(path)


# --- Invalid rows ---


def test_missing_phone_marks_invalid():
    path = _make_xlsx(
        [
            ["phone", "name"],
            ["", "No Phone"],
        ]
    )
    try:
        rows = parse_excel_file(path)
        assert rows[0].is_valid is False
        assert rows[0].errors
    finally:
        os.unlink(path)


def test_invalid_phone_chars_marks_invalid():
    path = _make_xlsx(
        [
            ["phone", "name"],
            ["(849)abc", "Bad"],
        ]
    )
    try:
        rows = parse_excel_file(path)
        assert rows[0].is_valid is False
    finally:
        os.unlink(path)


def test_duplicate_phone_marks_second_as_duplicate():
    path = _make_xlsx(
        [
            ["phone", "name"],
            ["84901234567", "Alice"],
            ["84901234567", "Alice Copy"],
        ]
    )
    try:
        rows = parse_excel_file(path)
        assert rows[0].is_valid is True
        assert rows[1].is_valid is False
        assert any("uplicate" in e for e in rows[1].errors)
    finally:
        os.unlink(path)


# --- Structural errors ---


def test_missing_phone_column_raises():
    path = _make_xlsx(
        [
            ["name", "order_id"],
            ["Alice", "ORD001"],
        ]
    )
    try:
        with pytest.raises(ExcelParseError, match="phone"):
            parse_excel_file(path)
    finally:
        os.unlink(path)


def test_empty_file_raises():
    path = _make_xlsx([])
    try:
        with pytest.raises(ExcelParseError, match="empty"):
            parse_excel_file(path)
    finally:
        os.unlink(path)
