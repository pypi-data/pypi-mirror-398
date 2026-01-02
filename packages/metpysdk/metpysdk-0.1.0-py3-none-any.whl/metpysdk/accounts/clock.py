from ..layouts.clock import ClockLayout
from .primitives import dataclass


@dataclass(frozen=True)
class Clock:
    slot: int
    epoch_start_timestamp: int
    epoch: int
    leader_schedule_epoch: int
    unix_timestamp: int

    @staticmethod
    def from_bytes(raw: bytes) -> "Clock":
        parsed = ClockLayout.parse(raw)
        return Clock(
            slot=parsed.slot,
            epoch_start_timestamp=parsed.epoch_start_timestamp,
            epoch=parsed.epoch,
            leader_schedule_epoch=parsed.leader_schedule_epoch,
            unix_timestamp=parsed.unix_timestamp,
        )