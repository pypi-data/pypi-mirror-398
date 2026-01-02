from collections.abc import Iterable
from typing import Optional, TypedDict

from ..accounts.bins import Bin
from ..accounts.position import ActiveBin
from ..maths.price import adjust_price_for_decimals, price_from_bin_id
from .constants import BIN_ARRAY_BITMAP_SIZE, BITS_PER_U64, MAX_BIN_PER_ARRAY, TOTAL_BITMAP_BITS

# -------------------------
# Types (decoded data, NOT layouts)
# -------------------------

class BitmapExtension(TypedDict):
    positive: list[list[int]]  # 12 x [8 x u64]
    negative: list[list[int]]


# -------------------------
# Bin index maths
# -------------------------

def bin_id_to_bin_array_index(bin_id: int) -> int:
    """
    Exact port of TS binIdToBinArrayIndex
    """
    idx, mod = divmod(bin_id, MAX_BIN_PER_ARRAY)
    if bin_id < 0 and mod != 0:
        idx -= 1
    return idx


def get_bin_array_indexes_coverage(
    lower_bin_id: int,
    upper_bin_id: int,
) -> list[int]:
    lower = bin_id_to_bin_array_index(lower_bin_id)
    upper = bin_id_to_bin_array_index(upper_bin_id)
    return list(range(lower, upper + 1))


# -------------------------
# Bitmap helpers
# -------------------------

def is_overflow_default_bin_array_bitmap(bin_array_index: int) -> bool:
    return bin_array_index < 0 or bin_array_index >= TOTAL_BITMAP_BITS


def _is_bit_set(bitmap: list[int], bit_index: int) -> bool:
    word = bit_index // BITS_PER_U64
    if word < 0 or word >= len(bitmap):
        return False
    offset = bit_index % BITS_PER_U64
    return ((bitmap[word] >> offset) & 1) == 1

def _is_extension_bit_set(
    bitmap: list[list[int]],
    abs_index: int,
) -> bool:
    chunk = abs_index // BITS_PER_U64
    offset = abs_index % BITS_PER_U64

    if chunk >= len(bitmap):
        return False

    return ((bitmap[chunk] >> offset) & 1) == 1



# -------------------------
# Public API
# -------------------------

def is_bin_array_initialized(
    bin_array_index: int,
    bitmap: list[int],
    extension_bitmap: Optional[BitmapExtension] = None,
) -> bool:
    """
    Exact DLMM bitmap logic (TS parity).
    """

    if -BIN_ARRAY_BITMAP_SIZE <= bin_array_index < BIN_ARRAY_BITMAP_SIZE:
        if bin_array_index >= 0:
            bit = bin_array_index
            word = (bit // BITS_PER_U64) + 8
            offset = bit % BITS_PER_U64
        else:
            bit = abs(bin_array_index) - 1
            word = bit // BITS_PER_U64
            offset = bit % BITS_PER_U64

        if word < 0 or word >= len(bitmap):
            return False

        return ((bitmap[word] >> offset) & 1) == 1

    if extension_bitmap is None:
        return False

    abs_index = abs(bin_array_index)

    if bin_array_index > 0:
        return _is_extension_bit_set(extension_bitmap.positive, abs_index)
    return _is_extension_bit_set(extension_bitmap.negative, abs_index)

def find_initialized_bin_array(
    start: int,
    end: int,
    bitmap: list[int],
    bitmap_ext: Optional[BitmapExtension],
) -> Optional[int]:
    step = 1 if start <= end else -1

    i = start
    while True:
        if is_bin_array_initialized(i, bitmap, bitmap_ext):
            return i
        if i == end:
            break
        i += step

    return None

def get_initialized_bin_array_indexes(
    bin_array_indexes: Iterable[int],
    default_bitmap: list[int],
    extension_bitmap: Optional[BitmapExtension] = None,
) -> list[int]:
    """
    Filters initialized bin array indexes from a list.
    """
    return [
        idx
        for idx in bin_array_indexes
        if is_bin_array_initialized(idx, default_bitmap, extension_bitmap)
    ]


def get_missing_bin_array_indexes(
    lower_bin_id: int,
    upper_bin_id: int,
    default_bitmap: list[int],
    extension_bitmap: Optional[BitmapExtension] = None,
) -> list[int]:
    """
    Returns missing (uninitialized) bin array indexes for a bin range.
    """
    required = get_bin_array_indexes_coverage(lower_bin_id, upper_bin_id)
    return [
        idx
        for idx in required
        if not is_bin_array_initialized(idx, default_bitmap, extension_bitmap)
    ]

def get_bin_array_lower_upper_bin_id(bin_array_index: int) -> tuple[int, int]:
    lower = bin_array_index * MAX_BIN_PER_ARRAY
    upper = lower + MAX_BIN_PER_ARRAY - 1
    return lower, upper

def enumerate_bins(
    *,
    bins_by_id: dict[int, Bin],
    lower_bin_id: int,
    upper_bin_id: int,
    bin_step_bps: int,
    base_token_decimals: int,
    quote_token_decimals: int,
    version: int,
):
    for bin_id in range(lower_bin_id, upper_bin_id + 1):
        raw_price = price_from_bin_id(
            bin_id=bin_id,
            bin_step_bps=bin_step_bps,
        )

        price = adjust_price_for_decimals(
            price=raw_price,
            base_decimals=base_token_decimals,
            quote_decimals=quote_token_decimals,
        )

        bin_obj = bins_by_id.get(bin_id)

        if bin_obj is not None:
            yield ActiveBin({
                "binId": bin_id,
                "xAmount": str(bin_obj.amount_x),
                "yAmount": str(bin_obj.amount_y),
                "supply": str(bin_obj.liquidity_supply),
                "price": float(price),
                "version": version,
                "pricePerToken": str(price),
                "feeAmountXPerTokenStored": bin_obj.fee_amount_x_per_token_stored,
                "feeAmountYPerTokenStored": bin_obj.fee_amount_y_per_token_stored,
                "rewardPerTokenStored": bin_obj.reward_per_token_stored
            })
        else:
            # empty bin (must exist logically)
            yield ActiveBin({
                "binId": bin_id,
                "xAmount": "0",
                "yAmount": "0",
                "supply": "0",
                "price": float(price),
                "version": version,
                "pricePerToken": str(price),
                "feeAmountXPerTokenStored": "0",
                "feeAmountYPerTokenStored": "0",
                "rewardPerTokenStored": []
            })