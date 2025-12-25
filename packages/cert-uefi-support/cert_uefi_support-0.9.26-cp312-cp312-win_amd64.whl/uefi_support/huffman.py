#!/bin/env python3
import os
import struct
import zlib
from typing import Optional, Iterator, Any

class Error(Exception):
    pass

def cwDec(w: int) -> str:  # Convert 16-bit value to string codeword
    return bin(0x10000 | w).rstrip('0')[3:-1]

def cwEnc(cw: str) -> int:  # Convert string codeword to 16-bit value
    return int((cw + '1').ljust(16, '0'), 2)

#***************************************************************************
#***************************************************************************
#***************************************************************************

def HuffTabReader_bin(ab: bytes) -> Iterator[tuple[str, int, bytes]]:
    fmtRec = struct.Struct("<HB")
    o = 0
    while o < len(ab):
        w, cb = fmtRec.unpack_from(ab, o)
        o += fmtRec.size
        v = ab[o:o + cb]
        assert len(v) == cb
        o += cb
        yield (cwDec(w), cb, v)

#***************************************************************************
#***************************************************************************
#***************************************************************************

class HuffNode(object):
    def __init__(self, cw: str, hd: Optional['HuffDecoder']):
        self.cw = cw  # String codeword value
        self.w = cwEnc(cw)  # Encoded codeword value
        if hd:
            self.nBits: Optional[int] = len(cw)  # Length of codeword in bits
            self.cb = hd.dLen.get(cw, None)
            self.av: list[Any] = [d.get(cw, None) for d in hd.adTab]
        else:
            self.nBits = None  # Actual length of codeword is unknown

#***************************************************************************
#***************************************************************************
#***************************************************************************

