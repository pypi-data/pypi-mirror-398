from dataclasses import dataclass

from .primitives import Pubkey, Union


@dataclass(slots=True)
class RewardInfoAccount:
    mint: Pubkey
    vault: Pubkey
    funder: Pubkey

    reward_duration: int
    reward_duration_end: int
    reward_rate: int

    last_update_time: int
    cumulative_seconds_with_empty_liquidity_reward: int

    @classmethod
    def from_layout(cls, raw) -> "RewardInfoAccount":
        """
        Convert parsed CStruct RewardInfo into an account model.
        """
        return cls(
            mint=Pubkey.from_bytes(raw.mint),
            vault=Pubkey.from_bytes(raw.vault),
            funder=Pubkey.from_bytes(raw.funder),
            reward_duration=raw.reward_duration,
            reward_duration_end=raw.reward_duration_end,
            reward_rate=raw.reward_rate,
            last_update_time=raw.last_update_time,
            cumulative_seconds_with_empty_liquidity_reward=(
                raw.cumulative_seconds_with_empty_liquidity_reward
            ),
        )

@dataclass(slots=True)
class LBPair:
    bump_seed: list[int]
    bin_step_seed: list[int]
    pair_type: int
    active_id: int
    bin_step: int
    status: int
    require_base_factor_seed: int
    base_factor_seed: list[int]
    token_x_mint: Pubkey
    token_y_mint: Pubkey
    padding1: list[int]
    padding2: list[int]
    fee_owner: Union[Pubkey, None]
    base_key: str
    reserve_x: Pubkey
    reserve_y: Pubkey
    token_mint_x_program_flag: int
    token_mint_y_program_flag: int
    reward_infos: list[RewardInfoAccount]

    def __init__(self, data) -> None:
        self.bump_seed = data.bump_seed
        self.bin_step_seed = data.bin_step_seed
        self.pair_type = data.pair_type
        self.active_id = data.active_id
        self.bin_step = data.bin_step
        self.status = data.status
        self.require_base_factor_seed = data.require_base_factor_seed
        self.base_factor_seed = data.base_factor_seed
        self.token_x_mint = Pubkey.from_bytes(data.token_x_mint)
        self.token_y_mint = Pubkey.from_bytes(data.token_y_mint)
        self.padding1 = data.padding1
        self.padding2 = data.padding2
        fee_owner = data.get("feeOwner", None)
        self.fee_owner = Pubkey.from_string(fee_owner) if fee_owner else fee_owner
        self.base_key = data.base_key
        self.reserve_x = Pubkey.from_bytes(data.reserve_x)
        self.reserve_y = Pubkey.from_bytes(data.reserve_y)
        self.token_mint_x_program_flag = data.token_mint_x_program_flag
        self.token_mint_y_program_flag = data.token_mint_y_program_flag
        self.reward_infos = [RewardInfoAccount.from_layout(x) for x in data.reward_infos]