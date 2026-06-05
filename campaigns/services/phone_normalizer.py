import re


def normalize_phone_number(value: str) -> tuple[str, str | None]:
    """
    Normalize a phone number string.

    Returns a tuple of (normalized_phone, error_message).
    If normalization succeeds, error_message is None.
    If the value is invalid, normalized_phone is empty string and error_message describes the issue.
    """
    if not value or not value.strip():
        return "", "Phone number is missing."

    # Remove leading/trailing whitespace
    phone = value.strip()

    # Remove leading +
    if phone.startswith("+"):
        phone = phone[1:]

    # Remove all spaces
    phone = phone.replace(" ", "")

    # Remove hyphens and dots (common formatting)
    phone = phone.replace("-", "").replace(".", "")

    # After normalization, must be digits only
    if not re.fullmatch(r"\d+", phone):
        return "", f"Phone '{value}' contains invalid characters after normalization."

    # Sanity check: minimum 7 digits, maximum 15 (E.164 max)
    if len(phone) < 7:
        return "", f"Phone '{value}' is too short."

    if len(phone) > 15:
        return "", f"Phone '{value}' is too long."

    return phone, None
