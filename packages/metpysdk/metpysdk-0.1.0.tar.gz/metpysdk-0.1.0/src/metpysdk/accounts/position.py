from .primitives import PositionVersion, Pubkey, dataclass


@dataclass
class ActiveBinRef:
    bin_id: int
    bin_step: int
    price: float

    def __init__(self, data: dict):
        self.bin_id = data["bin_id"]
        self.bin_step = data["bin_step"]
        self.price = data["price"]

@dataclass
class ActiveBin:
    bin_id: int
    x_amount: str
    y_amount: str
    supply: str
    version: int
    price: float
    price_per_token: str
    fee_amount_x_per_token_stored: int
    fee_amount_y_per_token_stored: int
    reward_per_token_stored: list[int]

    def __init__(self, data: dict):
        self.bin_id = data["binId"]
        self.x_amount = data["xAmount"]
        self.y_amount = data["yAmount"]
        self.supply = data["supply"]
        self.price = float(data["price"])
        self.version = data["version"]
        self.price_per_token = data["pricePerToken"]
        self.fee_amount_x_per_token_stored = int(data["feeAmountXPerTokenStored"])
        self.fee_amount_y_per_token_stored = int(data["feeAmountYPerTokenStored"])
        reward_per_token_stored = [int(x) for x in data["rewardPerTokenStored"]]
        self.reward_per_token_stored = reward_per_token_stored

@dataclass
class PositionBinData:
    bin_id: int
    price: str
    price_per_token: str
    bin_x_Amount: str
    bin_y_Amount: str
    bin_liquidity: str
    position_liquidity: str
    position_x_amount: str
    position_y_amount: str

    def __init__(self, data: dict):
        if data.get("binId") is None:
            raise AttributeError("binId is required")
        if data.get("price") is None:
            raise AttributeError("price is required")
        if data.get("pricePerToken") is None:
            raise AttributeError("pricePerToken is required")
        if data.get("binXAmount") is None:
            raise AttributeError("binXAmount is required")
        if data.get("binYAmount") is None:
            raise AttributeError("binYAmount is required")
        if data.get("binLiquidity") is None:
            raise AttributeError("binLiquidity is required")
        if data.get("positionLiquidity") is None:
            raise AttributeError("positionLiquidity is required")
        if data.get("positionXAmount") is None:
            raise AttributeError("positionXAmount is required")
        if data.get("positionYAmount") is None:
            raise AttributeError("positionYAmount is required")

        self.bin_id = data["binId"]
        self.price = data["price"]
        self.price_per_token = data["pricePerToken"]
        self.bin_x_Amount = data["binXAmount"]
        self.bin_y_Amount = data["binYAmount"]
        self.bin_liquidity = data["binLiquidity"]
        self.position_liquidity = data["positionLiquidity"]
        self.position_x_amount = data["positionXAmount"]
        self.position_y_amount = data["positionYAmount"]

    def to_json(self) -> dict:
        return {
            "binId": self.bin_id,
            "price": self.price,
            "pricePerToken": self.price_per_token,
            "binXAmount": self.bin_x_Amount,
            "binYAmount": self.bin_y_Amount,
            "binLiquidity": self.bin_liquidity,
            "positionLiquidity": self.position_liquidity,
            "positionXAmount": self.position_x_amount,
            "positionYAmount": self.position_y_amount
        }
@dataclass
class PositionData:
    total_x_amount: str
    total_y_amount: str
    position_bin_data: list[PositionBinData]
    last_updated_at: int
    upper_bin_id: int
    lower_bin_id: int
    fee_X: int
    fee_Y: int
    reward_one: int
    reward_two: int
    fee_owner: str
    total_claimed_fee_X_amount: int
    total_claimed_fee_Y_amount: int

    def __init__(self, data: dict):
        if data.get("totalXAmount") is None:
            raise AttributeError("totalXAmount is required")
        if data.get("totalYAmount") is None:
            raise AttributeError("totalYAmount is required")
        if data.get("positionBinData") is None:
            raise AttributeError("positionBinData is required")
        if data.get("lastUpdatedAt") is None:
            raise AttributeError("lastUpdatedAt is required")
        if data.get("upperBinId") is None:
            raise AttributeError("upperBinId is required")
        if data.get("lowerBinId") is None:
            raise AttributeError("lowerBinId is required")
        if data.get("feeX") is None:
            raise AttributeError("feeX is required")
        if data.get("feeY") is None:
            raise AttributeError("feeY is required")
        if data.get("rewardOne") is None:
            raise AttributeError("rewardOne is required")
        if data.get("rewardTwo") is None:
            raise AttributeError("rewardTwo is required")
        if data.get("feeOwner") is None:
            raise AttributeError("feeOwner is required")
        if data.get("totalClaimedFeeXAmount") is None:
            raise AttributeError("totalClaimedFeeXAmount is required")
        if data.get("totalClaimedFeeYAmount") is None:
            raise AttributeError("totalClaimedFeeYAmount is required")

        self.total_x_amount = data["totalXAmount"]
        self.total_y_amount = data["totalYAmount"]
        self.position_bin_data = [PositionBinData(bin_data) for bin_data in data["positionBinData"]]
        last_updated_at = data["lastUpdatedAt"]
        self.last_updated_at = last_updated_at if isinstance(last_updated_at, int) \
            else int(last_updated_at, 16)
        self.upper_bin_id = data["upperBinId"]
        self.lower_bin_id = data["lowerBinId"]
        self.fee_X = int(data["feeX"], 16)
        self.fee_Y = int(data["feeY"], 16)
        self.reward_one = data["rewardOne"]
        self.reward_two = data["rewardTwo"]
        self.fee_owner = data["feeOwner"]
        self.total_claimed_fee_X_amount = int(data["totalClaimedFeeXAmount"], 16)
        self.total_claimed_fee_Y_amount = int(data["totalClaimedFeeYAmount"], 16)

    def to_json(self) -> dict:
        return {
            "totalXAmount": self.total_x_amount,
            "totalYAmount": self.total_y_amount,
            "positionBinData": [bin_data.to_json() for bin_data in self.position_bin_data],
            "lastUpdatedAt": self.last_updated_at,
            "upperBinId": self.upper_bin_id,
            "lowerBinId": self.lower_bin_id,
            "feeX": self.fee_X,
            "feeY": self.fee_Y,
            "rewardOne": self.reward_one,
            "rewardTwo": self.reward_two,
            "feeOwner": self.fee_owner,
            "totalClaimedFeeXAmount": self.total_claimed_fee_X_amount,
            "totalClaimedFeeYAmount": self.total_claimed_fee_Y_amount
        }

@dataclass
class Position:
    public_key: Pubkey
    position_data: PositionData
    position_version: PositionVersion

    def __init__(self, data: dict):
        if data.get("public_key") is None:
            raise AttributeError("public_key is required")
        if data.get("position_data") is None:
            raise AttributeError("position_data is required")
        if data.get("version") is None:
            raise AttributeError("version is required")

        self.public_key = Pubkey.from_string(data["public_key"]) \
            if isinstance(data["public_key"], str) else data["public_key"]
        self.position_data = PositionData(data["position_data"])
        self.position_version = data["version"]

    def to_json(self):
        return {
            "publicKey": str(self.public_key),
            "positionData": self.position_data.to_json(),
            "version": str(self.position_version)
        }
