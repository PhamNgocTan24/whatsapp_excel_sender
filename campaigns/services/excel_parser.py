import re
from dataclasses import dataclass, field

import openpyxl

from .phone_normalizer import normalize_phone_number


class ExcelParseError(Exception):
    """Raised when the Excel file itself is structurally invalid."""
    pass


@dataclass
class ParsedRecipientRow:
    row_number: int
    phone: str
    name: str
    params: dict
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def _normalize_header(raw: str) -> str:
    """Normalize a header string to lowercase snake_case."""
    header = raw.strip().lower()
    # Replace spaces and hyphens with underscores
    header = re.sub(r"[\s\-]+", "_", header)
    # Remove characters that are not alphanumeric or underscore
    header = re.sub(r"[^\w]", "", header)
    return header


def _is_row_empty(row) -> bool:
    """Return True if all cells in the row are None or empty string."""
    return all(cell.value is None or str(cell.value).strip() == "" for cell in row)


def _cell_to_str(value) -> str:
    """Convert a cell value to a clean string."""
    if value is None:
        return ""
    return str(value).strip()


def parse_excel_file(file_path: str) -> list[ParsedRecipientRow]:
    """
    Parse an Excel file and return a list of ParsedRecipientRow.

    Args:
        file_path: Absolute path to the .xlsx file.

    Returns:
        List of ParsedRecipientRow (valid and invalid mixed).

    Raises:
        ExcelParseError: If the file cannot be read or is missing required columns.
    """
    try:
        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    except Exception as exc:
        raise ExcelParseError(f"Could not open Excel file: {exc}") from exc

    sheet = workbook.worksheets[0]
    rows = list(sheet.iter_rows())

    if not rows:
        raise ExcelParseError("The Excel file is empty.")

    # Parse header row
    raw_headers = [_cell_to_str(cell.value) for cell in rows[0]]
    headers = [_normalize_header(h) for h in raw_headers]

    if "phone" not in headers:
        raise ExcelParseError(
            "Missing required column 'phone'. "
            f"Found columns: {', '.join(h for h in headers if h)}"
        )

    phone_index = headers.index("phone")
    name_index = headers.index("name") if "name" in headers else None

    # Columns that are not phone/name become template params
    param_indices = {
        i: headers[i]
        for i in range(len(headers))
        if i not in (phone_index, name_index) and headers[i]
    }

    parsed_rows: list[ParsedRecipientRow] = []
    seen_phones: set[str] = set()

    for row_index, row in enumerate(rows[1:], start=2):  # Excel row numbers start at 1, data at 2
        if _is_row_empty(row):
            continue

        cells = list(row)

        def get_cell(index: int) -> str:
            if index < len(cells):
                return _cell_to_str(cells[index].value)
            return ""

        raw_phone = get_cell(phone_index)
        name = get_cell(name_index) if name_index is not None else ""
        params = {col_name: get_cell(i) for i, col_name in param_indices.items()}

        errors: list[str] = []
        normalized_phone = ""

        # Normalize phone
        normalized_phone, phone_error = normalize_phone_number(raw_phone)
        if phone_error:
            errors.append(phone_error)
        elif normalized_phone in seen_phones:
            errors.append(f"Duplicate phone number: {normalized_phone}")
            parsed_rows.append(ParsedRecipientRow(
                row_number=row_index,
                phone=normalized_phone,
                name=name,
                params=params,
                errors=errors,
            ))
            continue
        else:
            seen_phones.add(normalized_phone)

        parsed_rows.append(ParsedRecipientRow(
            row_number=row_index,
            phone=normalized_phone if not errors else raw_phone,
            name=name,
            params=params,
            errors=errors,
        ))

    workbook.close()
    return parsed_rows
