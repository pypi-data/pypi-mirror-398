from enum import Enum
from typing import TypedDict, Union
from dataclasses import dataclass
from solders.pubkey import Pubkey

class DlmmHttpError(Exception):
    def __init__(self, message):
        super().__init__(message)


class StrategyType(Enum):
    SpotOneSide = 0,
    CurveOneSide = 1,
    BidAskOneSide = 2,
    SpotImBalanced = 3,
    CurveImBalanced = 4,
    BidAskImBalanced = 5,
    SpotBalanced = 6,
    CurveBalanced = 7,
    BidAskBalanced = 8

    def __str__(self) -> str:
        return f"{self.value[0]}"

    def __repr__(self) -> str:
        return self.name


class ActivationType(Enum):
    Slot = 0,
    Timestamp = 1,

    def __str__(self) -> str:
        return self.value[1]

    def __repr__(self) -> str:
        return self.name


class PositionVersion(Enum):
    V1 = "V1",
    V2 = "V2"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


class StrategyParameters(TypedDict):
    max_bin_id: int
    min_bin_id: int
    strategy_type: StrategyType