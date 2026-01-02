from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from solders.pubkey import Pubkey

from ..layouts.discriminators import POSITION_V2_DISCRIMINATOR
from ..layouts.position import ExtendedPositionBinDataLayout, PositionV2Layout
from ..utils.bitmap import bin_id_to_bin_array_index
from ..utils.constants import DLMM_PROGRAM_ID, SCALE_OFFSET
from ..utils.derivation import derive_bin_array, parse_anchor_account
from .bins import get_bins_between_lower_and_upper_bound


def is_position_v2(data: bytes) -> bool:
    return data[:8] == POSITION_V2_DISCRIMINATOR

def wrap_position(
    *,
    position_pubkey: Pubkey,
    raw_data: bytes) -> PositionRaw:
    if not is_position_v2(raw_data):
        raise RuntimeError("Unknown position account type")

    base_size = PositionV2Layout.sizeof()+8
    base_raw = raw_data[:base_size]
    extended_raw = raw_data[base_size:]
    base = parse_anchor_account(
        base_raw,
        PositionV2Layout,
        POSITION_V2_DISCRIMINATOR
    )

    extended = parse_extended_position_data(extended_raw)

    combined = combine_base_and_extended_position_bin_data(
        base,
        extended,
    )

    return PositionRaw(
        public_key=position_pubkey,
        state=base,
        extended=extended,
        bins=combined,
    )

def parse_extended_position_data(
    raw: bytes,
) -> list:
    """
    Parse extended position bin data.
    """
    items = []
    offset = 0
    size = ExtendedPositionBinDataLayout.sizeof()

    while offset + size <= len(raw):
        item = ExtendedPositionBinDataLayout.parse(raw[offset : offset + size])
        items.append(item)
        offset += size

    return items

def combine_base_and_extended_position_bin_data(
    base,
    extended: list,
):
    liquidity_shares = list(base.liquidity_shares)
    reward_infos = list(base.reward_infos)
    fee_infos = list(base.fee_infos)

    for ext in extended:
        liquidity_shares.append(ext.liquidity_share)
        reward_infos.append(ext.reward_info)
        fee_infos.append(ext.fee_info)

    return {
        "liquidity_shares": liquidity_shares,
        "reward_infos": reward_infos,
        "fee_infos": fee_infos,
    }

def get_bin_array_indexes_coverage(
    *,
    lower_bin_id: int,
    upper_bin_id: int,
) -> list[int]:
    lower = bin_id_to_bin_array_index(lower_bin_id)
    upper = bin_id_to_bin_array_index(upper_bin_id)
    return list(range(lower, upper + 1))

def get_bin_array_pubkeys_coverage(
    *,
    lb_pair: Pubkey,
    lower_bin_id: int,
    upper_bin_id: int,
    program_id: Pubkey,
) -> list[Pubkey]:
    lower_index = bin_id_to_bin_array_index(lower_bin_id)
    upper_index = bin_id_to_bin_array_index(upper_bin_id)

    pubkeys: list[Pubkey] = []

    for idx in range(lower_index, upper_index + 1):
        pubkeys.append(
            derive_bin_array(
                lb_pair=lb_pair,
                bin_array_index=idx,
                program_id=program_id,
            )
        )

    return pubkeys


