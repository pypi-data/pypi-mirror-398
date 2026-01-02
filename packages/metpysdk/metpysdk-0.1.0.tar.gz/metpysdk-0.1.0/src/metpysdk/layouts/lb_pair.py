from construct import Bytes

from .parameters import ProtocolFee, StaticParameters, VariableParameters
from .primitives import I32, I64, U8, U16, U64, CStruct, PubkeyLayout
from .rewards import RewardInfo

LB_PAIR_LAYOUT = CStruct(
    "parameters" / StaticParameters,
    "v_parameters" / VariableParameters,
    "bump_seed" / Bytes(1),
    "bin_step_seed" / Bytes(2),
    "pair_type" / U8,
    "active_id" / I32,
    "bin_step" / U16,
    "status" / U8,
    "require_base_factor_seed" / U8,
    "base_factor_seed" / Bytes(2),
    "activation_type" / U8,
    "creator_pool_on_off_control" / U8,
    "token_x_mint" / PubkeyLayout,
    "token_y_mint" / PubkeyLayout,
    "reserve_x" / PubkeyLayout,
    "reserve_y" / PubkeyLayout,
    "protocol_fee" / ProtocolFee,
    "padding1" / Bytes(32),
    "reward_infos" / RewardInfo[2],
    "oracle" / PubkeyLayout,
    "bin_array_bitmap" / U64[16],
    "last_updated_at" / I64,
    "padding2" / Bytes(32),
    "pre_activation_swap_address" / PubkeyLayout,
    "base_key" / PubkeyLayout,
    "activation_point" / U64,
    "pre_activation_duration" / U64,
    "padding3" / Bytes(8),
    "padding4" / U64,
    "creator" / PubkeyLayout,
    "token_mint_x_program_flag" / U8,
    "token_mint_y_program_flag" / U8,
    "reserved" / Bytes(22),
)
