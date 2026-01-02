from solders.pubkey import Pubkey

# ==============================
# Program
# ==============================

DLMM_PROGRAM_ID = Pubkey.from_string(
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
)

SYSVAR_CLOCK_PUBKEY = Pubkey.from_string(
    "SysvarC1ock11111111111111111111111111111111"
)

# ==============================
# Bin / BinArray constants
# ==============================

# Number of bins inside ONE BinArray
MAX_BIN_PER_ARRAY = 70  # IDL: MAX_BIN_PER_ARRAY

# Bitmap size PER SIDE (positive / negative)
BIN_ARRAY_BITMAP_SIZE = 512  # IDL: BIN_ARRAY_BITMAP_SIZE

# Total bitmap bits (positive + negative)
TOTAL_BITMAP_BITS = BIN_ARRAY_BITMAP_SIZE * 2  # 1024

# Bitmap storage layout
BITS_PER_U64 = 64
BITMAP_U64_WORDS = TOTAL_BITMAP_BITS // BITS_PER_U64  # 16

# Extension bitmap
EXTENSION_BINARRAY_BITMAP_SIZE = 12  # IDL: EXTENSION_BINARRAY_BITMAP_SIZE

# ==============================
# Seeds (from IDL)
# ==============================

BIN_ARRAY_SEED = b"bin_array"
BIN_ARRAY_BITMAP_SEED = b"bitmap"
POSITION_SEED = b"position"
ORACLE_SEED = b"oracle"

# ==============================
# Fee / precision constants
# ==============================

BASIS_POINT_MAX = 10_000
FEE_PRECISION = 1_000_000_000  # 1e9

# ==============================
# Limits (useful later)
# ==============================

MAX_BIN_ID = 443_636
MIN_BIN_ID = -443_636

MAX_BIN_STEP = 400

MINIMUM_LIQUIDITY = 1_000_000

NUM_REWARDS = 2

SCALE_OFFSET = 64

# ==============================
# Urls
# ==============================

SOLANA_MAINNET = "https://api.mainnet-beta.solana.com"