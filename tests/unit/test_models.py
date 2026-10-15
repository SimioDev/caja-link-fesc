from datetime import date

from src.adapters.models import AffiliateType, Membership


def _membership(valid_from, valid_to):
    return Membership(valid_from=valid_from, valid_to=valid_to, affiliate_type=AffiliateType.DEPENDIENTE)


def test_is_active_false_before_valid_from():
    membership = _membership(date(2027, 1, 1), None)
    assert not membership.is_active(date(2026, 10, 15))


def test_is_active_true_within_range():
    membership = _membership(date(2020, 1, 1), date(2030, 1, 1))
    assert membership.is_active(date(2026, 10, 15))


def test_is_active_false_after_valid_to():
    membership = _membership(date(2020, 1, 1), date(2025, 1, 1))
    assert not membership.is_active(date(2026, 10, 15))


def test_is_active_true_on_exact_valid_from():
    membership = _membership(date(2026, 10, 15), None)
    assert membership.is_active(date(2026, 10, 15))


def test_is_active_true_on_exact_valid_to():
    membership = _membership(date(2020, 1, 1), date(2026, 10, 15))
    assert membership.is_active(date(2026, 10, 15))