def process_position(
    *,
    lb_pair,
    clock,
    position,
    base_mint,
    quote_mint,
    reward_mint_0,
    reward_mint_1,
    bin_array_map: dict,
):
    lower_bin_id = position.lower_bin_id
    upper_bin_id = position.upper_bin_id

    pos_shares: list[int] = position.liquidity_shares()
    fee_infos = position.fee_infos()
    position_reward_infos = position.reward_infos()

    total_claimed_fee_x = position.total_claimed_fee_x_amount()
    total_claimed_fee_y = position.total_claimed_fee_y_amount()

    total_x_amount = Decimal(0)
    total_y_amount = Decimal(0)

    fee_x = 0
    fee_y = 0

    rewards = [0, 0]

    position_data = []

    bins = get_bins_between_lower_and_upper_bound(
        lb_pair_key=position.lb_pair(),
        lb_pair=lb_pair,
        lower_bin_id=lower_bin_id,
        upper_bin_id=upper_bin_id,
        base_token_decimals=base_mint["decimals"],
        quote_token_decimals=quote_mint["decimals"],
        bin_array_map=bin_array_map,  # dict[int, BinArrayLayout]
        program_id=DLMM_PROGRAM_ID,
    )

    if not bins:
        return None

    for idx, bin in enumerate(bins):
        # bin_supply = int(bin["supply"])
        # pos_share = pos_shares[idx]
        bin_supply = int(bin.supply)
        pos_share = pos_shares[idx]

        # -----------------------------
        # Position liquidity in bin
        # -----------------------------
        if bin_supply == 0:
            position_x_amount = 0
            position_y_amount = 0
        else:
            position_x_amount = (pos_share * int(bin.x_amount)) // bin_supply
            position_y_amount = (pos_share * int(bin.y_amount)) // bin_supply

        total_x_amount += Decimal(position_x_amount)
        total_y_amount += Decimal(position_y_amount)

        # -----------------------------
        # Fees
        # -----------------------------
        fee_info = fee_infos[idx]

        if pos_share == 0:
            new_fee_x = 0
            new_fee_y = 0
        else:
            new_fee_x = mul_shr(
                pos_share >> SCALE_OFFSET,
                bin.fee_amount_x_per_token_stored - fee_info.feeXPerTokenComplete,
                SCALE_OFFSET,
            )
            new_fee_y = mul_shr(
                pos_share >> SCALE_OFFSET,
                bin.fee_amount_y_per_token_stored - fee_info.feeYPerTokenComplete,
                SCALE_OFFSET,
            )

        claimable_fee_x = new_fee_x + fee_info.feeXPending
        claimable_fee_y = new_fee_y + fee_info.feeYPending

        fee_x += claimable_fee_x
        fee_y += claimable_fee_y

        # -----------------------------
        # Rewards
        # -----------------------------
        claimable_rewards_in_bin = [0, 0]

        for j in range(2):
            pair_reward_info = lb_pair.reward_infos[j]

            if pair_reward_info.mint == Pubkey.default():
                continue

            reward_per_token_stored = bin.reward_per_token_stored[j]

            # Active bin reward update
            if bin.bin_id == lb_pair.active_id and bin.supply != 0:
                current_time = min(
                    clock.unix_timestamp,
                    pair_reward_info.reward_duration_end,
                )

                delta = current_time - pair_reward_info.last_update_time
                liquidity_supply = int(bin.supply) >> SCALE_OFFSET

                if liquidity_supply > 0:
                    reward_delta = (
                        pair_reward_info.reward_rate
                        * delta
                        // 15
                        // liquidity_supply
                    )
                    reward_per_token_stored += reward_delta

            pos_reward_info = position_reward_infos[idx]

            delta_reward = (
                reward_per_token_stored
                - pos_reward_info.rewardPerTokenCompletes[j]
            )

            if pos_share == 0:
                new_reward = 0
            else:
                new_reward = mul_shr(
                    delta_reward,
                    pos_share >> SCALE_OFFSET,
                    SCALE_OFFSET,
                )

            claimable_reward = new_reward + pos_reward_info.rewardPendings[j]

            claimable_rewards_in_bin[j] += claimable_reward
            rewards[j] += claimable_reward

        # -----------------------------
        # Collect per-bin position data
        # -----------------------------
        position_data.append(
            {
                "binId": bin.bin_id,
                "price": bin.price,
                "pricePerToken": bin.price_per_token,
                "binXAmount": str(bin.x_amount),
                "binYAmount": str(bin.y_amount),
                "binLiquidity": str(bin_supply),
                "positionLiquidity": str(pos_share),
                "positionXAmount": str(position_x_amount),
                "positionYAmount": str(position_y_amount),
                "positionFeeXAmount": str(claimable_fee_x),
                "positionFeeYAmount": str(claimable_fee_y),
                "positionRewardAmount": [
                    str(claimable_rewards_in_bin[0]),
                    str(claimable_rewards_in_bin[1]),
                ],
            }
        )

    return {
        "totalXAmount": str(total_x_amount),
        "totalYAmount": str(total_y_amount),
        "positionBinData": position_data,
        "lastUpdatedAt": position.last_updated_at(),
        "upperBinId": position.upper_bin_id,
        "lowerBinId": position.lower_bin_id,
        "feeX": str(fee_x),
        "feeY": str(fee_y),
        "rewardOne": str(rewards[0]),
        "rewardTwo": str(rewards[1]),
        "feeOwner": position.fee_owner(),
        "totalClaimedFeeXAmount": str(total_claimed_fee_x),
        "totalClaimedFeeYAmount": str(total_claimed_fee_y),
    }

def mul_shr(a: int, b: int, shift: int) -> int:
    """
    Equivalent to TS mulShr(..., Rounding.Down)
    """
    return (a * b) >> shift

@dataclass
class PositionRaw:
    public_key: Pubkey
    state: object  # PositionV2 parsed struct
    extended: list
    bins: dict  # combinedPositionBinData

    # -------------------------
    # Identity
    # -------------------------

    def address(self) -> Pubkey:
        return self.public_key

    def lb_pair(self) -> Pubkey:
        return self.state.lb_pair

    def owner(self) -> Pubkey:
        return self.state.owner

    def operator(self) -> Pubkey:
        return self.state.operator

    def fee_owner(self) -> Pubkey:
        return self.state.fee_owner

    # -------------------------
    # Bin range
    # -------------------------

    @property
    def lower_bin_id(self) -> int:
        return self.state.lower_bin_id

    @property
    def upper_bin_id(self) -> int:
        return self.state.upper_bin_id

    def width(self) -> int:
        return self.upper_bin_id - self.lower_bin_id + 1

    # -------------------------
    # Liquidity & accounting
    # -------------------------

    def liquidity_shares(self) -> list:
        return self.bins["liquidity_shares"]

    def reward_infos(self) -> list:
        return self.bins["reward_infos"]

    def fee_infos(self) -> list:
        return self.bins["fee_infos"]

    def last_updated_at(self) -> int:
        return self.state.last_updated_at

    def total_claimed_fee_x_amount(self) -> int:
        return self.state.total_claimed_fee_x_amount

    def total_claimed_fee_y_amount(self) -> int:
        return self.state.total_claimed_fee_y_amount

    def total_claimed_rewards(self) -> list:
        return list(self.state.total_claimed_rewards)

    def get_bin_array_indexes_coverage(self) -> list[int]:
        is_extended = len(self.extended) > 0

        if is_extended:
            return get_bin_array_indexes_coverage(
                lower_bin_id=self.lower_bin_id,
                upper_bin_id=self.upper_bin_id
            )

        lower_idx = bin_id_to_bin_array_index(self.lower_bin_id)
        return [lower_idx, lower_idx + 1]

    def get_bin_array_pubkeys_coverage(
        self,
        program_id: Pubkey = DLMM_PROGRAM_ID,
    ) -> list[Pubkey]:
        return [
            derive_bin_array(self.lb_pair(), idx, program_id)
            for idx in self.get_bin_array_indexes_coverage()
        ]

    # -------------------------
    # Versioning
    # -------------------------

    @property
    def version(self) -> int:
        return 2
