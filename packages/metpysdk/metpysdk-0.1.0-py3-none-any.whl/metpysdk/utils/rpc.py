import base64

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey


async def get_account_data(pubkey: Pubkey, rpc: AsyncClient) -> bytes:
    resp = await rpc.get_account_info(pubkey, encoding="base64")

    if resp.value is None:
        raise ValueError(f"Account {pubkey} not found")

    data = resp.value.data

    # Case 1: already raw bytes (solders / base64+zstd)
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)

    # Case 2: [base64_string, encoding]
    if isinstance(data, list):
        return base64.b64decode(data[0])

    raise TypeError(f"Unsupported account data type: {type(data)}")


async def get_multiple_account_datas(
    pubkeys,
    rpc: AsyncClient,
) -> list[tuple[Pubkey, bytes]]:
    """
    Fetch multiple accounts by pubkey.
    Returns list of (pubkey, raw_bytes) for existing accounts.
    """
    valid_pubkeys = []
    for pubkey in pubkeys:
        if isinstance(pubkey, Pubkey):
            valid_pubkeys.append(pubkey)
            continue
        if isinstance(pubkey, bytes):
            valid_pubkeys.append(Pubkey.from_bytes(pubkey))
            continue
        if isinstance(pubkey, str):
            valid_pubkeys.append(Pubkey.from_string(pubkey))
            continue
        raise TypeError(f"Unsupported pubkey type: {type(pubkey)}")

    # valid_pubkeys = [
    #     pubkey for pubkey in pubkeys if isinstance(pubkey, Pubkey)
    # ]
    if not valid_pubkeys:
        return []

    resp = await rpc.get_multiple_accounts(valid_pubkeys)

    result = []
    for pk, acc in zip(pubkeys, resp.value):
        if acc is None:
            result.append((pk, acc))
            continue
        result.append((pk, bytes(acc.data)))

    return result

async def get_program_accounts_with_filters(pubkey: Pubkey, filters, rpc: AsyncClient):
    resp = await rpc.get_program_accounts(pubkey, filters=filters)
    return resp.value[0]

