def monthly_total(base_price: float, tax_percent: float, discount_percent: float) -> float:
    # BUG: applies discount after tax, which is not desired for this repository.
    taxed = base_price + (base_price * (tax_percent / 100.0))
    discounted = taxed - (taxed * (discount_percent / 100.0))
    return round(discounted, 2)
