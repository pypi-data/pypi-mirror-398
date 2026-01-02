from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_2022_PROGRAM_ID, TOKEN_PROGRAM_ID

from ..accounts.lb_pair import LBPair
from ..accounts.token import TokenReserve
from ..layouts.bin import BinArrayBitmapExtensionLayout
from ..layouts.lb_pair import LB_PAIR_LAYOUT
from ..utils.constants import DLMM_PROGRAM_ID
from ..utils.derivation import derive_bin_array_bitmap_extension, unpack_mint
from ..utils.rpc import get_account_data, get_multiple_account_datas


def _token_program_from_flag(flag: int):
    return TOKEN_2022_PROGRAM_ID if flag == 1 else TOKEN_PROGRAM_ID

class DLMMClient:
    """Handles connection/session and initializes LBPair and token accounts."""

    def __init__(self, pool: Pubkey, rpc: AsyncClient):
        self.pool = pool
        self.token_x = None
        self.token_y = None
        self.rpc = rpc
        self._lb_pair_raw = None
        self.lb_pair = None
        self.token_x_decimals: int | None = None
        self.token_y_decimals: int | None = None
        self.rewards = []

    async def fetch_lb_pair(self) -> LBPair:
        if self.lb_pair is not None:
            return self.lb_pair

        raw = await get_account_data(self.pool, self.rpc)
        decoded = LB_PAIR_LAYOUT.parse(raw)

        self.lb_pair = LBPair(decoded)
        return self.lb_pair

    async def fetch_token_metadata(self):
        if self.token_x is not None and self.token_y is not None:
            return

        lb_pair = await self.fetch_lb_pair()

        accounts_to_fetch = [
            lb_pair.reserve_x,
            lb_pair.reserve_y,
            lb_pair.token_x_mint,
            lb_pair.token_y_mint,
            lb_pair.reward_infos[0].vault,
            lb_pair.reward_infos[1].vault,
            lb_pair.reward_infos[0].mint,
            lb_pair.reward_infos[1].mint,
        ]

        accounts = await get_multiple_account_datas(accounts_to_fetch, self.rpc)
        acc_map = {pk: data for pk, data in accounts if data is not None}

        # ------------------------------------------------
        # Determine token programs
        # ------------------------------------------------
        program_x = (
            TOKEN_2022_PROGRAM_ID
            if lb_pair.token_mint_x_program_flag == 1
            else TOKEN_PROGRAM_ID
        )
        program_y = (
            TOKEN_2022_PROGRAM_ID
            if lb_pair.token_mint_y_program_flag == 1
            else TOKEN_PROGRAM_ID
        )

        # ------------------------------------------------
        # Decode token X / Y mints
        # ------------------------------------------------
        mint_x_raw = acc_map.get(lb_pair.token_x_mint)
        mint_y_raw = acc_map.get(lb_pair.token_y_mint)

        if mint_x_raw is None or mint_y_raw is None:
            raise RuntimeError("Token mint accounts not found")

        mint_x = unpack_mint(lb_pair.token_x_mint, mint_x_raw, program_x)
        mint_y = unpack_mint(lb_pair.token_y_mint, mint_y_raw, program_y)

        # ------------------------------------------------
        # Decode reserves
        # ------------------------------------------------
        reserve_x_raw = acc_map.get(lb_pair.reserve_x)
        reserve_y_raw = acc_map.get(lb_pair.reserve_y)

        if reserve_x_raw is None or reserve_y_raw is None:
            raise RuntimeError("Reserve accounts not found")

        amount_x = int.from_bytes(reserve_x_raw[64:72], "little")
        amount_y = int.from_bytes(reserve_y_raw[64:72], "little")

        self.token_x = TokenReserve(
            public_key=lb_pair.token_x_mint,
            reserve=lb_pair.reserve_x,
            mint=mint_x,
            amount=amount_x,
            owner=program_x,
            transfer_hook_account_metas=[],
        )

        self.token_y = TokenReserve(
            public_key=lb_pair.token_y_mint,
            reserve=lb_pair.reserve_y,
            mint=mint_y,
            amount=amount_y,
            owner=program_y,
            transfer_hook_account_metas=[],
        )

        # ------------------------------------------------
        # Rewards (optional, up to 2)
        # ------------------------------------------------

        for reward_info in lb_pair.reward_infos:
            # Skip empty reward slots
            if reward_info.mint == Pubkey.default():
                self.rewards.append(None)
                continue

            vault_raw = acc_map.get(reward_info.vault)
            mint_raw = acc_map.get(reward_info.mint)
            if any([not vault_raw, not mint_raw]):
                self.rewards.append(None)
                continue

            # Owner must be a token program
            mint_owner = Pubkey.from_bytes(reward_info.funder)
            if mint_owner not in (TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID):
                # This is the case you're hitting now
                self.rewards.append(None)
                continue

            reward_amount = int.from_bytes(vault_raw[64:72], "little")

            reward_mint = unpack_mint(
                reward_info.mint,
                mint_raw,
                mint_owner,
            )

            self.rewards.append(
                TokenReserve(
                    public_key=reward_info.mint,
                    reserve=reward_info.vault,
                    mint=reward_mint,
                    amount=reward_amount,
                    owner=mint_owner,
                    transfer_hook_account_metas=[],
                )
            )

    async def fetch_bitmap_extension(self):
        pda = derive_bin_array_bitmap_extension(
            self.pool,
            DLMM_PROGRAM_ID,
        )

        accounts = await get_multiple_account_datas([pda], self.rpc)
        if not accounts:
            return None

        _, raw = accounts[0]
        return BinArrayBitmapExtensionLayout.parse(raw)