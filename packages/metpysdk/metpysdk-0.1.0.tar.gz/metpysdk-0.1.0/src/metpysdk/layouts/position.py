from construct import Bytes

from .primitives import I32, I64, U8, U64, U128, CStruct, PubkeyLayout
from .rewards import FeeInfo, UserRewardInfo

Position = CStruct(
    "lb_pair" / PubkeyLayout,
    "owner" / PubkeyLayout,
    "liquidity_shares" / U64[70],
    "reward_infos" / UserRewardInfo[70],
    "fee_infos" / FeeInfo[70],
    "lower_bin_id" / I32,
    "upper_bin_id" / I32,
    "last_updated_at" / I64,
    "total_claimed_fee_x_amount" / U64,
    "total_claimed_fee_y_amount" / U64,
    "total_claimed_rewards" / U64[2],
    "reserved" / Bytes(160),
)

PositionV2Layout = CStruct(
    "lb_pair" / PubkeyLayout,
    "owner" / PubkeyLayout,
    "liquidity_shares" / U128[70],
    "reward_infos" / UserRewardInfo[70],
    "fee_infos" / FeeInfo[70],
    "lower_bin_id" / I32,
    "upper_bin_id" / I32,
    "last_updated_at" / I64,
    "total_claimed_fee_x_amount" / U64,
    "total_claimed_fee_y_amount" / U64,
    "total_claimed_rewards" / U64[2],
    "operator" / PubkeyLayout,
    "lock_release_point" / U64,
    "padding0" / U8,
    "fee_owner" / PubkeyLayout,
    "reserved" / Bytes(87),
)

ExtendedPositionBinDataLayout = CStruct(
    "liquidity_share" / U128,
    "reward_info" / UserRewardInfo,
    "fee_info" / FeeInfo,
)
