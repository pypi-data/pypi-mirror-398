from .primitives import dataclass

@dataclass
class BinLiquidty:
    bin_id: int
    x_amount: str
    y_amount: str
    supply: str
    version: int
    price: str
    price_per_token: str

    def __init__(self, data: dict) -> None:
        if data.get("binId") is None:
            raise AttributeError("binId is required")
        if data.get("xAmount") is None:
            raise AttributeError("xAmount is required")
        if data.get("yAmount") is None:
            raise AttributeError("yAmount is required")
        if data.get("supply") is None:
            raise AttributeError("supply is required")
        if data.get("version") is None:
            raise AttributeError("version is required")
        if data.get("price") is None:
            raise AttributeError("price is required")

        self.bin_id = int(data["binId"])
        self.x_amount = data["xAmount"]
        self.y_amount = data["yAmount"]
        self.supply = data["supply"]
        self.version = int(data["version"])
        self.price = data["price"]
        self.price_per_token = data["pricePerToken"]

@dataclass
class GetBins:
    active_bin: int
    bin_liquidty: list[BinLiquidty]

    def __init__(self, data: dict) -> None:
        if data.get("activeBin") is None:
            raise AttributeError("activeBin is required")

        if data.get("bins") is None:
            raise AttributeError("bins is required")

        self.active_bin = int(data["activeBin"])
        self.bin_liquidty = [BinLiquidty(bin_data) for bin_data in data["bins"]]

@dataclass
class Bin:
    amount_x: int
    amount_x_in: int
    amount_y: int
    amount_y_in: int
    fee_amount_x_per_token_stored: int
    fee_amount_y_per_token_stored: int
    liquidity_supply: int
    price: int
    reward_per_token_stored: list[int]

    def __init__(self, data: dict) -> None:
        self.amount_x = int(data["amountX"], 16)
        self.amount_x_in = int(data["amountXIn"], 16)
        self.amount_y = int(data["amountY"], 16)
        self.amount_y_in = int(data["amountYIn"], 16)
        self.fee_amount_x_per_token_stored = int(data["feeAmountXPerTokenStored"], 16)
        self.fee_amount_y_per_token_stored = int(data["feeAmountYPerTokenStored"], 16)
        self.liquidity_supply = int(data["liquiditySupply"], 16)
        self.price = int(data["price"], 16)
        self.reward_per_token_stored = [int(r, 16) for r in data["rewardPerTokenStored"]]


@dataclass
class BinAccount:
    index: int
    bins: list[Bin]

    def __init__(self, data: dict) -> None:
        self.index = int(data["index"], 16)
        self.bins = [Bin(b) for b in data["bins"]]


@dataclass
class BinArray:
    public_key: str
    account: BinAccount

    def __init__(self, data: dict) -> None:
        self.public_key = data["publicKey"]
        self.account = BinAccount(data["account"])
