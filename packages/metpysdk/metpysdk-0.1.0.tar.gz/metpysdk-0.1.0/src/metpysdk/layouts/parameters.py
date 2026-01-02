from construct import Bytes

from .primitives import I32, I64, U8, U16, U32, U64, CStruct

StaticParameters = CStruct(
    "base_factor" / U16,
    "filter_period" / U16,
    "decay_period" / U16,
    "reduction_factor" / U16,

    "variable_fee_control" / U32,
    "max_volatility_accumulator" / U32,

    "min_bin_id" / I32,
    "max_bin_id" / I32,

    "protocol_share" / U16,
    "base_fee_power_factor" / U8,

    "padding" / Bytes(5),
)

VariableParameters = CStruct(
    "volatility_accumulator" / U32,
    "volatility_reference" / U32,
    "index_reference" / I32,
    "padding" / Bytes(4),
    "last_update_timestamp" / I64,
    "padding1" / Bytes(8),
)

ProtocolFee = CStruct(
    "amount_x" / U64,
    "amount_y" / U64,
)
