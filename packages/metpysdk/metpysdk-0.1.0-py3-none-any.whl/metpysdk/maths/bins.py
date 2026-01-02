from decimal import Decimal, getcontext

from ..layouts.bin import Bin

# High precision for DLMM maths
getcontext().prec = 40


# -------------------------
# Amount scaling helpers
# (move to maths/amounts.py later)
# -------------------------

def to_lamports(amount: Decimal, decimals: int) -> int:
    return int(amount * (Decimal(10) ** decimals))


def from_lamports(amount: int, decimals: int) -> Decimal:
    return Decimal(amount) / (Decimal(10) ** decimals)


# -------------------------
# Bin list helpers
# -------------------------

def slice_bins_by_relative_index(
    bins: list[Bin],
    start: int,
    end: int,
) -> list[Bin]:
    """
    Slice bins by local index inside a BinArray.
    Does NOT use global binId.
    """
    return bins[start : end + 1]


def bins_around_index(
    bins: list[Bin],
    center_index: int,
    left: int,
    right: int,
) -> list[Bin]:
    """
    Return bins around a given local index.
    """
    start = max(0, center_index - left)
    end = min(len(bins) - 1, center_index + right)
    return bins[start : end + 1]


# -------------------------
# Bin inspection helpers
# -------------------------

def has_liquidity(bin: Bin) -> bool:
    return bin.liquidity_supply > 0


def filter_bins_with_liquidity(bins: list[Bin]) -> list[Bin]:
    return [b for b in bins if b.liquidity_supply > 0]
