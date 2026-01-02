from solders.instruction import AccountMeta

from .primitives import Pubkey, dataclass


@dataclass(slots=True)
class TokenReserve:
    public_key: Pubkey          # token mint
    reserve: Pubkey             # reserve account
    mint: dict                  # unpacked mint (supply, decimals, authority, ...)
    amount: int                 # reserve balance (raw amount)
    owner: Pubkey               # token program owner
    transfer_hook_account_metas: list[AccountMeta]

    @property
    def decimals(self) -> int:
        return self.mint["decimals"]
