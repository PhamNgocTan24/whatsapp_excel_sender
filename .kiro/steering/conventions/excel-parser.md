---
inclusion: manual
---

# Excel Parser Convention

## Library

Use `openpyxl` to read `.xlsx` files.

## Parser Input/Output

The Excel parser should NOT directly save database records. It should return parsed row objects:

```python
@dataclass
class ParsedRecipientRow:
    row_number: int
    phone: str
    name: str
    params: dict
    errors: list[str]
```

## Header Normalization

- Strip whitespace.
- Lowercase.
- Replace spaces with underscores.
- Remove unsupported characters if needed.

Examples:
```
"Phone Number" -> "phone_number"
" appointment date " -> "appointment_date"
```

Required phone column must be exactly: `phone`

## Parsing Behavior

- Read the first worksheet only.
- Use the first row as headers.
- Trim whitespace from header names.
- Normalize header names to lowercase snake_case.
- Ignore fully empty rows.
- Keep row number for error reporting.

## Empty Values

- `phone`: empty string if missing
- `name`: empty string if missing
- `params`: keep empty string values so operator can see missing data

## Phone Normalization

| Input | Output |
|-------|--------|
| `+84901234567` | `84901234567` |
| `84 901 234 567` | `84901234567` |
| `(849)123` | invalid |

Rules:
- Remove `+` prefix
- Remove spaces
- After normalization, if contains non-digit → mark as `invalid`
- Duplicate phone in same campaign → mark as `invalid` or `duplicate`
