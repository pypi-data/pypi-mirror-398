from .primitives import I64, U64, CStruct

ClockLayout = CStruct(
    "slot" / U64,
    "epoch_start_timestamp" / I64,
    "epoch" / U64,
    "leader_schedule_epoch" / U64,
    "unix_timestamp" / I64,
)
