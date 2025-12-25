import orjson

try:
    from compression import zstd as _native_zstd

    def compress(data: bytes) -> bytes:
        return _native_zstd.compress(data, level=3)

    def decompress(data: bytes) -> bytes:
        return _native_zstd.decompress(data)

except ImportError:
    # Python < 3.14 Fallback
    import zstandard as _pypi_zstd

    # Create singletons to avoid overhead on every call
    _compressor = _pypi_zstd.ZstdCompressor(level=3)
    _decompressor = _pypi_zstd.ZstdDecompressor()

    def compress(data: bytes) -> bytes:
        return _compressor.compress(data)

    def decompress(data: bytes) -> bytes:
        return _decompressor.decompress(data)


def serialize(data: dict) -> bytes:
    """Serializes a dict to bytes using orjson."""
    payload = orjson.dumps(data)
    if len(payload) > 1024:
        payload = b"zstd:" + compress(payload)
    return payload


def deserialize(payload: bytes) -> dict:
    """Deserializes bytes to a dict using orjson."""
    if payload.startswith(b"zstd:"):
        payload = decompress(payload[5:])
    data = orjson.loads(payload)
    return data
