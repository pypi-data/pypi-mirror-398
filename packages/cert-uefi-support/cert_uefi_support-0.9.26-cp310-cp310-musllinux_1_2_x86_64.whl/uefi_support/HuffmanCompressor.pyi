
def HuffmanDecompress(data: bytes, offset: int, flags: int,
                      length: int, version: int) -> bytes: ...

class HuffmanException(Exception):
    pass
