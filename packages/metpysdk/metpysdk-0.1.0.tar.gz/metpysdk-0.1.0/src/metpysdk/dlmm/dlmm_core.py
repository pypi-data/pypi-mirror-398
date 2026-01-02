import asyncio
from typing import Any, Optional

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from ..accounts.bins import Bin
from ..accounts.clock import Clock
from ..accounts.position import ActiveBin, Position
from ..accounts.position import Position as PositionAccount
from ..helpers.positions import (
    get_bin_array_pubkeys_coverage,
    process_position,
    wrap_position,
)
from ..layouts.bin import BinArray as BinArrayLayout
from ..layouts.bin import BinArrayBitmapExtensionLayout
from ..layouts.clock import ClockLayout
from ..layouts.discriminators import (
    BIN_ARRAY_BITMAP_EXTENSION_DISCRIMINATOR,
    BIN_ARRAY_DISCRIMINATOR,
    LB_PAIR_DISCRIMINATOR,
)
from ..layouts.lb_pair import LB_PAIR_LAYOUT
from ..utils.bitmap import (
    bin_id_to_bin_array_index,
    enumerate_bins,
    get_bin_array_lower_upper_bin_id,
    is_bin_array_initialized,
)
from ..utils.constants import (
    DLMM_PROGRAM_ID,
    SOLANA_MAINNET,
    SYSVAR_CLOCK_PUBKEY,
)
from ..utils.derivation import (
    derive_bin_array,
    derive_bin_array_bitmap_extension,
    parse_anchor_account,
)
from ..utils.filters import (
    position_lb_pair_filter,
    position_owner_filter,
    position_v2_filter,
)
from ..utils.rpc import get_account_data, get_multiple_account_datas
from .client import DLMMClient


