from solders.pubkey import Pubkey

from ..accounts.position import ActiveBin
from ..layouts.bin import BinArray as BinArrayLayout
from ..maths.price import adjust_price_for_decimals, price_from_bin_id
from ..utils.bitmap import bin_id_to_bin_array_index, get_bin_array_lower_upper_bin_id
from ..utils.constants import MAX_BIN_PER_ARRAY
from ..utils.derivation import derive_bin_array


def get_bins_between_lower_and_upper_bound(
    *,
    lb_pair_key: Pubkey,
    lb_pair,
    lower_bin_id: int,
    upper_bin_id: int,
    base_token_decimals: int,
    quote_token_decimals: int,
    bin_array_map: dict[str, BinArrayLayout],
    program_id: Pubkey,
) -> list[ActiveBin]:

    lower_bin_array_index = bin_id_to_bin_array_index(lower_bin_id)
    upper_bin_array_index = bin_id_to_bin_array_index(upper_bin_id)

    bins: list[ActiveBin] = []

    for bin_array_index in range(
        lower_bin_array_index,
        upper_bin_array_index + 1,
    ):
        bin_array_pubkey = derive_bin_array(
            lb_pair_key,
            bin_array_index,
            program_id,
        )

        bin_array = bin_array_map.get(str(bin_array_pubkey))

        lower_id_for_array, _ = get_bin_array_lower_upper_bin_id(
            bin_array_index
        )

        for i in range(MAX_BIN_PER_ARRAY):
            bin_id = lower_id_for_array + i

            if bin_id < lower_bin_id or bin_id > upper_bin_id:
                continue

            raw_price = price_from_bin_id(
                bin_id=bin_id,
                bin_step_bps=lb_pair.bin_step,
            )

            price_per_token = adjust_price_for_decimals(
                price=raw_price,
                base_decimals=base_token_decimals,
                quote_decimals=quote_token_decimals,
            )

            if bin_array is None:
                # Empty bin (TS behavior)
                bins.append(
                    ActiveBin({
                        "binId": bin_id,
                        "xAmount": "0",
                        "yAmount": "0",
                        "supply": "0",
                        "feeAmountXPerTokenStored": "0",
                        "feeAmountYPerTokenStored": "0",
                        "rewardPerTokenStored": ["0", "0"],
                        "price": float(raw_price),
                        "version": 2,
                        "pricePerToken": str(price_per_token),
                    })
                )
            else:
                bin_obj = bin_array.bins[i]

                bins.append(
                    ActiveBin({
                        "binId": bin_id,
                        "xAmount": str(bin_obj.amount_x),
                        "yAmount": str(bin_obj.amount_y),
                        "supply": str(bin_obj.liquidity_supply),
                        "feeAmountXPerTokenStored": str(
                            bin_obj.fee_amount_x_per_token_stored
                        ),
                        "feeAmountYPerTokenStored": str(
                            bin_obj.fee_amount_y_per_token_stored
                        ),
                        "rewardPerTokenStored": [
                            str(bin_obj.reward_per_token_stored[0]),
                            str(bin_obj.reward_per_token_stored[1]),
                        ],
                        "price": float(raw_price),
                        "version": bin_array.version,
                        "pricePerToken": str(price_per_token),
                    })
                )

    return bins
