
def UefiDecompress(data: bytes) -> bytes: ...

def FrameworkDecompress(data: bytes) -> bytes: ...

class EfiException(Exception):
    pass
