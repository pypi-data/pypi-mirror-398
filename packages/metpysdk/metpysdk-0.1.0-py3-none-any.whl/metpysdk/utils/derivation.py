from typing import Optional

from solders.pubkey import Pubkey
from spl.token._layouts import MINT_LAYOUT

from .constants import BIN_ARRAY_SEED

BIN_ARRAY_BITMAP_EXTENSION_SEED = b"bin_array_bitmap_extension"

def derive_bin_array(
    lb_pair: Pubkey | str | bytes,
    bin_array_index: int,
    program_id: Pubkey,
) -> Pubkey:
    """
    Correct PDA derivation for BinArray.
    Mirrors TS SDK exactly.
    """
    if isinstance(lb_pair, bytes):
        lb_pair = Pubkey.from_bytes(lb_pair)
    if isinstance(lb_pair, str):
        lb_pair = Pubkey.from_string(lb_pair)
    seeds = [
        BIN_ARRAY_SEED,
        bytes(lb_pair),
        bin_array_index.to_bytes(8, "little", signed=True),
    ]

    pda, _ = Pubkey.find_program_address(seeds, program_id)
    return pda

def derive_bin_array_bitmap_extension(
    lb_pair: Pubkey,
    program_id: Pubkey,
) -> Pubkey:
    pda, _ = Pubkey.find_program_address(
        [
            BIN_ARRAY_BITMAP_EXTENSION_SEED,
            bytes(lb_pair),
        ],
        program_id,
    )
    return pda

def unpack_mint(
    mint_pubkey: Pubkey,
    raw_data: bytes,
    owner: Optional[Pubkey],
) -> dict:
    if len(raw_data) < MINT_LAYOUT.sizeof():
        raise ValueError("Invalid mint account size")

    decoded = MINT_LAYOUT.parse(raw_data)

    return {
        "address": mint_pubkey,
        "mint_authority": decoded.mint_authority if decoded.mint_authority_option else None,
        "supply": decoded.supply,
        "decimals": decoded.decimals,
        "is_initialized": decoded.is_initialized,
        "freeze_authority": decoded.freeze_authority if decoded.freeze_authority_option else None,
        "owner": owner,
    }

def parse_anchor_account(
    raw: bytes,
    layout,
    expected_discriminator: bytes | None = None,
):
    if len(raw) < 8:
        raise ValueError("Account data too short")

    disc = raw[:8]

    if expected_discriminator and disc != expected_discriminator:
        raise ValueError(
            f"Invalid discriminator: {disc.hex()} != {expected_discriminator.hex()}"
        )

    return layout.parse(raw[8:])