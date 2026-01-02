from .position import ActiveBinRef, Position
from .primitives import dataclass


@dataclass
class GetPositionByUser:
    active_bin: ActiveBinRef
    user_positions: list[Position]

    def __init__(self, data: dict):
        self.active_bin = ActiveBinRef(data["activeBin"])
        self.user_positions = [Position(position) for position in data["userPositions"]]