class DLMM:
    def __init__(
            self,
            *,
            pool: Pubkey,
            lb_pair,
            bitmap_ext,
            token_x,
            token_y,
            rewards: list,
            rpc: AsyncClient,
    ):
        # Core
        self.pool: Pubkey = pool
        self.rpc: AsyncClient = rpc

        # On-chain state
        self.lb_pair = lb_pair
        self.bitmap_ext = bitmap_ext

        # Token metadata
        self.token_x = token_x
        self.token_y = token_y
        self.rewards = rewards

    @staticmethod
    async def create(
            pool: Pubkey | str,
            rpc: AsyncClient = AsyncClient(SOLANA_MAINNET),
            program_id: Pubkey = DLMM_PROGRAM_ID,
    ) -> "DLMM":
        if isinstance(pool, str):
            pool = Pubkey.from_string(pool)
        bitmap_ext_pda = derive_bin_array_bitmap_extension(pool, program_id)

        accounts = await get_multiple_account_datas(
            [pool, bitmap_ext_pda],
            rpc,
        )

        acc_map = {pk: raw for pk, raw in accounts}

        lb_pair_raw = acc_map.get(pool)
        if lb_pair_raw is None:
            raise RuntimeError("LB Pair account not found")

        lb_pair = parse_anchor_account(
            lb_pair_raw,
            LB_PAIR_LAYOUT,
            LB_PAIR_DISCRIMINATOR
        )

        bitmap_ext_raw = acc_map.get(bitmap_ext_pda)
        if bitmap_ext_raw is not None:
            bitmap_ext = parse_anchor_account(
                bitmap_ext_raw,
                BinArrayBitmapExtensionLayout,
                BIN_ARRAY_BITMAP_EXTENSION_DISCRIMINATOR)
        else:
            bitmap_ext = None

        client = DLMMClient(
            pool,
            rpc,
        )

        # inject already-fetched data to avoid refetch
        client.lb_pair = lb_pair
        client.bitmap_ext = bitmap_ext

        await client.fetch_token_metadata()

        return DLMM(
            pool=pool,
            lb_pair=lb_pair,
            bitmap_ext=bitmap_ext,
            token_x=client.token_x,
            token_y=client.token_y,
            rewards=client.rewards,
            rpc=rpc
        )

    async def get_active_bin(self) -> ActiveBin:
        bins = await self.get_bins(
            lb_pair_pubkey=self.pool,
            lower_bin_id=self.lb_pair.active_id,
            upper_bin_id=self.lb_pair.active_id,
            base_token_decimals=self.token_x.mint["decimals"],
            quote_token_decimals=self.token_y.mint["decimals"],
            rpc=self.rpc,
            program_id=DLMM_PROGRAM_ID,
        )

        if not bins:
            raise RuntimeError("Active bin not found")

        return bins[0]

    async def get_bins(
            self,
            *,
            lb_pair_pubkey: Pubkey,
            lower_bin_id: int,
            upper_bin_id: int,
            base_token_decimals: int,
            quote_token_decimals: int,
            rpc,
            program_id: Pubkey,
            lower_bin_array: Optional[BinArrayLayout] = None,
            upper_bin_array: Optional[BinArrayLayout] = None,
    ) -> list[ActiveBin]:

        # --- bin array indexes ---
        lower_idx = bin_id_to_bin_array_index(lower_bin_id)
        upper_idx = bin_id_to_bin_array_index(upper_bin_id)

        has_cached_lower = lower_bin_array is not None
        has_cached_upper = upper_bin_array is not None
        is_single_array = lower_idx == upper_idx

        lower_offset = 1 if has_cached_lower else 0
        upper_offset = -1 if has_cached_upper else 0

        # --- bitmap filtering ---
        bitmap = self.lb_pair.bin_array_bitmap
        bitmap_ext = self.bitmap_ext

        bin_array_indices: list[int] = []
        for i in range(lower_idx + lower_offset, upper_idx + upper_offset + 1):
            if is_bin_array_initialized(i, bitmap, bitmap_ext):
                bin_array_indices.append(i)

        # --- derive bin array PDAs ---
        pubkeys = [
            derive_bin_array(lb_pair_pubkey, i, program_id)
            for i in bin_array_indices
        ]

        # --- fetch bin arrays ---
        fetched_arrays = []
        if pubkeys:
            accounts = await get_multiple_account_datas(pubkeys, rpc)
            fetched_arrays = [
                parse_anchor_account(
                    raw,
                    BinArrayLayout,
                    BIN_ARRAY_DISCRIMINATOR
                )
                for _, raw in accounts
            ]

        # --- combine cached + fetched ---
        bin_arrays = []

        if has_cached_lower:
            bin_arrays.append(lower_bin_array)

        bin_arrays.extend(fetched_arrays)

        if has_cached_upper and not is_single_array:
            bin_arrays.append(upper_bin_array)

        # --- build binsById ---
        bins_by_id: dict[int, Bin] = {}

        for bin_array in bin_arrays:
            if bin_array is None:
                continue

            lower_id, _ = get_bin_array_lower_upper_bin_id(bin_array.index)

            for i, bin_obj in enumerate(bin_array.bins):
                bins_by_id[lower_id + i] = bin_obj

        # --- version ---
        version = next(
            (ba.version for ba in bin_arrays if ba is not None),
            1,
        )

        # --- enumerate bins ---
        return list(
            enumerate_bins(
                bins_by_id=bins_by_id,
                lower_bin_id=lower_bin_id,
                upper_bin_id=upper_bin_id,
                bin_step_bps=self.lb_pair.bin_step,
                base_token_decimals=base_token_decimals,
                quote_token_decimals=quote_token_decimals,
                version=version,
            )
        )

    async def get_position(
            self,
            position_pubkey: Pubkey,
    ) -> PositionAccount:
        # -------------------------------------------------
        # Phase A: fetch & decode position
        # -------------------------------------------------
        raw = await get_account_data(position_pubkey, self.rpc)
        if raw is None:
            raise RuntimeError(f"Position {position_pubkey} not found")

        position = wrap_position(
            position_pubkey=position_pubkey,
            raw_data=raw,
        )

        # -------------------------------------------------
        # Phase B: derive bin array pubkeys
        # -------------------------------------------------
        bin_array_pubkeys = get_bin_array_pubkeys_coverage(
            lb_pair=self.pool,
            lower_bin_id=position.lower_bin_id,
            upper_bin_id=position.upper_bin_id,
            program_id=DLMM_PROGRAM_ID,
        )

        # -------------------------------------------------
        # Phase C: fetch clock + bin arrays
        # -------------------------------------------------
        accounts = await get_multiple_account_datas(
            [SYSVAR_CLOCK_PUBKEY, *bin_array_pubkeys],
            self.rpc,
        )

        # --- clock ---
        _, clock_raw = accounts[0]
        if clock_raw is None:
            raise RuntimeError("Clock sysvar not found")

        clock = Clock.from_bytes(clock_raw)

        # --- bin arrays ---
        bin_array_map = {}

        for (pk, raw), _ in zip(accounts[1:], bin_array_pubkeys):
            if raw is None:
                continue

            bin_array = parse_anchor_account(
                raw,
                BinArrayLayout,
                BIN_ARRAY_DISCRIMINATOR
            )
            bin_array_map[str(pk)] = bin_array

        # -------------------------------------------------
        # Phase D: process position
        # -------------------------------------------------
        processed = process_position(
            lb_pair=self.lb_pair,
            clock=clock,
            position=position,
            base_mint=self.token_x.mint,
            quote_mint=self.token_y.mint,
            reward_mint_0=self.rewards[0].mint if self.rewards[0] else None,
            reward_mint_1=self.rewards[1].mint if self.rewards[1] else None,
            bin_array_map=bin_array_map
        )

        return PositionAccount(
            {
                "public_key":position_pubkey,
                "position_data" : processed,
                "version": position.version
            }
        )

    async def get_positions_by_user_and_lb_pair(
            self,
            user_pubkey: Pubkey | None = None,
    ):
        tasks: list[Any] = [self.get_active_bin()]
        if user_pubkey is not None:
            tasks.append(
                self.rpc.get_program_accounts(
                    DLMM_PROGRAM_ID,
                    encoding="base64",
                    filters=[
                        position_v2_filter(),
                        position_owner_filter(user_pubkey),
                        position_lb_pair_filter(self.pool),
                    ],
                )
            )

        active_bin, positions_resp = await asyncio.gather(*tasks)

        if active_bin is None:
            raise RuntimeError("Error fetching active bin")

        if user_pubkey is None:
            return {
                "activeBin": active_bin,
                "userPositions": [],
            }

        positions = []
        for acc in positions_resp.value:
            position = wrap_position(
                position_pubkey=acc.pubkey,
                raw_data=bytes(acc.account.data),
            )
            positions.append(position)

        if not positions:
            return {
                "activeBin": active_bin,
                "userPositions": [],
            }

        bin_array_pubkeys: set[Any] = set()

        for position in positions:
            keys = position.get_bin_array_pubkeys_coverage(DLMM_PROGRAM_ID)
            for key in keys:
                bin_array_pubkeys.add(str(key))

        bin_array_pubkeys = {Pubkey.from_string(k) for k in bin_array_pubkeys}

        accounts = await get_multiple_account_datas(
            [
                self.pool,
                SYSVAR_CLOCK_PUBKEY,
                *bin_array_pubkeys,
            ],
            self.rpc,
        )

        lb_pair_raw = accounts[0][1]
        clock_raw = accounts[1][1]

        if lb_pair_raw is None:
            raise RuntimeError("LB Pair account not found")

        if clock_raw is None:
            raise RuntimeError("Clock account not found")

        clock = ClockLayout.parse(clock_raw)

        # -------------------------------------------------
        # Phase E: decode bin arrays
        # -------------------------------------------------
        bin_array_map: dict[str, BinArrayLayout] = {}

        for (pk, raw) in accounts[2:]:
            if raw is None:
                continue

            bin_array = parse_anchor_account(
                raw, BinArrayLayout, BIN_ARRAY_DISCRIMINATOR
            )
            bin_array_map[str(pk)] = bin_array

        # -------------------------------------------------
        # Phase F: process positions
        # -------------------------------------------------
        user_positions = []

        for position in positions:
            processed = process_position(
                lb_pair=self.lb_pair,
                clock=clock,
                position=position,
                base_mint=self.token_x.mint,
                quote_mint=self.token_y.mint,
                reward_mint_0=self.rewards[0].mint if self.rewards and self.rewards[0] else None,
                reward_mint_1=self.rewards[1].mint if self.rewards and self.rewards[1] else None,
                bin_array_map=bin_array_map,
            )

            user_positions.append(
                Position({
                    "public_key": position.public_key,
                    "position_data": processed,
                    "version": position.version,
                })
            )

        return {
            "activeBin": active_bin,
            "userPositions": user_positions,
        }
