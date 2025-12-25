#!/bin/env python3

import functools
import sys
import os
import io
from enum import Enum
from dataclasses import dataclass
from types import TracebackType
from collections.abc import Callable
from typing import Optional, Union, Iterator, Any, Type, TypeVar, ParamSpec

from .EfiCompressor import (
    UefiDecompress as _uefiDecompress,
    FrameworkDecompress as _frameworkDecompress, EfiException)
from .LzmaCompressor import LzmaDecompress as _lzmaDecompress, LzmaException
from .HuffmanCompressor import HuffmanDecompress as _huffmanDecompress, HuffmanException
from .huffman import HuffDecoder, Error as HuffError
from .Cab import Decompressor as CabDecompressor
try:
    from ._version import version as __version__ # type: ignore
except Exception:
    __version__ = "0.0.0"


__all__ = ['UefiDecompress', 'FrameworkDecompress', 'LzmaDecompress',
           'HuffmanDecompress', 'HuffmanFlags',
           'Huffman11Decompress',
           'Error', 'CompressionError', 'DecompressionError']

class Error(Exception):
    pass

class CompressionError(Error):
    pass

class DecompressionError(Error):
    pass

class WrappedDecompressionError(DecompressionError):

    def __init__(self, original: Exception, algo: str, size: Any = None,
                 traceback: Optional[TracebackType] = None) -> None:
        self.algo = algo
        self.size = size
        Error.__init__(self, *original.args)
        if traceback is not None:
            self.with_traceback(traceback)

    def __str__(self) -> str:
        sizestr = f"[{self.size!s}]" if self.size is not None else ""
        if len(self.args) == 1:
            argstr = f"{self.args[0]!s}"
        elif len(self.args) > 1:
            argstr = f"{self.args!s}"
        else:
            argstr = "None"
        return f"DecompressionError ({self.algo}{sizestr}): {argstr}"

class HuffmanFlags(Enum):
    Uncompressed = 0x0
    Code = 0x20
    Empty = 0x40
    Data = 0x60
    Invalid = 0xff

def normal_length(args: list[Any], kwds: Any) -> int:
    return len(args[0])

RetVal = TypeVar('RetVal')  # Return type of the decorated function
Params = ParamSpec('Params')  # Parameters of the decorated function
def wrap_errors(
        err_from: Type[Exception], algo: str,
        length: Callable[[Any, Any], Any] = normal_length
) -> Callable[[Callable[Params, RetVal]], Callable[Params, RetVal]]:
    def decorator_wrapper(func: Callable[Params, RetVal]) -> Callable[Params, RetVal]:
        @functools.wraps(func)
        def wrapper(*args: Params.args, **kwds: Params.kwargs) -> RetVal:
            try:
                return func(*args, **kwds)
            except err_from as e:
                raise WrappedDecompressionError(e, algo, length(args, kwds), sys.exc_info()[2])
        return wrapper
    return decorator_wrapper

@wrap_errors(LzmaException, "LZMA")
def LzmaDecompress(x: bytes) -> bytes:
    """Return the decompressed result of the argument buffer"""
    result = _lzmaDecompress(x)[0]
    assert isinstance(result, bytes)
    return result

UefiDecompress = wrap_errors(EfiException, "UEFI")(_uefiDecompress)
FrameworkDecompress = wrap_errors(EfiException, "Framework")(_frameworkDecompress)

@wrap_errors(HuffmanException, "Huffman",
             (lambda args, kwds: (len(args[0]), args[1], args[3])))
def HuffmanDecompress(data: bytes, offset: int, flags: HuffmanFlags,
                      length: int, version: int) -> bytes:
    """Huffman decode data from DATA starting at OFFSET, where LENGTH is
the expected size of the output, FLAGS is a HuffmanFlags object, and
version is between 6 and 10 inclusive."""

    if version < 6 or version > 10:
        raise DecompressionError("Invalid version (must be from 6 to 10 inclusive)")
    if not isinstance(flags, HuffmanFlags):
        raise DecompressionError("Flags must be a HuffmanFlags enumeration object")
    if flags != HuffmanFlags.Code and flags != HuffmanFlags.Data:
        raise DecompressionError("Invalid Huffman flags")
    return _huffmanDecompress(data, offset, flags.value, length, version)

def huff11len(args: list[Any], kwds: Any) -> int:
    return args[1] if args[1] is not None else len(args[0])

decoder = HuffDecoder()

@wrap_errors(HuffError, "Huffman11", huff11len)
def Huffman11Decompress(data: bytes, length: Optional[int] = None) -> bytes:
    """Decompress Intel ME 11 compressed data"""
    if length is None:
        length = len(data)
    result = decoder.decompress(data, length)
    assert isinstance(result, bytes)
    return result

@dataclass
class CabInfo:
    """Class representing meta information of a CAB file."""
    filename: str
    file_size: int
    attributes: int
    date_time: tuple[int, int, int, int, int, int]
    #compressed_size: Optional[int]

class CabFile:
    def __init__(self, file: Union[str, os.PathLike[Any], io.IOBase]):
        if isinstance(file, os.PathLike):
            file = os.fspath(file)
        if isinstance(file, (str, bytes)):
            self.fp: io.IOBase = io.open(file, "rb")
        else:
            assert isinstance(file, io.IOBase)
            self.fp = file
        self.decompr = CabDecompressor()
        self.cab = self.decompr.open(self.fp)

    def infolist_gen(self) -> Iterator[CabInfo]:
        x = self.cab.first_file()
        while x is not None:
            yield CabInfo(*x.info)
            x = x.next()

    def infolist(self) -> list[CabInfo]:
        return list(self.infolist_gen())

    def open(self, filename: Union[str, CabInfo]) -> Optional[io.BytesIO]:  # noqa [A003]
        if isinstance(filename, CabInfo):
            filename = CabInfo.filename
        x = self.cab.first_file()
        while x is not None:
            if x.info[0] == filename:
                data = io.BytesIO()
                x.data(data)
                data.seek(0, 0)
                return data
            x = x.next()
        return None
