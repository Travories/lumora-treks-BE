"""Shared package group-pricing rules."""

from decimal import Decimal, ROUND_HALF_UP


GROUP_PRICE_BANDS = (
    (1, 1, Decimal("1.00")),
    (2, 3, Decimal("0.90")),
    (4, 7, Decimal("0.85")),
    (8, None, Decimal("0.80")),
)


def default_group_prices(base_price):
    """Return whole-number per-person tiers discounted by 10–20%."""

    price = Decimal(str(base_price))
    return [
        {
            "min_people": minimum,
            "max_people": maximum,
            "price_per_person": int((price * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
            "sort_order": order,
        }
        for order, (minimum, maximum, multiplier) in enumerate(GROUP_PRICE_BANDS, start=1)
    ]