class HuffDecoder(object):
    NAMES = ("Code", "Data")
    DUMP_KNOWN = 0
    DUMP_LEN = 1
    DUMP_ALL = 2
    fmtInt = struct.Struct("<L")
    baseDir = os.path.split(__file__)[0]
    BLOCK_SIZE = 0x1000  # 4K bytes

    def __init__(self) -> None:
        with open(os.path.join(self.baseDir, "huff11.bin"), "rb") as fi:
            self.unpackTables(zlib.decompress(fi.read(), -15))  # Load from compressed version
        self.prepareMap()

    def loadTable(self, items: Iterator[tuple[str, int, bytes]]) -> None:
        sv = set()  # Set for values
        d = {}
        for cw, cb, v in items:
            if cw in d:
                raise Error("Codeword %s already defined" % cw)

            if cb is None:
                continue
            cbKnown = self.dLen.get(cw, None)
            if cbKnown is None:
                self.dLen[cw] = cb
            elif cb != cbKnown:
                raise Error("Codeword %s sequence length %d != know %d" % (cw, cb, cbKnown))

            if v is None:
                continue
            assert len(v) == cb
            d[cw] = v  # Remember value
            sv.add(v)

        self.adTab.append(d)

    def unpackTables(self, ab: bytes) -> None:
        n, = self.fmtInt.unpack_from(ab)
        o = self.fmtInt.size
        self.dLen: dict[str, int] = {}
        self.adTab: list[dict[str, bytes]] = []
        for i in range(n):
            cb, = self.fmtInt.unpack_from(ab, o)
            o += self.fmtInt.size
            data = ab[o:o + cb]
            assert len(data) == cb
            o += cb
            self.loadTable(HuffTabReader_bin(data))

    def propagateMap(self, node: HuffNode) -> None:
        cw = node.cw
        for idx in range(int(cw[::-1], 2), len(self.aMap), 1 << len(cw)):
            assert self.aMap[idx] is None
            self.aMap[idx] = node

    def prepareMap(self) -> None:
        aCW = sorted(self.dLen.keys())[::-1]
        minBits, maxBits = len(aCW[0]), len(aCW[-1])
        self.aMap: list[Optional[Any]] = [None] * (1 << maxBits)  # 2**maxBits map
        aCW.append('0' * (maxBits + 1))  # Longer than max
        nBits = minBits  # Current length
        e = int(aCW[0], 2) | 1  # End value for current length
        for o in range(1, len(aCW)):
            nextBits = len(aCW[o])
            if nextBits == nBits:
                continue  # Run until length change
            assert nextBits > nBits  # Length must increase
            s = int(aCW[o - 1], 2)  # Start value for current length
            for i in range(s, e + 1):
                cw = bin(i)[2:].zfill(nBits)
                self.propagateMap(HuffNode(cw, self))
            e = int(aCW[o], 2) | 1  # End value for next length
            for i in range(int(e / 2) + 1, s):  # Handle values with unknown codeword length
                cw = bin(i)[2:].zfill(nBits)
                self.propagateMap(HuffNode(cw, None))
            nBits = nextBits
        for v in self.aMap:
            assert v is not None

    def enumCW(self, ab: bytes) -> Iterator[HuffNode]:
        v = int(bin(int("01" + ab.hex(), 16))[3:][::-1], 2)  # Reversed bits
        cb = 0
        while cb < self.BLOCK_SIZE:  # Block length
            node = self.aMap[v & 0x7FFF]
            assert node is not None
            if node.nBits is None:
                raise Error("Unknown codeword %s* length" % node.cw)
            yield node
            v >>= node.nBits
            if node.cb is not None:
                cb += node.cb

    def decompressChunk(self, ab: bytes, iTab: int) -> bytes:
        r = []
        cb = 0
        for node in self.enumCW(ab):
            v = node.av[iTab]
            if v is None:
                raise Error("Unknown sequence for codeword %s in table #%d" % (node.cw, iTab))
            r.append(v)
            cb += len(v)
            if cb >= self.BLOCK_SIZE:
                break
        return b''.join(r)

    def decompress(self, ab: bytes, length: int) -> bytes:
        nChunks, left = divmod(length, self.BLOCK_SIZE)
        assert 0 == left
        aOfs = list(struct.unpack_from("<%dL" % nChunks, ab))
        aOpt = [0] * nChunks
        for i in range(nChunks):
            aOpt[i], aOfs[i] = divmod(aOfs[i], 0x40000000)

        base = nChunks * 4
        aOfs.append(len(ab) - base)
        r = []
        for i, opt in enumerate(aOpt):
            iTab, bCompr = divmod(opt, 2)
            assert 1 == bCompr
            unpacked = self.decompressChunk(
                ab[base + aOfs[i]: base + aOfs[i + 1]], iTab)
            assert len(unpacked) == self.BLOCK_SIZE
            r.append(unpacked)
        return b''.join(r)

#---------------------------------------------------------------------------------------
# Experimental code.

# Lines 130-153 in me_cleaner.py
def get_chunks_offsets(chunk_count: int, data_start: int, data_size: int,
                       lut_data: bytes) -> list[list[int]]:
    #chunk_count = unpack("<I", llut[0x04:0x08])[0]
    #huffman_stream_end = sum(unpack("<II", llut[0x10:0x18]))
    huffman_stream_end = data_start + data_size
    nonzero_offsets = [huffman_stream_end]
    offsets = []

    for i in range(0, chunk_count):
        #chunk = llut[0x40 + i * 4:0x44 + i * 4]
        chunk = lut_data[(i * 4):(i + 1) * 4]
        offset = 0

        if chunk[3] != 0x80:
            offset = struct.unpack("<I", chunk[0:3] + b"\x00")[0]

        offsets.append([offset, 0])
        if offset != 0:
            nonzero_offsets.append(offset)

    nonzero_offsets.sort()

    for j in offsets:
        if j[0] != 0:
            j[1] = nonzero_offsets[nonzero_offsets.index(j[0]) + 1]

    return offsets

# Local Variables:
# mode: python
# fill-column: 90
# End:
