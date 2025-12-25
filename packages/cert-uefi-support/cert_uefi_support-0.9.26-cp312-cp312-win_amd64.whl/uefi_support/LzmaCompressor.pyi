
def LzmaDecompress(data: bytes) -> tuple[bytes, bytes]: ...

class LzmaException(Exception):
    pass
