from decimal import Decimal, getcontext

from ..utils.constants import BASIS_POINT_MAX

# DLMM price maths requires very high precision
getcontext().prec = 50
Q64 = Decimal(2) ** 64

# -------------------------
# Core DLMM price maths
# -------------------------

def price_from_bin_id(
    *,
    bin_id: int,
    bin_step_bps: int,
) -> Decimal:
    """
    DLMM price formula:
    price = (1 + bin_step / 10_000) ** bin_id
    """
    step = Decimal(bin_step_bps) / BASIS_POINT_MAX
    return (Decimal(1) + step) ** Decimal(bin_id)


def bin_id_from_price(
    *,
    price: Decimal,
    bin_step_bps: int,
    round_down: bool = True,
) -> int | None:
    """
    Inverse DLMM price formula.

    bin_id = log(price) / log(1 + bin_step)
    """
    if price <= 0:
        return None

    step = Decimal(bin_step_bps) / BASIS_POINT_MAX
    base = Decimal(1) + step

    raw = price.ln() / base.ln()

    if round_down:
        return int(raw.to_integral_value(rounding="ROUND_FLOOR"))
    return int(raw.to_integral_value(rounding="ROUND_CEILING"))

def adjust_price_for_decimals(
    *,
    price: Decimal,
    base_decimals: int,
    quote_decimals: int,
) -> Decimal:
    """
    Adjust raw DLMM price for token decimals.
    """
    scale = Decimal(10) ** (base_decimals - quote_decimals)
    return price * scale



# -------------------------
# Helpers
# -------------------------

def price_range_for_bin(
    *,
    bin_id: int,
    active_id: int,
    bin_step: Decimal,
    base_price: Decimal = Decimal(1),
) -> tuple[Decimal, Decimal]:
    """
    Return (min_price, max_price) for a bin.
    """
    min_price = price_from_bin_id(
        bin_id=bin_id,
        bin_step_bps=bin_step,
    )

    max_price = price_from_bin_id(
        bin_id=bin_id + 1,
        bin_step_bps=bin_step,
    )

    return min_price, max_price

def bin_price_to_decimal(
    raw_price: int,
    base_decimals: int,
    quote_decimals: int,
) -> Decimal:
    """
    Converts bin.price (u128 Q64.64) into human price per token.
    """
    price = Decimal(raw_price) / Q64
    scale = Decimal(10) ** (base_decimals - quote_decimals)
    return price * scale