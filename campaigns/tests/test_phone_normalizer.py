from campaigns.services.phone_normalizer import normalize_phone_number


def test_normalize_removes_plus_prefix():
    phone, error = normalize_phone_number("+84901234567")
    assert phone == "84901234567"
    assert error is None


def test_normalize_removes_spaces():
    phone, error = normalize_phone_number("84 901 234 567")
    assert phone == "84901234567"
    assert error is None


def test_normalize_removes_plus_and_spaces():
    phone, error = normalize_phone_number("+84 901 234 567")
    assert phone == "84901234567"
    assert error is None


def test_normalize_removes_hyphens():
    phone, error = normalize_phone_number("849-012-34567")
    assert phone == "84901234567"
    assert error is None


def test_normalize_plain_number():
    phone, error = normalize_phone_number("84901234567")
    assert phone == "84901234567"
    assert error is None


def test_invalid_contains_letters():
    phone, error = normalize_phone_number("(849)abc123")
    assert phone == ""
    assert error is not None


def test_invalid_parentheses():
    phone, error = normalize_phone_number("(849)123")
    assert phone == ""
    assert error is not None


def test_empty_string():
    phone, error = normalize_phone_number("")
    assert phone == ""
    assert error is not None


def test_none_like_empty():
    phone, error = normalize_phone_number("   ")
    assert phone == ""
    assert error is not None


def test_too_short():
    phone, error = normalize_phone_number("123")
    assert phone == ""
    assert error is not None


def test_too_long():
    phone, error = normalize_phone_number("1" * 16)
    assert phone == ""
    assert error is not None
