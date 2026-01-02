from .primitives import dataclass


@dataclass
class FeeInfo:
    base_fee_rate_percentage: float
    max_fee_rate_percentage: float
    protocol_fee_percentage: float

    def __init__(self, data: dict) -> None:
        self.base_fee_rate_percentage = float(data["baseFeeRatePercentage"])
        self.max_fee_rate_percentage = float(data["maxFeeRatePercentage"])
        self.protocol_fee_percentage = float(data["protocolFeePercentage"])