from epo_exporter.metrics import get_int, get_str, parse_epoch_or_iso


def test_get_int_basic():
    assert get_int(5) == 5
    assert get_int(5.9) == 5
    assert get_int("42") == 42
    assert get_int(None) is None
    assert get_int("not-a-number") is None


def test_get_str_basic():
    assert get_str("abc") == "abc"
    assert get_str(123) == "123"
    assert get_str(None) is None


def test_parse_epoch_or_iso():
    # epoch
    assert parse_epoch_or_iso(1700000000) == 1700000000
    # ISO with Z
    assert isinstance(parse_epoch_or_iso("2024-01-01T00:00:00Z"), int)
    # Bad input
    assert parse_epoch_or_iso("bad") is None


