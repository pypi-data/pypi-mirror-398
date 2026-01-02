import base58
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey

from ..layouts.discriminators import POSITION_V2_DISCRIMINATOR


def position_v2_filter():
    return MemcmpOpts(
        offset=0,
        bytes=base58.b58encode(POSITION_V2_DISCRIMINATOR).decode(),
    )

def position_owner_filter(owner: Pubkey):
    return MemcmpOpts(
        offset=8 + 32,
        bytes=str(owner),
    )

def position_lb_pair_filter(lb_pair: Pubkey):
    return MemcmpOpts(
        offset=8,
        bytes=str(lb_pair),
    )


class Filter:
    def __init__(self, offset: int, bytes_: str):
        self.offset = offset
        self.bytes = bytes_