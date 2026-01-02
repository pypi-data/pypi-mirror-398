from construct import Bytes

from .primitives import I64, U8, U64, U128, BitmapSide, CStruct, PubkeyLayout

Bin = CStruct(
    "amount_x" / U64,
    "amount_y" / U64,
    "price" / U128,
    "liquidity_supply" / U128,
    "reward_per_token_stored" / U128[2],
    "fee_amount_x_per_token_stored" / U128,
    "fee_amount_y_per_token_stored" / U128,
    "amount_x_in" / U128,
    "amount_y_in" / U128,
)

BinArray = CStruct(
    "index" / I64,
    "version" / U8,
    "padding" / Bytes(7),
    "lb_pair" / PubkeyLayout,
    "bins" / Bin[70],
)

BinArrayBitmapExtensionLayout = CStruct(
    "lbPair" / PubkeyLayout,
    "positive" / BitmapSide,
    "negative" / BitmapSide,
)
