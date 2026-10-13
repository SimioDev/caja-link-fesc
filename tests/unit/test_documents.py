from src.documents import mask, normalize, to_oriente_format


def test_normalize_strips_dots_spaces_and_leading_zeros():
    assert normalize("1.098.765.432") == "1098765432"
    assert normalize(" 1098765432 ") == "1098765432"
    assert normalize("001098765432") == "1098765432"


def test_normalize_is_idempotent_across_variants_of_the_same_document():
    canonical = normalize("1098765432")
    assert normalize("1.098.765.432") == canonical
    assert normalize("001098765432") == canonical
    assert normalize(" 1098765432 ") == canonical


def test_to_oriente_format_pads_to_twelve_digits():
    assert to_oriente_format("1098765432") == "001098765432"
    assert len(to_oriente_format("1098765432")) == 12


def test_mask_keeps_at_most_four_trailing_digits():
    assert mask("1098765432") == "******5432"
    assert mask("123") == "***"
