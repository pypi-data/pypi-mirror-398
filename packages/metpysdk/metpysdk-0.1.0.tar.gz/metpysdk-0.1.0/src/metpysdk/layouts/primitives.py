from construct import (
    Adapter,
    Array,
    Bytes,
    Int8ul,
    Int16ul,
    Int32sl,
    Int32ul,
    Int64sl,
    Int64ul,
    Struct,
)

# Aliases to keep your code unchanged
CStruct = Struct

U8 = Int8ul
U16 = Int16ul
U32 = Int32ul
U64 = Int64ul

I32 = Int32sl
I64 = Int64sl

PubkeyLayout = Bytes(32)

BitmapChunk = Array(8, U64)
BitmapSide = Array(12, BitmapChunk)

class U128Adapter(Adapter):
    def _decode(self, obj, context, path):
        return int.from_bytes(obj, "little", signed=False)

    def _encode(self, obj, context, path):
        return obj.to_bytes(16, "little", signed=False)

U128 = U128Adapter(Bytes(16))
