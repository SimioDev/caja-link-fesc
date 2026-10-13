import pytest

from src.documents import is_valid, mask, normalize, to_oriente_format


def test_normalize_strips_dots_spaces_and_leading_zeros():
    assert normalize("1.098.765.432") == "1098765432"
    assert normalize(" 1098765432 ") == "1098765432"
    assert normalize("001098765432") == "1098765432"


def test_normalize_is_idempotent_across_variants_of_the_same_document():
    canonical = normalize("1098765432")
    assert normalize("1.098.765.432") == canonical
    assert normalize("001098765432") == canonical
    assert normalize(" 1098765432 ") == canonical


@pytest.mark.parametrize("raw", ["abc", "...", "   ", "", "0", "000.000"])
def test_is_valid_rejects_documents_without_meaningful_digits(raw):
    assert not is_valid(normalize(raw))


@pytest.mark.parametrize("raw", ["1.098.765.432", "001098765432", "7"])
def test_is_valid_accepts_documents_with_digits(raw):
    assert is_valid(normalize(raw))


def test_to_oriente_format_pads_to_twelve_digits():
    assert to_oriente_format("1098765432") == "001098765432"
    assert len(to_oriente_format("1098765432")) == 12


def test_mask_keeps_at_most_four_trailing_digits():
    assert mask("1098765432") == "******5432"
    assert mask("123") == "***"
