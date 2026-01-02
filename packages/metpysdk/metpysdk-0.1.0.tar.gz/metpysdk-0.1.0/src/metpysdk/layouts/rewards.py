from .primitives import U64, U128, CStruct, PubkeyLayout

RewardInfo = CStruct(
    "mint" / PubkeyLayout,
    "vault" / PubkeyLayout,
    "funder" / PubkeyLayout,
    "reward_duration" / U64,
    "reward_duration_end" / U64,
    "reward_rate" / U128,
    "last_update_time" / U64,
    "cumulative_seconds_with_empty_liquidity_reward" / U64,
)

UserRewardInfo = CStruct(
    "rewardPerTokenCompletes" / U128[2],
    "rewardPendings" / U64[2],
)

FeeInfo = CStruct(
    "feeXPerTokenComplete" / U128,
    "feeYPerTokenComplete" / U128,
    "feeXPending" / U64,
    "feeYPending" / U64,
)
