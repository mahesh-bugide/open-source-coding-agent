from src.billing.calculator import monthly_total


def test_monthly_total_applies_discount_before_tax() -> None:
    # Expected: (100 - 10%) => 90, then +10% tax => 99
    assert monthly_total(100, tax_percent=10, discount_percent=10) == 99.0
