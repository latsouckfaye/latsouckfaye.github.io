"""Minimal pure-Python reader for the site's multi-band LZW-compressed GeoTIFF.

No GIS dependency (rasterio/GDAL/tifffile) is available in this environment,
so this module implements just enough of the TIFF 6.0 spec — IFD parsing and
TIFF-flavor LZW decompression (early-change, MSB-first) — to recover the raw
float32 bands. Validated against the file's own embedded GDAL statistics.
"""
import struct
import numpy as np

_TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8}
NODATA = -3.4e38


def _read_ifd(data, offset, endian):
    n = struct.unpack(endian + "H", data[offset:offset + 2])[0]
    entries = {}
    p = offset + 2
    for _ in range(n):
        tag, typ, count = struct.unpack(endian + "HHI", data[p:p + 8])
        valoff = data[p + 8:p + 12]
        tsize = _TYPE_SIZE.get(typ, 1)
        total = tsize * count
        raw = valoff[:total] if total <= 4 else data[struct.unpack(endian + "I", valoff)[0]:][:total]
        if typ == 3:
            vals = struct.unpack(endian + "H" * count, raw[:2 * count])
        elif typ == 4:
            vals = struct.unpack(endian + "I" * count, raw[:4 * count])
        else:
            vals = raw
        entries[tag] = vals
        p += 12
    return entries


def _lzw_decode(buf, expected_len):
    """TIFF-flavor LZW (early change), MSB-first bit packing."""
    CLEAR, EOI = 256, 257
    out = bytearray()
    bitbuf = bitcnt = pos = 0
    codesize = 9

    def reset_table():
        return [bytes([i]) for i in range(256)] + [b"", b""]

    table = reset_table()
    prev = None
    while len(out) < expected_len:
        while bitcnt < codesize:
            if pos >= len(buf):
                return bytes(out[:expected_len])
            bitbuf = (bitbuf << 8) | buf[pos]
            pos += 1
            bitcnt += 8
        bitcnt -= codesize
        code = (bitbuf >> bitcnt) & ((1 << codesize) - 1)

        if code == EOI:
            break
        if code == CLEAR:
            table = reset_table()
            codesize = 9
            prev = None
            continue
        if code < len(table):
            entry = table[code]
        elif code == len(table) and prev is not None:
            entry = prev + prev[:1]
        else:
            raise ValueError(f"bad LZW code {code} (table size {len(table)})")
        out += entry
        if prev is not None:
            table.append(prev + entry[:1])
        prev = entry
        tlen = len(table)
        if tlen == 511:
            codesize = 10
        elif tlen == 1023:
            codesize = 11
        elif tlen == 2047:
            codesize = 12
    return bytes(out[:expected_len])


def read_tiff_bands(path):
    """Return a list of (H, W) float32 numpy arrays, one per band, NaN where nodata."""
    with open(path, "rb") as f:
        data = f.read()

    endian = "<" if data[0:2] == b"II" else ">"
    ifd_offset = struct.unpack(endian + "I", data[4:8])[0]
    e = _read_ifd(data, ifd_offset, endian)

    W, H = e[256][0], e[257][0]
    spp = e[277][0]
    rows_per_strip = e[278][0]
    strip_offsets, strip_byte_counts = e[273], e[279]
    n_strips_per_band = -(-H // rows_per_strip)

    bands = []
    strip_i = 0
    for _ in range(spp):
        band = np.zeros((H, W), dtype=np.float32)
        row = 0
        for _ in range(n_strips_per_band):
            off, bc = strip_offsets[strip_i], strip_byte_counts[strip_i]
            this_rows = min(rows_per_strip, H - row)
            decoded = _lzw_decode(data[off:off + bc], this_rows * W * 4)
            band[row:row + this_rows, :] = np.frombuffer(decoded, dtype=endian + "f4").reshape(this_rows, W)
            row += this_rows
            strip_i += 1
        band[band <= NODATA] = np.nan
        bands.append(band)
    return bands
